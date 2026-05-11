"""LLM client.

Two families of clients are supported:

1. Remote API clients (Groq, OpenAI, HuggingFace router, OpenRouter) -- they
   share an OpenAI-compatible REST API, so the same OpenAICompatibleClient
   base works for all four. Differences are just base_url + API key env var.

2. Local client (LocalTransformersClient) -- loads a HuggingFace model
   directly with `transformers` and runs inference on the local GPU. Designed
   for free-tier GPU environments (Kaggle Notebooks 30h/week T4, Colab,
   ZeroGPU Spaces, or any local CUDA box). Loads the model once and reuses
   it across all calls so the cold-start cost amortises over the full sweep.

Tokens-per-day (TPD) handling for remote clients: when the provider returns
a 429 with "tokens per day" in the message, we DO NOT retry -- that's a
24h rolling limit and retrying just spends more tokens. Instead we raise
TokenBudgetExceeded so the runner can stop cleanly.
"""
from __future__ import annotations

import os
import time
from abc import ABC, abstractmethod

from openai import OpenAI, RateLimitError, APIError, APIConnectionError
from dotenv import load_dotenv

from config import ModelConfig

load_dotenv()


class TokenBudgetExceeded(RuntimeError):
    """Daily token quota gone. Distinct from RateLimitError because TPM
    errors retry; TPD errors abort the session.
    """


def _is_tpd_error(message: str) -> bool:
    low = message.lower()
    return (
        "tokens per day" in low
        or "(tpd)" in low
        or "tpd:" in low
        or "per day" in low
    )


class LLMClient(ABC):
    @abstractmethod
    def generate(self, system: str, user: str) -> str:
        ...


class OpenAICompatibleClient(LLMClient):
    """Base class for any provider exposing the OpenAI Chat Completions API."""

    BASE_URL: str | None = None
    API_KEY_ENV_VAR: str = "OPENAI_API_KEY"
    SETUP_HINT: str = "set OPENAI_API_KEY in your .env file"

    def __init__(self, cfg: ModelConfig):
        self.cfg = cfg
        api_key = os.environ.get(self.API_KEY_ENV_VAR)
        if not api_key:
            raise RuntimeError(
                f"{self.API_KEY_ENV_VAR} not set. {self.SETUP_HINT}"
            )
        self.client = OpenAI(api_key=api_key, base_url=self.BASE_URL)
        self.session_tokens: int = 0
        self.session_calls: int = 0

    def generate(self, system: str, user: str) -> str:
        last_err: Exception | None = None
        for attempt in range(self.cfg.max_retries + 1):
            try:
                resp = self.client.chat.completions.create(
                    model=self.cfg.model_id,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    temperature=self.cfg.temperature,
                    max_completion_tokens=self.cfg.max_tokens,
                )
                if resp.usage is not None:
                    self.session_tokens += int(getattr(resp.usage, "total_tokens", 0) or 0)
                self.session_calls += 1
                if self.cfg.request_delay_s > 0:
                    time.sleep(self.cfg.request_delay_s)
                return resp.choices[0].message.content or ""

            except RateLimitError as e:
                msg = str(e)
                if _is_tpd_error(msg):
                    raise TokenBudgetExceeded(
                        f"Daily token quota (TPD) exhausted on "
                        f"{self.cfg.provider}:{self.cfg.model_id}. "
                        f"This session burned {self.session_tokens:,} "
                        f"tokens across {self.session_calls} successful "
                        f"calls before the wall.\n"
                        f"  Provider message: {msg}"
                    ) from e
                wait = 4 * (2 ** attempt)
                last_err = e
                print(
                    f"    [rate limit] backing off {wait}s "
                    f"(attempt {attempt + 1}/{self.cfg.max_retries + 1})"
                )
                time.sleep(wait)

            except (APIConnectionError, APIError) as e:
                wait = 2 * (2 ** attempt)
                last_err = e
                print(
                    f"    [api error] {type(e).__name__}: backing off {wait}s "
                    f"(attempt {attempt + 1}/{self.cfg.max_retries + 1})"
                )
                time.sleep(wait)

        raise RuntimeError(
            f"All {self.cfg.max_retries + 1} attempts failed. Last error: {last_err}"
        )


class GroqClient(OpenAICompatibleClient):
    BASE_URL = "https://api.groq.com/openai/v1"
    API_KEY_ENV_VAR = "GROQ_API_KEY"
    SETUP_HINT = "Sign up at https://console.groq.com and put your key in .env"


class OpenAIClient(OpenAICompatibleClient):
    BASE_URL = None
    API_KEY_ENV_VAR = "OPENAI_API_KEY"
    SETUP_HINT = "Add credits at platform.openai.com/billing and put your key in .env"


class HuggingFaceClient(OpenAICompatibleClient):
    """HF Inference Providers router (paid per-token; $2/mo free for Pro)."""
    BASE_URL = "https://router.huggingface.co/v1"
    API_KEY_ENV_VAR = "HUGGINGFACE_API_KEY"
    SETUP_HINT = (
        "Create an HF API key at https://huggingface.co/settings/tokens "
        "and add HUGGINGFACE_API_KEY=hf_... to your .env file."
    )


class OpenRouterClient(OpenAICompatibleClient):
    BASE_URL = "https://openrouter.ai/api/v1"
    API_KEY_ENV_VAR = "OPENROUTER_API_KEY"
    SETUP_HINT = (
        "Create an API key at https://openrouter.ai/keys "
        "and add OPENROUTER_API_KEY=sk-or-v1-... to your .env file."
    )


class LocalTransformersClient(LLMClient):
    """Run a HuggingFace model locally via transformers (Kaggle / Colab / GPU box).

    Loads the model once into VRAM with 4-bit quantization (bitsandbytes) so
    8-9B models fit on a 16GB T4 (Kaggle's free tier). Subsequent calls reuse
    the in-memory model -- crucial because loading a 7B model takes 1-3 min.

    Requirements:
        pip install transformers accelerate bitsandbytes
    For gated models (Llama, Gemma) set HUGGINGFACE_API_KEY in env first and
    request access on the model's HF page.
    """

    def __init__(self, cfg: ModelConfig):
        self.cfg = cfg
        self.session_tokens: int = 0
        self.session_calls: int = 0

        # Lazy imports so machines without GPU stack can still use API providers.
        try:
            import torch
            from transformers import (
                AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig,
            )
        except ImportError as e:
            raise RuntimeError(
                "LocalTransformersClient requires transformers, accelerate, "
                "bitsandbytes, and torch. Install with:\n"
                "  pip install -r requirements_local.txt"
            ) from e

        self._torch = torch

        # Use HF token for gated models (Llama, Gemma).
        hf_token = os.environ.get("HUGGINGFACE_API_KEY") or os.environ.get("HF_TOKEN")

        print(f"[local] Loading {cfg.model_id} (1-3 min on first run; downloads cached after)...")

        self.tokenizer = AutoTokenizer.from_pretrained(
            cfg.model_id, token=hf_token, trust_remote_code=True,
        )
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        # 4-bit quantization keeps 8B models inside ~5GB VRAM. If GPU has
        # plenty of memory you can switch to bfloat16 by setting LOCAL_FP16=1.
        use_quant = os.environ.get("LOCAL_FP16") != "1" and torch.cuda.is_available()
        kwargs: dict = {
            "device_map": "auto",
            "token": hf_token,
            "trust_remote_code": True,
        }
        if use_quant:
            kwargs["quantization_config"] = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_use_double_quant=True,
            )
        else:
            kwargs["torch_dtype"] = torch.float16 if torch.cuda.is_available() else torch.float32

        self.model = AutoModelForCausalLM.from_pretrained(cfg.model_id, **kwargs)
        self.model.eval()

        device = next(self.model.parameters()).device
        n_params = sum(p.numel() for p in self.model.parameters()) / 1e9
        print(f"[local] Model loaded: {n_params:.1f}B params on {device}, "
              f"{'4-bit quantized' if use_quant else 'fp16'}")

    def generate(self, system: str, user: str) -> str:
        torch = self._torch
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
        # Qwen3 / DeepSeek-R1 / etc. tokenizers accept enable_thinking=False
        # to skip the <think> block entirely. This produces a direct JSON
        # answer instead of long chain-of-thought that often gets cut off
        # by max_tokens. Older / non-reasoning tokenizers reject the kwarg
        # with TypeError; we fall back gracefully in that case.
        try:
            prompt = self.tokenizer.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True,
                enable_thinking=False,
            )
        except TypeError:
            prompt = self.tokenizer.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True,
            )
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        prompt_tokens = inputs.input_ids.shape[1]

        with torch.no_grad():
            output = self.model.generate(
                **inputs,
                max_new_tokens=self.cfg.max_tokens,
                temperature=self.cfg.temperature,
                do_sample=self.cfg.temperature > 0,
                pad_token_id=self.tokenizer.eos_token_id,
            )

        # Strip the prompt prefix to get only the generated continuation.
        generated_ids = output[0][prompt_tokens:]
        text = self.tokenizer.decode(generated_ids, skip_special_tokens=True)

        completion_tokens = generated_ids.shape[0]
        self.session_tokens += prompt_tokens + completion_tokens
        self.session_calls += 1

        return text


def make_client(cfg: ModelConfig) -> LLMClient:
    if cfg.provider == "groq":
        return GroqClient(cfg)
    if cfg.provider == "openai":
        return OpenAIClient(cfg)
    if cfg.provider == "huggingface":
        return HuggingFaceClient(cfg)
    if cfg.provider == "openrouter":
        return OpenRouterClient(cfg)
    if cfg.provider == "local":
        return LocalTransformersClient(cfg)
    raise ValueError(f"Unsupported provider: {cfg.provider}")


def preflight_probe(client: LLMClient, model_id: str, provider: str) -> None:
    """One tiny call to verify the provider+model+key combination works."""
    try:
        out = client.generate(
            system="You are a test responder.",
            user="Reply with the single word OK and nothing else.",
        )
    except TokenBudgetExceeded:
        raise
    except Exception as e:
        msg = str(e)
        low = msg.lower()
        hint = ""
        if "no endpoints found" in low or "data policy" in low:
            hint = (
                "\n\n  Fix: this OpenRouter free model needs you to opt into "
                "the 'Free model publication' data policy at "
                "https://openrouter.ai/settings/privacy."
            )
        elif "rate limit" in low or "quota" in low or "429" in low:
            hint = (
                "\n\n  Fix: daily quota exhausted. Wait, switch to a smaller "
                "model, or use --quick (2 runs x 8 rounds)."
            )
        elif "api key" in low or "401" in low or "unauthorized" in low:
            hint = (
                "\n\n  Fix: API key missing or invalid. Check your .env file."
            )
        elif "gated" in low or "access" in low:
            hint = (
                "\n\n  Fix: the model is gated. Visit its HF page and accept "
                "the license / request access (Meta approval can take 24h)."
            )
        raise RuntimeError(
            f"Preflight probe failed for provider={provider} "
            f"model={model_id}:\n  {msg}{hint}"
        ) from e
    snippet = (out or "")[:30]
    print(f"[preflight] {provider}:{model_id} responded OK -> {snippet!r}")
