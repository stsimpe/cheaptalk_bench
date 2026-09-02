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
# RQ4: a moderation layer inside the channel. The filter inspects each composed
# message and, when it fires, the message is not delivered -- the sender still
# writes it and is never told, the neighbours simply receive nothing from it
# that round. "none" keeps every pre-2026-09 run byte-identical.
MessageFilter = Literal["none", "F1_competitive", "F3_relative_gain"]
# "local" runs the model on the current machine via transformers (Kaggle / Colab
# / your own GPU). The other providers are remote API calls.
Provider = Literal["groq", "openai", "huggingface", "openrouter", "local"]

# Message-content policies (alibi for cheap-talk content control).
# See message_policies.py for what each one does.
MessagePolicy = Literal[
    "meaningful",       # default LLM strategic message
    "irrelevant",       # off-topic templates
    "no_sense",         # alias for irrelevant
    "silence",          # empty message
    "counterfactual",   # LLM asked for IF/WOULD framing
    "framing",          # LLM asked for social-context framing (see framing_type)
]

FramingType = Literal["business", "team", "competitive", "neutral"]

# Context framing: a framing paragraph injected into the SYSTEM prompt, so it
# applies in BOTH conditions (works without cheap talk). Distinct from the
# message-phase "framing" policy, which only shapes the communicate prompt.
ContextFraming = Literal["none", "business", "team", "competitive"]


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
    max_tokens: int = 512
    request_delay_s: float = 3.0
    max_retries: int = 4


TopologyName = Literal["star", "clique", "line", "cycle"]


@dataclass
class ExperimentConfig:
    """Top-level knobs for one full experiment (many runs of one condition)."""
    game: GameName = "pd"
    condition: ConditionName = "no_comm"
    topology: TopologyName = "star"
    n_agents: int = 4
    n_rounds: int = 16
    n_runs: int = 5
    memory_window: int = 10
    model: ModelConfig = field(default_factory=ModelConfig)
    seed: int = 42
    message_max_words: int = 20
    message_policy: MessagePolicy = "meaningful"
    # Sub-knob: only used when message_policy == "framing".
    framing_type: FramingType = "business"
    # System-prompt framing, independent of the message channel ("none" keeps
    # every pre-existing scenario byte-identical).
    context_framing: ContextFraming = "none"
    # Channel-side moderation, independent of what the agent was told to write
    # ("none" keeps every pre-existing scenario byte-identical). Orthogonal to
    # message_policy on purpose: framing_competitive + a filter is the RQ4 cell.
    message_filter: MessageFilter = "none"
    # Resample an invalid action up to this many times (0 = old behavior).
    action_retries: int = 0
    # Scenario label this run belongs to ("baseline", "framing_team_context",
    # ...). Set by the runner so every record self-identifies: without it the
    # only trace of the scenario is the output directory name, and a
    # framing_*_context run is indistinguishable from a baseline one by config
    # alone. Empty on the pre-2026-07 records, which are derived instead.
    scenario: str = ""
    out_dir: str = "results"

    def to_dict(self) -> dict:
        return asdict(self)
