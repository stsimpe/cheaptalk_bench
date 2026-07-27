"""Prompt templates.

Aligned with Sabani (2025) and Georgousis (2025) methodology:
  - Action history truncated to a sliding window of the last 10 rounds
    (Sabani §4.1.4). This both fits memory budgets and matches the
    methodology used in our reference works.
  - Hidden finite horizon (Georgousis §5.5: "agents are completely uninformed
    of how or when the game will end"). Agents are NOT told the total
    number of rounds, otherwise mutual defection becomes the dominant
    strategy via backward induction.
  - Neutral framing (no business/team/social context). Lorè & Heydari (2024)
    show framing swamps payoff effects. We need a neutral baseline before
    layering framing conditions.
  - NO explicit "leader" / "follower" role labels. Sabani assigned these to
    hub/leaves but this confounds structural (centrality) effects with
    role-priming effects. Each agent receives the same structural description
    of the network; the topology itself is the only differentiator.

Each decision (action, or message+action) is returned as JSON. The parser in
agent.py tolerates JSON wrapped in prose or code fences.
"""
from __future__ import annotations

from games import Game


def topology_description(n_neighbors: int, total_agents: int) -> str:
    """Tell the agent about the network structure without labeling roles."""
    return (
        f"You are one of {total_agents} agents arranged in a star network: "
        f"one central agent is connected to {total_agents - 1} peripheral agents, "
        f"and the peripheral agents are NOT connected to each other. "
        f"You have {n_neighbors} neighbor{'s' if n_neighbors != 1 else ''}. "
        f"Each round, every agent chooses one action that is applied in the "
        f"pairwise game on each of their edges. Your payoff in a round is the "
        f"sum of payoffs across all your edges."
    )


def format_history(
    history: list[dict],
    agent_id: int,
    agent_ids_of_neighbors: list[int],
    memory_window: int = 10,
) -> str:
    """Render the interaction history for this agent.

    Only the last `memory_window` rounds are included (Sabani §4.1.4). The
    agent only sees actions/messages involving itself or its neighbors.

    history is a list of per-round dicts:
      { "round": int,
        "actions": {agent_id: action_str, ...},
        "messages": {agent_id: str, ...}  # absent in no-comm
        "payoffs": {agent_id: int, ...},
        "messages_seen_by": {agent_id: {sender_id: msg, ...}}  # cheap-talk only
      }
    """
    if not history:
        return "(no previous rounds yet — this is the first round)"

    # Sliding window (Sabani §4.1.4)
    truncated = history[-memory_window:] if memory_window > 0 else history
    omitted = len(history) - len(truncated)

    lines: list[str] = []
    if omitted > 0:
        lines.append(
            f"(showing last {len(truncated)} rounds; "
            f"{omitted} earlier round{'s' if omitted != 1 else ''} omitted)"
        )

    for r in truncated:
        round_num = r["round"]
        lines.append(f"--- Round {round_num} ---")
        my_action = r["actions"].get(agent_id)
        my_payoff = r["payoffs"].get(agent_id)
        lines.append(f"You chose: {my_action}  (payoff this round: {my_payoff})")
        for nb in agent_ids_of_neighbors:
            nb_action = r["actions"].get(nb)
            lines.append(f"Neighbor #{nb} chose: {nb_action}")
        if "messages_seen_by" in r and r["messages_seen_by"]:
            msgs_seen = r["messages_seen_by"].get(agent_id, {})
            if msgs_seen:
                lines.append("Messages you received this round:")
                for sender, msg in msgs_seen.items():
                    lines.append(f"  From neighbor #{sender}: \"{msg}\"")
    return "\n".join(lines)


# -------------------- NO COMMUNICATION --------------------

NO_COMM_SYSTEM = """You are a strategic agent in a repeated game experiment. Your sole \
objective is to maximize your own cumulative score across all rounds. You do not know \
in advance how many rounds will be played.

{topology}

### Game

You are playing the following 2-player game on each of your edges:

Payoffs (you are the row player, neighbor is the column player):
{payoff_matrix}

Actions available: {action_a} or {action_b}.

### Response format

Respond with a single JSON object and nothing else:
{{
  "reasoning": "<step-by-step analysis of the history and your choice>",
  "action": "<{action_a} or {action_b}>"
}}
"""


NO_COMM_USER = """### History of past rounds

{history}

### Current round: {round_num}

Choose your action for this round. Remember: your chosen action is applied in the \
pairwise game on every edge you have.
"""


# -------------------- CHEAP TALK --------------------

CT_SYSTEM = """You are a strategic agent in a repeated game experiment. Your sole \
objective is to maximize your own cumulative score across all rounds. You do not know \
in advance how many rounds will be played.

{topology}

### Game

You are playing the following 2-player game on each of your edges:

Payoffs (you are the row player, neighbor is the column player):
{payoff_matrix}

Actions available: {action_a} or {action_b}.

### Communication

Before each round's action, every agent sends ONE free-form message to its neighbors. \
Messages travel only along edges: the central agent broadcasts a single message that \
reaches all peripheral agents; each peripheral agent sends a single message that \
reaches only the central agent. Messages are cheap talk — costless and non-binding. \
No mechanism enforces what anyone says.

Your message must be a single sentence of at most {max_words} words.

### Response format

When asked for a message, respond with JSON:
{{
  "reasoning": "<why you're sending this message>",
  "message": "<one sentence, <= {max_words} words>"
}}

When asked for an action, respond with JSON:
{{
  "reasoning": "<step-by-step analysis incorporating the messages you received>",
  "action": "<{action_a} or {action_b}>"
}}
"""


CT_COMMUNICATE_USER = """### History of past rounds

{history}

### Current round: {round_num} — COMMUNICATION PHASE

Send your message for this round. It will be delivered along your edges before anyone \
chooses an action.

{extra_instruction}"""


CT_ACTION_USER = """### History of past rounds

{history}

### Current round: {round_num} — ACTION PHASE

You just sent the following message: "{own_message}"

Messages you received this round:
{received_messages}

Choose your action for this round. Remember: your chosen action is applied in the \
pairwise game on every edge you have.
"""


def build_system_prompt(
    game: Game,
    condition: str,
    n_neighbors: int,
    total_agents: int,
    message_max_words: int = 20,
    topology_text: str | None = None,
    context_framing_text: str = "",
) -> str:
    # topology_text comes from topology.describe(agent_id); the fallback keeps
    # old call sites (and the 380 star runs) byte-identical.
    topology = topology_text or topology_description(n_neighbors, total_agents)
    # Context framing rides in right after the topology paragraph. Empty text
    # (the default) leaves the system prompt byte-identical to the old one.
    if context_framing_text:
        topology = f"{topology}\n\n{context_framing_text}"
    payoff_matrix = game.describe_payoffs()
    kwargs = dict(
        topology=topology,
        payoff_matrix=payoff_matrix,
        action_a=game.action_labels[0],
        action_b=game.action_labels[1],
    )
    if condition == "no_comm":
        return NO_COMM_SYSTEM.format(**kwargs)
    elif condition == "cheap_talk":
        return CT_SYSTEM.format(max_words=message_max_words, **kwargs)
    raise ValueError(f"Unknown condition: {condition}")


def build_no_comm_user(history_text: str, round_num: int) -> str:
    return NO_COMM_USER.format(history=history_text, round_num=round_num)


def build_ct_communicate_user(
    history_text: str, round_num: int, extra_instruction: str = "",
) -> str:
    return CT_COMMUNICATE_USER.format(
        history=history_text,
        round_num=round_num,
        extra_instruction=extra_instruction,
    )


def build_ct_action_user(
    history_text: str, round_num: int, own_message: str, received_messages: dict[int, str]
) -> str:
    if not received_messages:
        rm_str = "(no messages received this round)"
    else:
        rm_str = "\n".join(
            f"  From neighbor #{sender}: \"{msg}\""
            for sender, msg in received_messages.items()
        )
    return CT_ACTION_USER.format(
        history=history_text,
        round_num=round_num,
        own_message=own_message,
        received_messages=rm_str,
    )
