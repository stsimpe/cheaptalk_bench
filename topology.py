"""Network topologies.

Every topology exposes the same interface, and the engine only ever calls
these four things:

    n_agents            -> int
    neighbors(agent_id) -> list[int]
    edges()             -> list[tuple[int, int]]
    describe(agent_id)  -> str   (topology paragraph for that agent's prompt)

Message semantics are identical everywhere: each agent sends ONE message per
round and it is delivered to all of its neighbors, nothing else. What changes
between topologies is only who the neighbors are.

  - StarTopology: agent 0 is the hub, leaves connect only to it. The hub's
    message reaches all leaves, each leaf's message reaches only the hub.
    Leaves never see each other's messages.
  - CliqueTopology: every agent is connected to every other agent, so every
    message is effectively a broadcast to the whole population. This is the
    comparison case for RQ2: no node is structurally privileged.
  - LineTopology: agents form a path 0-1-2-...-(n-1). Interior nodes have two
    neighbors, endpoints one. Included because it is free once the protocol
    exists, and it gives a third point on the centrality axis.
  - CycleTopology: agents form a ring 0-1-...-(n-1)-0. Every node has exactly
    two neighbors, so it is degree-regular like the clique but sparse like the
    line: no node is structurally privileged AND no message reaches everyone
    in one hop. This separates "symmetry" from "connectivity" in RQ2.

The prompt descriptions deliberately avoid role labels (no "leader"/"hub"
words beyond the structural description), matching the design decision of
the star experiments.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class StarTopology:
    n_agents: int
    hub_id: int = 0

    name = "star"

    @property
    def leaf_ids(self) -> list[int]:
        return [i for i in range(self.n_agents) if i != self.hub_id]

    def neighbors(self, agent_id: int) -> list[int]:
        if agent_id == self.hub_id:
            return self.leaf_ids
        return [self.hub_id]

    def is_hub(self, agent_id: int) -> bool:
        return agent_id == self.hub_id

    def position_label(self, agent_id: int) -> str:
        return "hub" if self.is_hub(agent_id) else "leaf"

    def edges(self) -> list[tuple[int, int]]:
        """Undirected edges as (hub, leaf) pairs."""
        return [(self.hub_id, leaf) for leaf in self.leaf_ids]

    def describe(self, agent_id: int) -> str:
        n_neighbors = len(self.neighbors(agent_id))
        return (
            f"You are one of {self.n_agents} agents arranged in a star network: "
            f"one central agent is connected to {self.n_agents - 1} peripheral agents, "
            f"and the peripheral agents are NOT connected to each other. "
            f"You have {n_neighbors} neighbor{'s' if n_neighbors != 1 else ''}. "
            f"Each round, every agent chooses one action that is applied in the "
            f"pairwise game on each of their edges. Your payoff in a round is the "
            f"sum of payoffs across all your edges."
        )

    def to_dict(self) -> dict:
        return {
            "type": self.name,
            "n_agents": self.n_agents,
            "hub_id": self.hub_id,
            "edges": self.edges(),
        }


@dataclass
class CliqueTopology:
    n_agents: int

    name = "clique"

    def neighbors(self, agent_id: int) -> list[int]:
        return [i for i in range(self.n_agents) if i != agent_id]

    def edges(self) -> list[tuple[int, int]]:
        return [
            (i, j)
            for i in range(self.n_agents)
            for j in range(i + 1, self.n_agents)
        ]

    def position_label(self, agent_id: int) -> str:
        return "clique"

    def describe(self, agent_id: int) -> str:
        return (
            f"You are one of {self.n_agents} agents arranged in a fully connected "
            f"network: every agent is connected to every other agent. "
            f"You have {self.n_agents - 1} neighbors. "
            f"Each round, every agent chooses one action that is applied in the "
            f"pairwise game on each of their edges. Your payoff in a round is the "
            f"sum of payoffs across all your edges."
        )

    def to_dict(self) -> dict:
        return {
            "type": self.name,
            "n_agents": self.n_agents,
            "edges": self.edges(),
        }


@dataclass
class LineTopology:
    n_agents: int

    name = "line"

    def neighbors(self, agent_id: int) -> list[int]:
        out = []
        if agent_id > 0:
            out.append(agent_id - 1)
        if agent_id < self.n_agents - 1:
            out.append(agent_id + 1)
        return out

    def edges(self) -> list[tuple[int, int]]:
        return [(i, i + 1) for i in range(self.n_agents - 1)]

    def position_label(self, agent_id: int) -> str:
        return "endpoint" if agent_id in (0, self.n_agents - 1) else "interior"

    def describe(self, agent_id: int) -> str:
        n_neighbors = len(self.neighbors(agent_id))
        return (
            f"You are one of {self.n_agents} agents arranged in a line network: "
            f"the agents form a chain and each agent is connected only to the "
            f"agents directly adjacent to it in the chain. "
            f"You have {n_neighbors} neighbor{'s' if n_neighbors != 1 else ''}. "
            f"Each round, every agent chooses one action that is applied in the "
            f"pairwise game on each of their edges. Your payoff in a round is the "
            f"sum of payoffs across all your edges."
        )

    def to_dict(self) -> dict:
        return {
            "type": self.name,
            "n_agents": self.n_agents,
            "edges": self.edges(),
        }


@dataclass
class CycleTopology:
    n_agents: int

    name = "cycle"

    def __post_init__(self):
        if self.n_agents < 3:
            raise ValueError(
                f"CycleTopology needs at least 3 agents, got {self.n_agents}"
            )

    def neighbors(self, agent_id: int) -> list[int]:
        prev = (agent_id - 1) % self.n_agents
        nxt = (agent_id + 1) % self.n_agents
        # n_agents == 3: prev and nxt are distinct, but keep the sorted,
        # duplicate-free form so the list is stable for any n.
        return sorted({prev, nxt})

    def edges(self) -> list[tuple[int, int]]:
        return [(i, (i + 1) % self.n_agents) for i in range(self.n_agents)]

    def position_label(self, agent_id: int) -> str:
        return "cycle"

    def describe(self, agent_id: int) -> str:
        return (
            f"You are one of {self.n_agents} agents arranged in a ring network: "
            f"the agents form a closed cycle and each agent is connected only to "
            f"the two agents directly adjacent to it in the ring. "
            f"You have 2 neighbors. "
            f"Each round, every agent chooses one action that is applied in the "
            f"pairwise game on each of their edges. Your payoff in a round is the "
            f"sum of payoffs across all your edges."
        )

    def to_dict(self) -> dict:
        return {
            "type": self.name,
            "n_agents": self.n_agents,
            "edges": self.edges(),
        }


TOPOLOGIES = {
    "star": StarTopology,
    "clique": CliqueTopology,
    "line": LineTopology,
    "cycle": CycleTopology,
}


def make_topology(name: str, n_agents: int):
    if name not in TOPOLOGIES:
        raise ValueError(f"Unknown topology: {name!r} (choose from {sorted(TOPOLOGIES)})")
    return TOPOLOGIES[name](n_agents=n_agents)
