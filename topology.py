"""Star topology.

Agent 0 is the hub; agents 1..n-1 are leaves. Each leaf has a single edge to
the hub. There are no leaf-to-leaf edges.

Message semantics (for the cheap-talk condition):
  - The hub sends ONE broadcast message that reaches all leaves.
  - Each leaf sends ONE message that reaches the hub only.
  - Leaves do NOT see each other's messages. This is what makes the topology
    structurally non-trivial for cheap talk (if we broadcast to everyone, the
    star collapses to a fully-connected 4-agent game for comm purposes).
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class StarTopology:
    n_agents: int
    hub_id: int = 0

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
