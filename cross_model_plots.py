"""Plotting addon for cross_model_analysis.py.

Reads cross_model_aggregated.csv + cross_model_master.csv and emits PNG plots:
  - coop_rate_heatmap_pd.png            scenario × model heatmap (PD)
  - coop_rate_heatmap_sh.png            scenario × model heatmap (SH)
  - delta_heatmap_pd.png                Δ vs no_comm baseline (PD)
  - delta_heatmap_sh.png                Δ vs no_comm baseline (SH)
  - hub_exploitation_heatmap.png        hub deception rate (PD only)
  - cheaptalk_delta_bars_pd.png         bar chart of Δ per model (PD)
  - cheaptalk_delta_bars_sh.png         bar chart of Δ per model (SH)
  - trajectory_per_scenario.png         coop rate vs round, one panel per scenario

Usage:
    pip install matplotlib seaborn
    python cross_model_plots.py --in-dir cross_model_output --roots ...

The --roots argument is only needed for the trajectory plot, which has to
re-load each JSON's round-by-round actions. The other plots use only the
aggregated CSVs.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys
from collections import defaultdict

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl

# Try seaborn for heatmaps; fall back to matplotlib if missing.
try:
    import seaborn as sns
    HAS_SEABORN = True
except ImportError:
    HAS_SEABORN = False

SCENARIO_ORDER = [
    "no_comm",
    "baseline_cheap_talk",
    "no_sense",
    "silence",
    "counterfactual",
    "framing_business",
    "framing_team",
    "framing_competitive",
]


def order_scenarios(scenarios):
    """Return scenarios sorted by SCENARIO_ORDER, with unknowns at the end."""
    known = [s for s in SCENARIO_ORDER if s in scenarios]
    unknown = sorted(s for s in scenarios if s not in SCENARIO_ORDER)
    return known + unknown


def _heatmap(matrix: pd.DataFrame, title: str, cbar_label: str, out_path: str,
             cmap: str = "RdYlGn", vmin=None, vmax=None, fmt: str = ".2f"):
    """Draw a heatmap from a pandas DataFrame and save to PNG."""
    fig, ax = plt.subplots(figsize=(max(6, 0.8 * matrix.shape[1] + 3),
                                    max(4, 0.4 * matrix.shape[0] + 2)))
    if HAS_SEABORN:
        sns.heatmap(
            matrix, annot=True, fmt=fmt, cmap=cmap, vmin=vmin, vmax=vmax,
            cbar_kws={"label": cbar_label}, ax=ax, linewidths=0.5,
            linecolor="white", annot_kws={"size": 9},
        )
    else:
        im = ax.imshow(matrix.values, aspect="auto", cmap=cmap,
                       vmin=vmin, vmax=vmax)
        ax.set_xticks(range(matrix.shape[1]))
        ax.set_xticklabels(matrix.columns, rotation=45, ha="right")
        ax.set_yticks(range(matrix.shape[0]))
        ax.set_yticklabels(matrix.index)
        for i in range(matrix.shape[0]):
            for j in range(matrix.shape[1]):
                v = matrix.values[i, j]
                if np.isnan(v):
                    continue
                ax.text(j, i, format(v, fmt), ha="center", va="center",
                        color="black", fontsize=8)
        fig.colorbar(im, ax=ax, label=cbar_label)
    ax.set_title(title)
    plt.tight_layout()
    fig.savefig(out_path, dpi=120, bbox_inches="tight")
    plt.close(fig)
    print(f"  -> {out_path}")


def plot_coop_rate_heatmaps(agg: pd.DataFrame, out_dir: str):
    """One heatmap per game: rows=scenarios, cols=models, cells=coop rate."""
    for game in ["pd", "sh"]:
        sub = agg[agg["game"] == game]
        if sub.empty:
            continue
        mat = sub.pivot_table(
            index="scenario", columns="model_id",
            values="coop_rate_overall_mean", aggfunc="first",
        )
        mat = mat.reindex(order_scenarios(mat.index.tolist()))
        out = os.path.join(out_dir, f"coop_rate_heatmap_{game}.png")
        _heatmap(
            mat,
            title=f"Cooperation rate by (model × scenario) — {game.upper()}",
            cbar_label="Cooperation rate",
            out_path=out, cmap="RdYlGn", vmin=0, vmax=1,
        )


def plot_delta_heatmaps(delta_df: pd.DataFrame, out_dir: str):
    """One heatmap per game: rows=scenarios, cols=models, cells=Δ vs no_comm."""
    for game in ["pd", "sh"]:
        sub = delta_df[delta_df["game"] == game]
        if sub.empty:
            continue
        mat = sub.pivot_table(
            index="scenario", columns="model_id",
            values="delta", aggfunc="first",
        )
        mat = mat.reindex(order_scenarios(mat.index.tolist()))
        out = os.path.join(out_dir, f"delta_heatmap_{game}.png")
        # diverging colour map centred at 0
        absmax = float(np.nanmax(np.abs(mat.values))) if not mat.empty else 1.0
        _heatmap(
            mat,
            title=f"Δ cooperation vs no_comm baseline — {game.upper()}",
            cbar_label="Δ (cheap-talk − no_comm)",
            out_path=out, cmap="RdBu_r",
            vmin=-absmax, vmax=absmax,
        )


def plot_hub_exploit_heatmap(agg: pd.DataFrame, out_dir: str):
    sub = agg[agg["game"] == "pd"]
    if sub.empty:
        return
    mat = sub.pivot_table(
        index="scenario", columns="model_id",
        values="hub_exploitation_rate_mean", aggfunc="first",
    )
    if mat.dropna(how="all").empty:
        return
    mat = mat.reindex(order_scenarios(mat.index.tolist()))
    out = os.path.join(out_dir, "hub_exploitation_heatmap.png")
    _heatmap(
        mat,
        title="Hub exploitation rate (PD cheap-talk only)\n"
              "Hub sent cooperative-sounding message, then defected",
        cbar_label="Exploitation rate",
        out_path=out, cmap="OrRd", vmin=0, vmax=0.4,
    )


def plot_delta_bars(delta_df: pd.DataFrame, out_dir: str):
    """Bar chart: Δ per (model, scenario), one figure per game."""
    for game in ["pd", "sh"]:
        sub = delta_df[delta_df["game"] == game].copy()
        if sub.empty:
            continue
        # Order scenarios and models
        sub["scenario"] = pd.Categorical(
            sub["scenario"],
            categories=[s for s in order_scenarios(sub["scenario"].unique())
                        if s != "no_comm"],
            ordered=True,
        )
        models = sorted(sub["model_id"].unique())
        scenarios = [s for s in SCENARIO_ORDER if s in sub["scenario"].unique()]
        x = np.arange(len(scenarios))
        width = 0.8 / max(1, len(models))

        fig, ax = plt.subplots(figsize=(max(8, len(scenarios) * 1.2), 5))
        for i, model in enumerate(models):
            ms = sub[sub["model_id"] == model].set_index("scenario")
            vals = [ms.loc[s, "delta"] if s in ms.index else np.nan for s in scenarios]
            ax.bar(x + i * width, vals, width, label=model)
        ax.axhline(0, color="black", lw=0.8)
        ax.set_xticks(x + width * (len(models) - 1) / 2)
        ax.set_xticklabels(scenarios, rotation=30, ha="right")
        ax.set_ylabel("Δ cooperation (cheap_talk − no_comm)")
        ax.set_title(f"Cheap-talk Δ by model × scenario — {game.upper()}")
        ax.legend(loc="best", fontsize=8)
        ax.grid(axis="y", alpha=0.3)
        out = os.path.join(out_dir, f"cheaptalk_delta_bars_{game}.png")
        plt.tight_layout()
        fig.savefig(out, dpi=120, bbox_inches="tight")
        plt.close(fig)
        print(f"  -> {out}")


# ---------- Trajectory (needs raw JSONs) ----------

def collect_trajectories(roots: list[str]):
    """Walk roots; per (model, scenario, game, round), collect coop rates."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    # scenario_of (not the local derive_scenario) -- see cross_model_analysis.
    from cross_model_analysis import (
        discover_records, normalise_model_id,
    )
    from analysis import scenario_of
    from games import GAMES

    rows = []
    for path, data in discover_records(roots):
        cfg = data.get("config", {})
        model_id = normalise_model_id(cfg.get("model", {}).get("model_id", "unknown"))
        scenario = scenario_of(data)
        game_name = cfg.get("game")
        if game_name not in GAMES:
            continue
        coop_label = GAMES[game_name].cooperative_action
        valid = set(GAMES[game_name].action_labels)
        for r in data.get("history", []):
            actions = r.get("actions", {})
            valid_actions = [a for a in actions.values() if a in valid]
            if not valid_actions:
                continue
            n_coop = sum(1 for a in valid_actions if a == coop_label)
            rows.append({
                "model_id": model_id,
                "scenario": scenario,
                "game": game_name,
                "round": r.get("round", -1),
                "coop_rate": n_coop / len(valid_actions),
            })
    return pd.DataFrame(rows)


def plot_trajectories(traj_df: pd.DataFrame, out_dir: str):
    """One panel per scenario; lines colored by model. Separate PNG per game."""
    for game in ["pd", "sh"]:
        sub = traj_df[traj_df["game"] == game]
        if sub.empty:
            continue
        scenarios = order_scenarios(sub["scenario"].unique().tolist())
        models = sorted(sub["model_id"].unique().tolist())

        nrows = (len(scenarios) + 1) // 2
        ncols = 2 if len(scenarios) > 1 else 1
        fig, axes = plt.subplots(nrows, ncols, figsize=(ncols * 5, nrows * 3),
                                 squeeze=False)
        colors = plt.cm.tab10(np.linspace(0, 1, len(models)))

        for idx, scenario in enumerate(scenarios):
            ax = axes[idx // ncols][idx % ncols]
            for color, model in zip(colors, models):
                sm = sub[(sub["scenario"] == scenario) & (sub["model_id"] == model)]
                if sm.empty:
                    continue
                grp = sm.groupby("round")["coop_rate"].mean()
                ax.plot(grp.index, grp.values, marker="o", markersize=3,
                        linewidth=1.2, color=color, label=model)
            ax.set_title(scenario, fontsize=10)
            ax.set_xlabel("Round")
            ax.set_ylabel("Coop rate")
            ax.set_ylim(-0.05, 1.05)
            ax.grid(alpha=0.3)
            ax.set_xticks(range(1, 17, 2))
        # Hide unused subplots
        for j in range(len(scenarios), nrows * ncols):
            axes[j // ncols][j % ncols].axis("off")

        # One legend for the whole figure
        handles, labels = axes[0][0].get_legend_handles_labels()
        if handles:
            fig.legend(handles, labels, loc="lower center",
                       ncol=len(models), bbox_to_anchor=(0.5, -0.02), fontsize=9)
        fig.suptitle(f"Cooperation trajectory by round — {game.upper()}",
                     fontsize=12, y=1.0)
        plt.tight_layout()
        out = os.path.join(out_dir, f"trajectory_per_scenario_{game}.png")
        fig.savefig(out, dpi=110, bbox_inches="tight")
        plt.close(fig)
        print(f"  -> {out}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in-dir", default="cross_model_output",
                    help="Folder with cross_model_aggregated.csv etc.")
    ap.add_argument("--out-dir", default=None,
                    help="Where to write PNGs (default: same as in-dir).")
    ap.add_argument("--roots", nargs="+", default=None,
                    help="If provided, also plot per-round trajectory (re-reads JSONs).")
    args = ap.parse_args()

    out_dir = args.out_dir or args.in_dir
    os.makedirs(out_dir, exist_ok=True)

    agg_path = os.path.join(args.in_dir, "cross_model_aggregated.csv")
    delta_path = os.path.join(args.in_dir, "cross_model_delta.csv")
    if not os.path.exists(agg_path):
        print(f"Missing {agg_path}. Run cross_model_analysis.py first.")
        return
    agg = pd.read_csv(agg_path)
    delta_df = pd.read_csv(delta_path) if os.path.exists(delta_path) else pd.DataFrame()

    print("Plotting coop-rate heatmaps...")
    plot_coop_rate_heatmaps(agg, out_dir)

    if not delta_df.empty:
        print("Plotting Δ heatmaps...")
        plot_delta_heatmaps(delta_df, out_dir)
        print("Plotting Δ bar charts...")
        plot_delta_bars(delta_df, out_dir)

    print("Plotting hub-exploitation heatmap...")
    plot_hub_exploit_heatmap(agg, out_dir)

    if args.roots:
        print("Collecting per-round trajectories (re-reading JSONs)...")
        traj_df = collect_trajectories(args.roots)
        print(f"  loaded {len(traj_df)} round-level rows")
        plot_trajectories(traj_df, out_dir)


if __name__ == "__main__":
    main()
