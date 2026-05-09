"""Configuration dataclasses for the benchmark.

Defaults aligned with the methodology of Sabani (2025) and Georgousis (2025):
  - n_rounds=16  (Georgousis section 5.5; finite horizon HIDDEN from agents)
  - memory_window=10  (Sabani section 4.1.4 sliding window)
  - n_runs=5  (Georgousis section 6.1)
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Literal


GameName = Literal["pd", "sh"]
ConditionName = Literal["no_comm", "cheap_talk"]
# "local" runs the model on the current machine via transformers (Kaggle / Colab
# / your own GPU). The other providers are remote API calls.
Provider = Literal["groq", "openai", "huggingface", "openrouter", "local"]
MessagePolicy = Literal["meaningful", "irrelevant", "silence"]


# Defaults are tuned for FREE TIERS so the pilot can run end-to-end without
# credits. For groq we use llama-3.1-8b-instant (5x more daily tokens than 70B).
# For local (Kaggle/Colab) we default to a model that is NOT gated (Qwen) so
# the user can verify the local path works before requesting Llama access.
DEFAULT_MODELS: dict[str, str] = {
    "groq": "llama-3.1-8b-instant",
    "openai": "gpt-4o-mini",
    "huggingface": "meta-llama/Llama-3.1-8B-Instruct",
    "openrouter": "google/gemma-2-9b-it:free",
    "local": "Qwen/Qwen2.5-7B-Instruct",
}


@dataclass
class ModelConfig:
    """Which model, with what sampling params. All 4 agents share this in v1."""
    provider: Provider = "groq"
    model_id: str = "llama-3.1-8b-instant"
    temperature: float = 0.7
    max_tokens: int = 320
    request_delay_s: float = 3.0
    max_retries: int = 4


@dataclass
class ExperimentConfig:
    """Top-level knobs for one full experiment (many runs of one condition)."""
    game: GameName = "pd"
    condition: ConditionName = "no_comm"
    n_agents: int = 4              # 1 hub + 3 leaves (Sabani section 5.2.3)
    n_rounds: int = 16             # Georgousis section 5.5
    n_runs: int = 5                # Georgousis section 6.1
    memory_window: int = 10        # Sabani section 4.1.4 (sliding window)
    model: ModelConfig = field(default_factory=ModelConfig)
    seed: int = 42
    message_max_words: int = 20
    message_policy: MessagePolicy = "meaningful"
    out_dir: str = "results"

    def to_dict(self) -> dict:
        return asdict(self)
