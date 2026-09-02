"""Game engine.

Responsibilities:
  - Own the ground-truth history and payoff computation.
  - Filter each agent's view of history to what the topology exposes.
  - Run rounds (two-phase in the cheap-talk case).
  - Produce a single run-record dict that is serialised to JSON.

Payoff semantics:
  Every agent commits to one action per round. For each edge (a, b), we
  compute the pairwise payoff of a against b and of b against a, and sum
  across a node's edges to get that node's round payoff. The hub therefore
  plays 3 pairwise instances of the game per round, each leaf plays 1.

Invalid actions (model output that doesn't canonicalise to a valid label) are
recorded but excluded from payoff computation that round for the offending
agent (the agent gets 0 for that round and the flag is stored). This matches
Sabani's invalid-rate metric.
"""
from __future__ import annotations

from dataclasses import asdict
from typing import Callable

from agent import Agent
from config import ExperimentConfig, ModelConfig
from games import Game, GAMES
from llm_client import make_client
from topology import StarTopology, make_topology


class GameEngine:
    def __init__(self, game: Game, topology, condition: str, cfg: ExperimentConfig):
        self.game = game
        self.topology = topology
        self.condition = condition
        self.cfg = cfg
        self.valid_actions = set(game.action_labels)

    def build_agents(self, client, run_id: int = 0) -> list[Agent]:
        agents: list[Agent] = []
        for i in range(self.topology.n_agents):
            neighbors = self.topology.neighbors(i)
            agents.append(
                Agent(
                    agent_id=i,
                    n_neighbors=len(neighbors),
                    neighbor_ids=neighbors,
                    total_agents=self.topology.n_agents,
                    game=self.game,
                    condition=self.condition,
                    client=client,
                    message_max_words=self.cfg.message_max_words,
                    memory_window=self.cfg.memory_window,
                    message_policy=self.cfg.message_policy,
                    framing_type=self.cfg.framing_type,
                    context_framing=getattr(self.cfg, "context_framing", "none"),
                    message_filter=getattr(self.cfg, "message_filter", "none"),
                    topology_text=self.topology.describe(i),
                    noise_seed=self.cfg.seed + run_id,
                    action_retries=getattr(self.cfg, "action_retries", 0),
                )
            )
        return agents

    def _messages_seen_by(self, messages: dict[int, str]) -> dict[int, dict[int, str]]:
        """For each agent, which messages are visible to it?

        Rules (star topology):
          - Hub sees messages from all its neighbors (all leaves).
          - Leaf sees message from its only neighbor (the hub).
        """
        seen: dict[int, dict[int, str]] = {i: {} for i in range(self.topology.n_agents)}
        for sender, msg in messages.items():
            for nb in self.topology.neighbors(sender):
                seen[nb][sender] = msg
        return seen

    def _compute_payoffs(self, actions: dict[int, str]) -> dict[int, int]:
        """Sum of pairwise payoffs across each agent's edges."""
        payoffs = {i: 0 for i in range(self.topology.n_agents)}
        for (u, v) in self.topology.edges():
            a_u = actions.get(u)
            a_v = actions.get(v)
            if a_u not in self.valid_actions or a_v not in self.valid_actions:
                continue
            payoffs[u] += self.game.payoffs[(a_u, a_v)][0]
            payoffs[v] += self.game.payoffs[(a_v, a_u)][0]
        return payoffs

    def _run_round_no_comm(self, round_num: int, agents: list[Agent], history: list[dict]) -> dict:
        actions: dict[int, str] = {}
        reasonings: dict[int, str] = {}
        invalid_flags: dict[int, bool] = {}
        for agent in agents:
            action, reasoning = agent.choose_action_no_comm(history, round_num)
            actions[agent.agent_id] = action
            reasonings[agent.agent_id] = reasoning
            invalid_flags[agent.agent_id] = action not in self.valid_actions
        payoffs = self._compute_payoffs(actions)
        return {
            "round": round_num,
            "actions": actions,
            "reasonings": reasonings,
            "invalid": invalid_flags,
            "payoffs": payoffs,
        }

    def _run_round_cheap_talk(self, round_num: int, agents: list[Agent], history: list[dict]) -> dict:
        messages: dict[int, str] = {}          # what neighbours receive
        composed: dict[int, str] = {}          # what the sender actually wrote
        blocked: dict[int, bool] = {}
        comm_reasonings: dict[int, str] = {}
        for agent in agents:
            msg, written, reasoning, was_blocked = agent.send_message(history, round_num)
            messages[agent.agent_id] = msg
            composed[agent.agent_id] = written
            blocked[agent.agent_id] = was_blocked
            comm_reasonings[agent.agent_id] = reasoning

        seen = self._messages_seen_by(messages)

        actions: dict[int, str] = {}
        action_reasonings: dict[int, str] = {}
        invalid_flags: dict[int, bool] = {}
        for agent in agents:
            # The sender knows what it wrote even if the channel dropped it --
            # the filter moderates delivery, not the agent.
            own = composed[agent.agent_id]
            received = seen[agent.agent_id]
            action, reasoning = agent.choose_action_cheap_talk(history, round_num, own, received)
            actions[agent.agent_id] = action
            action_reasonings[agent.agent_id] = reasoning
            invalid_flags[agent.agent_id] = action not in self.valid_actions

        payoffs = self._compute_payoffs(actions)
        record = {
            "round": round_num,
            "messages": messages,
            "messages_seen_by": seen,
            "comm_reasonings": comm_reasonings,
            "actions": actions,
            "reasonings": action_reasonings,
            "invalid": invalid_flags,
            "payoffs": payoffs,
        }
        # Only written when a filter is active, so unfiltered records keep the
        # exact schema every earlier run has.
        if any(blocked.values()) or getattr(self.cfg, "message_filter", "none") != "none":
            record["messages_composed"] = composed
            record["messages_blocked"] = blocked
        return record

    def run_one(self, run_id: int, client) -> dict:
        agents = self.build_agents(client, run_id=run_id)
        history: list[dict] = []
        for r in range(1, self.cfg.n_rounds + 1):
            if self.condition == "no_comm":
                record = self._run_round_no_comm(r, agents, history)
            else:
                record = self._run_round_cheap_talk(r, agents, history)
            history.append(record)
            actions_str = ", ".join(
                f"{i}:{record['actions'][i][:1]}" for i in range(self.topology.n_agents)
            )
            tok_str = ""
            tokens = getattr(client, "session_tokens", None)
            if tokens is not None:
                tok_str = f"  [tokens: {tokens:,}]"
            print(f"  run {run_id} round {r:2d}: {actions_str}  "
                  f"payoffs {record['payoffs']}{tok_str}")

        return {
            "run_id": run_id,
            "config": self.cfg.to_dict(),
            "topology": self.topology.to_dict(),
            "game": self.game.name,
            "history": history,
        }


def make_engine(cfg: ExperimentConfig) -> GameEngine:
    game = GAMES[cfg.game]
    topo = make_topology(getattr(cfg, "topology", "star"), n_agents=cfg.n_agents)
    return GameEngine(game=game, topology=topo, condition=cfg.condition, cfg=cfg)
