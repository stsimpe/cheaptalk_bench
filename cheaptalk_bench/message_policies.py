"""Message policies for cheap talk ablation experiments.

A "message policy" overrides the agent's LLM-generated message with a canned
template. This lets us test whether the cheap talk effect depends on message
CONTENT or merely on the presence of a communication CHANNEL.

Three policies:
  - meaningful: LLM-generated strategic messages (default cheap talk)
  - irrelevant: off-topic messages unrelated to the game
  - silence: empty string (channel exists but no info transmitted)
"""
from __future__ import annotations

import random
from typing import Literal

MessagePolicy = Literal["meaningful", "irrelevant", "silence"]

# Templates for irrelevant messages (randomly sampled per agent per round)
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


def apply_policy(
    policy: MessagePolicy,
    agent_id: int,
    round_num: int,
    llm_message: str,
) -> str:
    """Apply the message policy to override (or pass through) the LLM output.
    
    Args:
        policy: which policy to apply
        agent_id: used for seeding irrelevant message selection
        round_num: used for seeding irrelevant message selection
        llm_message: what the LLM generated
    
    Returns:
        The final message to send (may be the LLM message or a template)
    """
    if policy == "meaningful":
        return llm_message
    elif policy == "irrelevant":
        # Deterministic random selection based on agent+round for reproducibility
        seed = agent_id * 1000 + round_num
        rng = random.Random(seed)
        return rng.choice(IRRELEVANT_TEMPLATES)
    elif policy == "silence":
        return ""
    else:
        raise ValueError(f"Unknown message policy: {policy}")
