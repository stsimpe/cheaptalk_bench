"""RQ4 figure: framing_competitive (PD, star) unfiltered vs F3 vs F1, per model.

Every run is drawn, so the reader sees spread rather than a mean alone, and the
cooperation level that meaningful cheap talk reaches is marked for scale: the
gap a defence would have to close is the distance to that line.

    python cheaptalk_bench/rq4_filter_plot.py --root . --out figures/rq4_filter_outcome.png
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analysis import summarise_run  # noqa: E402

MODELS = ["Llama-3.1-8B-Instruct", "Qwen2.5-7B-Instruct", "gemma-2-9b-it",
          "gemma-2-2b-it", "Qwen3-4B"]
ARMS = [  # label, colour (fixed categorical order), marker, glob patterns
    ("unfiltered (n=10)", "#2a78d6", "o",
     ["{m}_star/framing_competitive/cheap_talk/*.json",
      "rq4/replicates_n10/{m}/framing_competitive/cheap_talk/*.json"]),
    ("F3, narrow filter", "#eb6834", "s",
     ["rq4/filtered_F3/{m}_F3_relative_gain/framing_competitive/cheap_talk/*.json"]),
    ("F1, broad filter", "#1baf7a", "^",
     ["rq4/filtered_F1/{m}_F1_competitive/framing_competitive/cheap_talk/*.json"]),
]


def coop_rates(root: str, patterns: list[str], model: str) -> list[float]:
    out = []
    for pat in patterns:
        for p in sorted(glob.glob(os.path.join(root, pat.format(m=model)))):
            with open(p, encoding="utf-8") as f:
                rec = json.load(f)
            if rec["config"]["game"] == "pd":
                out.append(summarise_run(rec)["coop_rate_overall"])
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--out", default="figures/rq4_filter_outcome.png")
    args = ap.parse_args()

    fig, ax = plt.subplots(figsize=(7.2, 3.4), dpi=200)
    ink, muted = "#0b0b0b", "#898781"
    ax.axhspan(0.98, 1.0, color="#e4e3df", zorder=0)
    ax.text(len(MODELS) - 0.5, 0.955, "meaningful cheap talk: 0.98-1.00",
            ha="right", va="top", fontsize=8, color="#52514e")

    width = 0.26
    for j, (label, colour, marker, pats) in enumerate(ARMS):
        for i, m in enumerate(MODELS):
            vals = coop_rates(args.root, pats, m)
            if not vals:
                raise SystemExit(f"no runs for {m} / {label}")
            x = i + (j - 1) * width
            jitter = np.linspace(-0.06, 0.06, len(vals))
            ax.scatter(x + jitter, vals, s=12, color=colour, alpha=0.45,
                       marker=marker, linewidths=0, zorder=2)
            ax.plot([x - 0.1, x + 0.1], [np.mean(vals)] * 2, color=colour,
                    lw=2, solid_capstyle="round", zorder=3)
            ax.scatter([], [], color=colour, marker=marker, s=24,
                       label=label if i == 0 else None)

    ax.set_xticks(range(len(MODELS)))
    ax.set_xticklabels(MODELS, fontsize=8, color=ink)
    ax.set_ylim(-0.03, 1.03)
    ax.set_ylabel("PD cooperation rate", fontsize=9, color=ink)
    ax.tick_params(colors=muted, labelsize=8)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(muted)
    ax.grid(axis="y", color="#ecebe7", lw=0.6, zorder=0)
    ax.legend(loc="upper left", bbox_to_anchor=(0, 0.93), frameon=False,
              fontsize=8, ncol=3, handletextpad=0.3, columnspacing=1.2)
    fig.tight_layout()
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    fig.savefig(args.out, facecolor="white")
    print("wrote", args.out)


if __name__ == "__main__":
    main()
