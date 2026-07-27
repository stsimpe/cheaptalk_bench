"""Message policies for cheap talk ablation experiments.

A message policy controls WHAT the agent says during the communication phase
of cheap talk. Policies fall into two categories:

  REPLACEMENT policies (override the LLM output entirely):
    - meaningful   : LLM-generated strategic message (default)
    - irrelevant   : canned off-topic templates (alias: no_sense)
    - no_sense     : alias for irrelevant
    - silence      : empty string (channel exists, zero content)

  AUGMENTATION policies (instruct the LLM to use a specific style):
    - counterfactual : message must be phrased as IF-WOULD counterfactual
    - framing        : message uses social framing (business/team/competitive)

REPLACEMENT vs AUGMENTATION:
  Replacement policies skip the LLM call (no tokens spent).
  Augmentation policies still call the LLM but inject an extra instruction
  into the user prompt to shape the output.

Mapping to thesis RQs:
  - irrelevant/no_sense + silence: RQ1 content-vs-channel control
  - counterfactual: RQ1 content type, RQ4 intervention prototype
  - framing (per Lore & Heydari 2024): RQ1 framing axis
"""
from __future__ import annotations

import random
from typing import Literal

# All currently supported policy names.
MessagePolicy = Literal[
    "meaningful",
    "irrelevant",
    "no_sense",
    "silence",
    "counterfactual",
    "framing",
]

FramingType = Literal["business", "team", "competitive", "neutral"]


# Replacement-policy templates: off-topic small talk that has nothing to do
# with the game. Used by irrelevant / no_sense.
IRRELEVANT_TEMPLATES = [
    "Nice weather today.",
    "I had coffee this morning.",
    "The sky is blue.",
    "It's a sunny day.",
    "I like pizza.",
    "Time flies.",
    "Water is wet.",
    "Birds can fly.",
    "The Earth is round.",
    "Music is enjoyable.",
]


# Augmentation-policy instructions: inserted into the COMMUNICATE phase user
# prompt. Crafted so the LLM understands the constraint without the system
# prompt being changed (which would confound with the framing experiments).

COUNTERFACTUAL_INSTRUCTION = (
    "SPECIAL CONSTRAINT FOR THIS MESSAGE: phrase your message as a "
    "COUNTERFACTUAL claim. A counterfactual describes what WOULD happen, "
    "or what WOULD have happened, in a hypothetical scenario. Examples:\n"
    "  - \"If I had defected last round, I would have gained 6 instead of 4.\"\n"
    "  - \"If you cooperate this round, we both keep the streak alive.\"\n"
    "  - \"If neither of us defects, mutual trust holds for one more round.\"\n"
    "Your message MUST contain at least one IF/WOULD construction."
)

FRAMING_INSTRUCTIONS: dict[str, str] = {
    "business": (
        "SPECIAL CONSTRAINT FOR THIS MESSAGE: phrase your message in a "
        "professional/business tone. Treat the interaction as a commercial "
        "partnership where you and your neighbor are co-investors in a "
        "joint venture. Use vocabulary like 'investment', 'returns', "
        "'partnership', 'risk', 'contract'."
    ),
    "team": (
        "SPECIAL CONSTRAINT FOR THIS MESSAGE: phrase your message in a "
        "team-cooperative tone. Treat the interaction as a team challenge "
        "where you succeed or fail together. Use vocabulary like 'team', "
        "'together', 'we', 'shared goal', 'support'."
    ),
    "competitive": (
        "SPECIAL CONSTRAINT FOR THIS MESSAGE: phrase your message in a "
        "competitive tone. Treat the interaction as a contest with stakes "
        "and rivals. Use vocabulary like 'win', 'compete', 'rival', "
        "'advantage', 'edge'."
    ),
    "neutral": "",  # no augmentation -- equivalent to meaningful
}


# Context-framing paragraphs: injected into the SYSTEM prompt (after the
# topology paragraph), so they apply to BOTH conditions — including no_comm,
# where the message-phase framing above never fires. This is the control that
# separates "the social frame changes behavior" from "the frame changes the
# messages, and the messages change behavior". Vocabulary deliberately mirrors
# FRAMING_INSTRUCTIONS so the two mechanisms are comparable.
CONTEXT_FRAMING_PARAGRAPHS: dict[str, str] = {
    "business": (
        "Context: treat this interaction as a commercial partnership. You and "
        "your neighbors are co-investors in a joint venture, and each round is "
        "a business decision involving investment, returns, risk and contracts."
    ),
    "team": (
        "Context: treat this interaction as a team challenge. You and your "
        "neighbors are teammates working toward a shared goal — you succeed "
        "or fail together, and every round is a chance to support the team."
    ),
    "competitive": (
        "Context: treat this interaction as a contest with stakes and rivals. "
        "You and your neighbors are competitors, and every round is a chance "
        "to gain an advantage, get the edge and win."
    ),
    "none": "",
}


def get_context_framing_paragraph(context_framing: str) -> str:
    """Return the system-prompt context paragraph ('' when framing is 'none')."""
    return CONTEXT_FRAMING_PARAGRAPHS.get(context_framing, "")


def get_extra_message_instruction(
    policy: MessagePolicy, framing_type: str = "business",
) -> str:
    """Return extra instruction appended to the message-phase user prompt.

    Returns "" for replacement policies and meaningful (no augmentation).
    For counterfactual/framing, returns the corresponding constraint string.
    """
    if policy == "counterfactual":
        return COUNTERFACTUAL_INSTRUCTION
    if policy == "framing":
        return FRAMING_INSTRUCTIONS.get(framing_type, FRAMING_INSTRUCTIONS["business"])
    return ""


def is_replacement_policy(policy: MessagePolicy) -> bool:
    """Replacement policies skip the LLM call entirely."""
    return policy in ("irrelevant", "no_sense", "silence")


def apply_policy(
    policy: MessagePolicy,
    agent_id: int,
    round_num: int,
    llm_message: str,
    noise_seed: int = 0,
) -> str:
    """Apply replacement policy or pass through LLM output.

    noise_seed varies per run (the engine passes cfg.seed + run_id), so the
    canned no_sense templates differ between replicate runs. The old
    behavior (noise_seed=0) drew the SAME template sequence in every run,
    which made the N replicates non-independent for this scenario. Keeping
    noise_seed in the seed keeps runs reproducible from the config.
    """
    if policy in ("meaningful", "counterfactual", "framing"):
        return llm_message
    if policy in ("irrelevant", "no_sense"):
        seed = noise_seed * 100_000 + agent_id * 1000 + round_num
        rng = random.Random(seed)
        return rng.choice(IRRELEVANT_TEMPLATES)
    if policy == "silence":
        return ""
    raise ValueError(f"Unknown message policy: {policy}")
