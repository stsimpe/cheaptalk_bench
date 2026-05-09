"""Game definitions: pairwise 2x2 normal-form games.

Payoff matrices follow Georgousis (2025), Tables 5.4(a) and 5.4(d). These
satisfy:
  - PD strong condition: ba > aa > bb > ab  (i.e. T > R > P > S)
  - PD anti-alternation condition: 2*aa > ba + ab
    (prevents the trivial alternating-cooperate-defect strategy that beats
    mutual cooperation)
  - SH condition: aa > ba >= bb > ab

We adopt Georgousis' values (rather than Madmoun's 3/0/5/1 or 10/3/0) for
two reasons:
  1. They are concrete numerical assignments (Sabani uses a generic
     ordinal cost matrix without specifying numbers).
  2. The anti-alternation condition is satisfied: e.g., for PD,
     2*4 = 8 > 1 + 6 = 7, so agents cannot beat mutual cooperation by
     simply alternating C/D.
  3. They are pairwise (2-player) by construction, which fits our star
     topology where each edge is a separate game (Madmoun's N-player payoffs
     would not work on a star).

Each edge in the star runs an independent instance of the same 2x2 game.
Every agent commits to one action per round that applies on all its edges.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Game:
    name: str
    action_labels: tuple[str, str]   # (cooperative/risky, defective/safe)
    cooperative_action: str          # the label that we count as "cooperation"
    payoffs: dict[tuple[str, str], tuple[int, int]]

    def payoff(self, a_self: str, a_other: str) -> int:
        """Payoff for the row player playing a_self against a_other."""
        return self.payoffs[(a_self, a_other)][0]

    def describe_payoffs(self) -> str:
        """Text block suitable for pasting into prompts."""
        c, d = self.action_labels
        row = lambda x: f"| {x:9s} | {self.payoffs[(x, c)][0]}, {self.payoffs[(x, c)][1]} | {self.payoffs[(x, d)][0]}, {self.payoffs[(x, d)][1]} |"
        return (
            f"|           | {c:9s} | {d:9s} |\n"
            f"| --------- | --------- | --------- |\n"
            f"{row(c)}\n"
            f"{row(d)}"
        )


# PD payoffs from Georgousis (2025) Table 5.4(a):
#   CC=(4,4)  CD=(1,6)  DC=(6,1)  DD=(2,2)
# Satisfies T(6) > R(4) > P(2) > S(1) (strong PD)
# Satisfies 2*R(8) > T+S(7)        (no profitable alternation)
PRISONERS_DILEMMA = Game(
    name="Prisoner's Dilemma",
    action_labels=("Cooperate", "Defect"),
    cooperative_action="Cooperate",
    payoffs={
        ("Cooperate", "Cooperate"): (4, 4),
        ("Cooperate", "Defect"):    (1, 6),
        ("Defect",    "Cooperate"): (6, 1),
        ("Defect",    "Defect"):    (2, 2),
    },
)

# SH payoffs from Georgousis (2025) Table 5.4(d):
#   SS=(6,6)  SH=(1,4)  HS=(4,1)  HH=(2,2)
# Satisfies aa(6) > ba(4) >= bb(2) > ab(1)  (Stag Hunt)
STAG_HUNT = Game(
    name="Stag Hunt",
    action_labels=("Stag", "Hare"),
    cooperative_action="Stag",
    payoffs={
        ("Stag", "Stag"): (6, 6),
        ("Stag", "Hare"): (1, 4),
        ("Hare", "Stag"): (4, 1),
        ("Hare", "Hare"): (2, 2),
    },
)


GAMES: dict[str, Game] = {
    "pd": PRISONERS_DILEMMA,
    "sh": STAG_HUNT,
}
