"""The three topologies side by side, every run drawn (PD).

Companion to `topology_compare.py` and to the RQ2 table: the claim there is
that the star sits below the other two and that the ring and the clique are
indistinguishable, and several of these cells are bimodal, so the runs have to
be visible -- a mean drawn alone reads as a moderate effect when no single run
landed near it.

Ring runs come from the corrected-prompt re-measurement for the session-A
cells, the same source the RQ2 table uses.

Usage:
    python topology_three_plot.py --star <star folders> --ring <cycle_commfix folders>
        --clique <clique folders> --out figures/topology_three_pd.png
"""
from __future__ import annotations

import argparse
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from topology_compare import load

CELLS = [("no_comm", "no_comm"), ("silence", "silence"), ("no_sense", "no_sense"),
         ("counterfactual", "counterfactual"),
         ("baseline_cheap_talk", "cheap talk")]
TOPOS = [("star", "star  (degree 1 leaf)", "#4c72b0"),
         ("ring", "ring  (degree 2)", "#dd8452"),
         ("clique", "clique  (degree 3)", "#55a868")]
OFFSET = {"star": -0.24, "ring": 0.0, "clique": 0.24}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--star", nargs="+", required=True)
    ap.add_argument("--ring", nargs="+", required=True)
    ap.add_argument("--clique", nargs="+", required=True)
    ap.add_argument("--game", default="pd")
    ap.add_argument("--out", default="figures/topology_three_pd.png")
    args = ap.parse_args()

    data = {"star": load(args.star, args.game), "ring": load(args.ring, args.game),
            "clique": load(args.clique, args.game)}
    models = sorted({m for d in data.values() for (m, _) in d})

    fig, axes = plt.subplots(len(models), 1, figsize=(7.2, 1.55 * len(models)),
                             sharex=True, squeeze=False)
    for r, model in enumerate(models):
        ax = axes[r][0]
        for j, (cell, _) in enumerate(CELLS):
            for topo, label, color in TOPOS:
                runs = [x["coop"] for x in data[topo].get((model, cell), [])]
                if not runs:
                    continue
                o = OFFSET[topo]
                jitter = np.linspace(-0.05, 0.05, len(runs))
                ax.scatter(np.full(len(runs), j + o) + jitter, runs, s=13,
                           color=color, alpha=0.6, linewidths=0, zorder=3,
                           label=label if (r == 0 and j == 0) else None)
                ax.hlines(np.mean(runs), j + o - 0.11, j + o + 0.11,
                          color=color, lw=2.2, zorder=4)
        ax.axvline(2.5, color="0.7", lw=0.8, ls=":")
        ax.set_ylim(-0.05, 1.05)
        ax.set_yticks([0, 0.5, 1.0])
        ax.set_ylabel(model, fontsize=8)
        ax.grid(axis="y", alpha=0.25)
        ax.tick_params(labelsize=8)
    axes[-1][0].set_xticks(range(len(CELLS)))
    axes[-1][0].set_xticklabels([lab for _, lab in CELLS], fontsize=9)
    axes[-1][0].set_xlim(-0.6, len(CELLS) - 0.4)
    handles, labels = axes[0][0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=3, fontsize=9,
               frameon=False, bbox_to_anchor=(0.5, -0.015))
    fig.suptitle("Star, ring and clique: every run, "
                 f"{args.game.upper()}", fontsize=11)
    fig.text(0.5, 0.945, "left of the dotted line the channel carries no content, "
             "which is where topology shows; right of it, messages", ha="center",
             fontsize=8, color="0.35")
    fig.tight_layout(rect=(0, 0.02, 1, 0.94))
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    fig.savefig(args.out, dpi=150, bbox_inches="tight")
    print(f"-> {args.out}")


if __name__ == "__main__":
    main()
