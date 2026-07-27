"""Content-contrast heatmap: each scenario minus baseline_cheap_talk.

The existing delta_heatmap_*.png measures each scenario against the NO-comm
baseline, which mixes the *channel* effect with the *content* effect.

This plot instead measures each cheap-talk scenario against
`baseline_cheap_talk` (default free-form messaging). Because every cell here
is a cheap-talk condition, the channel is held fixed and the difference
isolates the CONTENT effect alone -- exactly the RQ1 "does tone steer the
equilibrium?" question.

  contrast = coop_rate(scenario) - coop_rate(baseline_cheap_talk)

  * Negative (blue) = this content manipulation HURT cooperation relative to
    plain meaningful cheap talk (e.g. competitive framing).
  * Near zero (white) = the content change had no effect beyond plain cheap
    talk (e.g. business/team framing in the strong models).
  * Positive (red) = the content change further improved cooperation.

Usage:
    python framing_contrast_plot.py --in-dir cross_model_output
    # optional: restrict to framing scenarios only
    python framing_contrast_plot.py --in-dir cross_model_output --framings-only
"""
from __future__ import annotations

import argparse
import os

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

try:
    import seaborn as sns
    HAS_SEABORN = True
except ImportError:
    HAS_SEABORN = False


# Scenarios contrasted against baseline_cheap_talk, in display order.
CONTRAST_SCENARIOS = [
    "no_sense",
    "silence",
    "counterfactual",
    "framing_business",
    "framing_team",
    "framing_competitive",
]
FRAMINGS_ONLY = ["framing_business", "framing_team", "framing_competitive"]

REFERENCE = "baseline_cheap_talk"


def _heatmap(matrix: pd.DataFrame, title: str, cbar_label: str, out_path: str,
             cmap="RdBu_r", vmin=None, vmax=None, fmt=".2f"):
    fig, ax = plt.subplots(figsize=(max(6, 0.9 * matrix.shape[1] + 3),
                                    max(4, 0.5 * matrix.shape[0] + 2)))
    if HAS_SEABORN:
        sns.heatmap(matrix, annot=True, fmt=fmt, cmap=cmap, vmin=vmin, vmax=vmax,
                    cbar_kws={"label": cbar_label}, ax=ax, linewidths=0.5,
                    linecolor="white", annot_kws={"size": 9})
    else:
        im = ax.imshow(matrix.values, aspect="auto", cmap=cmap, vmin=vmin, vmax=vmax)
        ax.set_xticks(range(matrix.shape[1])); ax.set_xticklabels(matrix.columns, rotation=45, ha="right")
        ax.set_yticks(range(matrix.shape[0])); ax.set_yticklabels(matrix.index)
        for i in range(matrix.shape[0]):
            for j in range(matrix.shape[1]):
                v = matrix.values[i, j]
                if not np.isnan(v):
                    ax.text(j, i, format(v, fmt), ha="center", va="center", fontsize=8)
        fig.colorbar(im, ax=ax, label=cbar_label)
    ax.set_title(title)
    plt.tight_layout()
    fig.savefig(out_path, dpi=120, bbox_inches="tight")
    plt.close(fig)
    print(f"  -> {out_path}")


def build_contrast(agg: pd.DataFrame, game: str, scenarios: list[str]) -> pd.DataFrame:
    """Rows = scenarios, cols = models, cells = coop(scenario) - coop(baseline_cheap_talk)."""
    sub = agg[agg["game"] == game]
    # coop rate per (model, scenario)
    coop = sub.pivot_table(index="scenario", columns="model_id",
                           values="coop_rate_overall_mean", aggfunc="first")
    if REFERENCE not in coop.index:
        raise SystemExit(f"'{REFERENCE}' not found for game={game}; cannot contrast.")
    ref = coop.loc[REFERENCE]
    rows = {}
    for sc in scenarios:
        if sc in coop.index:
            rows[sc] = coop.loc[sc] - ref
    return pd.DataFrame(rows).T  # scenarios as rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in-dir", default="cross_model_output")
    ap.add_argument("--out-dir", default=None)
    ap.add_argument("--framings-only", action="store_true",
                    help="Only the three framing scenarios (drops no_sense/silence/counterfactual).")
    args = ap.parse_args()

    out_dir = args.out_dir or args.in_dir
    os.makedirs(out_dir, exist_ok=True)

    agg_path = os.path.join(args.in_dir, "cross_model_aggregated.csv")
    if not os.path.exists(agg_path):
        raise SystemExit(f"Missing {agg_path}. Run cross_model_analysis.py first.")
    agg = pd.read_csv(agg_path)

    scenarios = FRAMINGS_ONLY if args.framings_only else CONTRAST_SCENARIOS
    suffix = "_framings" if args.framings_only else ""

    for game in ["pd", "sh"]:
        if game not in agg["game"].unique():
            continue
        mat = build_contrast(agg, game, scenarios)
        if mat.empty:
            continue
        absmax = float(np.nanmax(np.abs(mat.values))) if mat.size else 1.0
        out = os.path.join(out_dir, f"content_contrast_heatmap_{game}{suffix}.png")
        _heatmap(
            mat,
            title=f"Content effect vs. plain cheap talk -- {game.upper()}\n"
                  f"(scenario coop rate minus baseline_cheap_talk; channel held fixed)",
            cbar_label="Delta vs baseline_cheap_talk",
            out_path=out, cmap="RdBu_r", vmin=-absmax, vmax=absmax,
        )

    # Also dump the numbers to CSV for the report/poster tables.
    all_rows = []
    for game in ["pd", "sh"]:
        if game not in agg["game"].unique():
            continue
        mat = build_contrast(agg, game, scenarios)
        for scenario in mat.index:
            for model in mat.columns:
                all_rows.append({
                    "game": game, "scenario": scenario, "model_id": model,
                    "contrast_vs_baseline_cheap_talk": mat.loc[scenario, model],
                })
    csv_out = os.path.join(out_dir, f"content_contrast{suffix}.csv")
    pd.DataFrame(all_rows).to_csv(csv_out, index=False)
    print(f"  -> {csv_out}")


if __name__ == "__main__":
    main()
