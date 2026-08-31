"""Plotting addon for cross_model_analysis.py.

Reads cross_model_aggregated.csv / cross_model_delta.csv / cross_model_master.csv
and emits PNG figures.

EVERY figure is produced per topology. Star and cycle are different experiments
and pooling them (or, worse, letting pivot_table's aggfunc="first" silently pick
whichever row came first) was the bug this module used to have. Filenames carry
the topology suffix; there is deliberately no pooled variant.

The x/row axis is `cell`, not `scenario`: the three framing_*_context scenarios
ran under both conditions and appear as `framing_team_context[no_comm]` and
`framing_team_context[cheap_talk]`. See cell_label() in cross_model_analysis.

Figures, per topology <T>:
  coop_rate_heatmap_{pd,sh}_<T>.png      cell x model heatmap
  delta_heatmap_{pd,sh}_<T>.png          delta vs the no_comm cell
  cheaptalk_delta_bars_{pd,sh}_<T>.png   the same deltas as grouped bars
  hub_exploitation_heatmap_<T>.png       hub said "cooperate", then defected
  trajectory_per_cell_{pd,sh}_<T>.png    coop rate vs round (needs --roots)
Figures that cross topologies:
  two_channel_dissociation_{pd,sh}.png   frame in prompt vs frame in messages
  topology_contrast_{pd,sh}.png          star vs cycle, every run shown

Usage:
    python cross_model_plots.py --in-dir cross_model_output_final
    python cross_model_plots.py --in-dir ... --roots results_dir1 results_dir2
    python cross_model_plots.py --in-dir ... --topology star

--roots is only needed for the trajectory figure, which re-reads every JSON.
"""
from __future__ import annotations

import argparse
import os
import sys

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Try seaborn for heatmaps; fall back to matplotlib if missing.
try:
    import seaborn as sns
    HAS_SEABORN = True
except ImportError:
    HAS_SEABORN = False

CELL_ORDER = [
    "no_comm",
    "baseline_cheap_talk",
    "no_sense",
    "silence",
    "counterfactual",
    "framing_business",
    "framing_team",
    "framing_competitive",
    "framing_business_context[no_comm]",
    "framing_business_context[cheap_talk]",
    "framing_team_context[no_comm]",
    "framing_team_context[cheap_talk]",
    "framing_competitive_context[no_comm]",
    "framing_competitive_context[cheap_talk]",
]

# Draw star before cycle; anything else after, alphabetically.
TOPOLOGY_ORDER = ["star", "cycle"]

# The three frames. Each was delivered three ways -- see the dissociation plot.
FRAMINGS = ["business", "team", "competitive"]


def order_cells(cells):
    """Return cells sorted by CELL_ORDER, with unknowns at the end."""
    cells = list(cells)
    known = [c for c in CELL_ORDER if c in cells]
    unknown = sorted(c for c in cells if c not in CELL_ORDER)
    return known + unknown


def topologies_in(df: pd.DataFrame) -> list[str]:
    if "topology" not in df.columns:
        raise SystemExit(
            "This CSV has no 'topology' column, so it predates the topology fix.\n"
            "Re-run cross_model_analysis.py before plotting."
        )
    present = set(df["topology"].dropna().unique())
    known = [t for t in TOPOLOGY_ORDER if t in present]
    return known + sorted(present - set(known))


def _cell_axis(df: pd.DataFrame) -> pd.DataFrame:
    """Accept older CSVs that only carry 'scenario'."""
    if "cell" not in df.columns and "scenario" in df.columns:
        df = df.copy()
        df["cell"] = df["scenario"]
    return df


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


def _pivot(sub: pd.DataFrame, values: str) -> pd.DataFrame:
    """cell x model matrix. Refuses to draw if anything is still being pooled."""
    dup = int(sub.duplicated(["cell", "model_id"]).sum())
    if dup:
        raise SystemExit(
            f"{dup} duplicate (cell, model) rows reached a pivot. Something is "
            "still being pooled that should not be -- do not plot this."
        )
    mat = sub.pivot(index="cell", columns="model_id", values=values)
    return mat.reindex(order_cells(mat.index.tolist()))


# ---------- Per-topology figures ----------

def plot_coop_rate_heatmaps(agg: pd.DataFrame, out_dir: str, topo: str):
    """One heatmap per game: rows=cells, cols=models, values=coop rate."""
    for game in ["pd", "sh"]:
        sub = agg[(agg["game"] == game) & (agg["topology"] == topo)]
        if sub.empty:
            continue
        mat = _pivot(sub, "coop_rate_overall_mean")
        _heatmap(
            mat,
            title=f"Cooperation rate by (model x cell) -- {game.upper()}, {topo}",
            cbar_label="Cooperation rate",
            out_path=os.path.join(out_dir, f"coop_rate_heatmap_{game}_{topo}.png"),
            cmap="RdYlGn", vmin=0, vmax=1,
        )


def plot_delta_heatmaps(delta_df: pd.DataFrame, out_dir: str, topo: str):
    """One heatmap per game: delta vs the no_comm cell of the same topology."""
    for game in ["pd", "sh"]:
        sub = delta_df[(delta_df["game"] == game) & (delta_df["topology"] == topo)]
        if sub.empty:
            continue
        mat = _pivot(sub, "delta")
        absmax = float(np.nanmax(np.abs(mat.values))) if mat.size else 1.0
        _heatmap(
            mat,
            title=f"Delta cooperation vs no_comm -- {game.upper()}, {topo}",
            cbar_label="Delta (cell - no_comm)",
            out_path=os.path.join(out_dir, f"delta_heatmap_{game}_{topo}.png"),
            cmap="RdBu_r", vmin=-absmax, vmax=absmax,
        )


def plot_hub_exploit_heatmap(agg: pd.DataFrame, out_dir: str, topo: str):
    sub = agg[(agg["game"] == "pd") & (agg["topology"] == topo)]
    if sub.empty:
        return
    mat = _pivot(sub, "hub_exploitation_rate_mean")
    if mat.dropna(how="all").empty:
        return
    _heatmap(
        mat,
        title=f"Hub exploitation rate (PD, {topo})\n"
              "Hub sent a cooperative-sounding message, then defected",
        cbar_label="Exploitation rate",
        out_path=os.path.join(out_dir, f"hub_exploitation_heatmap_{topo}.png"),
        cmap="OrRd", vmin=0, vmax=0.4,
    )


def plot_delta_bars(delta_df: pd.DataFrame, out_dir: str, topo: str):
    """Grouped bars: delta per (model, cell), one figure per game."""
    for game in ["pd", "sh"]:
        sub = delta_df[(delta_df["game"] == game) & (delta_df["topology"] == topo)]
        if sub.empty:
            continue
        models = sorted(sub["model_id"].unique())
        cells = order_cells(sub["cell"].unique())
        x = np.arange(len(cells))
        width = 0.8 / max(1, len(models))

        fig, ax = plt.subplots(figsize=(max(9, len(cells) * 1.1), 5))
        for i, model in enumerate(models):
            ms = sub[sub["model_id"] == model].set_index("cell")
            vals = [ms.loc[c, "delta"] if c in ms.index else np.nan for c in cells]
            ax.bar(x + i * width, vals, width, label=model)
        ax.axhline(0, color="black", lw=0.8)
        ax.set_xticks(x + width * (len(models) - 1) / 2)
        ax.set_xticklabels(cells, rotation=40, ha="right", fontsize=8)
        ax.set_ylabel("Delta cooperation (cell - no_comm)")
        ax.set_title(f"Cheap-talk delta by model x cell -- {game.upper()}, {topo}")
        ax.legend(loc="best", fontsize=8)
        ax.grid(axis="y", alpha=0.3)
        out = os.path.join(out_dir, f"cheaptalk_delta_bars_{game}_{topo}.png")
        plt.tight_layout()
        fig.savefig(out, dpi=120, bbox_inches="tight")
        plt.close(fig)
        print(f"  -> {out}")


# ---------- Figures that cross topologies ----------

def plot_two_channel_dissociation(agg: pd.DataFrame, out_dir: str):
    """The headline result.

    For each frame, three bars per model:
      messages = framing_X                          frame only in what agents say
      prompt   = framing_X_context[no_comm]         frame in the system prompt,
                                                    channel closed
      both     = framing_X_context[cheap_talk]      frame in the prompt, talk on
    If the frame acted through a single mechanism the three would move together.
    """
    for game in ["pd", "sh"]:
        sub = agg[agg["game"] == game]
        if sub.empty:
            continue
        topos = topologies_in(sub)
        models = sorted(sub["model_id"].unique())
        channels = [
            ("messages", "framing_{f}", "#4c72b0"),
            ("prompt", "framing_{f}_context[no_comm]", "#dd8452"),
            ("both", "framing_{f}_context[cheap_talk]", "#55a868"),
        ]
        fig, axes = plt.subplots(len(topos), len(FRAMINGS),
                                 figsize=(4.6 * len(FRAMINGS), 3.4 * len(topos)),
                                 squeeze=False, sharey=True)
        for r, topo in enumerate(topos):
            ts = sub[sub["topology"] == topo]
            for c, frame in enumerate(FRAMINGS):
                ax = axes[r][c]
                x = np.arange(len(models))
                width = 0.8 / len(channels)
                for i, (label, tmpl, color) in enumerate(channels):
                    cs = ts[ts["cell"] == tmpl.format(f=frame)].set_index("model_id")
                    vals = [cs.loc[m, "coop_rate_overall_mean"]
                            if m in cs.index else np.nan for m in models]
                    ax.bar(x + i * width, vals, width, color=color,
                           label=label if (r == 0 and c == 0) else None)
                ax.set_xticks(x + width)
                ax.set_xticklabels(models, rotation=35, ha="right", fontsize=7)
                ax.set_ylim(0, 1.05)
                ax.grid(axis="y", alpha=0.3)
                if c == 0:
                    ax.set_ylabel(f"{topo}\ncooperation rate")
                if r == 0:
                    ax.set_title(f"framing_{frame}", fontsize=10)
        handles, labels = axes[0][0].get_legend_handles_labels()
        fig.legend(handles, labels, loc="lower center", ncol=3,
                   bbox_to_anchor=(0.5, -0.03), fontsize=9)
        fig.suptitle(
            f"Two-channel dissociation -- {game.upper()}\n"
            "the same frame delivered through messages, through the system "
            "prompt, or both",
            fontsize=12)
        plt.tight_layout()
        out = os.path.join(out_dir, f"two_channel_dissociation_{game}.png")
        fig.savefig(out, dpi=120, bbox_inches="tight")
        plt.close(fig)
        print(f"  -> {out}")


def plot_topology_contrast(master: pd.DataFrame, out_dir: str):
    """star vs cycle per (model, cell), with the individual runs plotted.

    The individual runs are the point: several low-communication cells are
    bimodal, and a mean drawn without them reads as a moderate effect when no
    single run landed anywhere near it.
    """
    master = _cell_axis(master)
    for game in ["pd", "sh"]:
        sub = master[master["game"] == game]
        if sub.empty:
            continue
        models = sorted(sub["model_id"].unique())
        cells = order_cells(sub["cell"].unique())
        fig, axes = plt.subplots(
            len(models), 1,
            figsize=(max(9, len(cells) * 0.95), 2.5 * len(models)),
            squeeze=False, sharex=True)
        for r, model in enumerate(models):
            ax = axes[r][0]
            ms = sub[sub["model_id"] == model]
            for j, cell in enumerate(cells):
                cs = ms[ms["cell"] == cell]
                star = cs[cs["topology"] == "star"]["coop_rate_overall"].dropna()
                cyc = cs[cs["topology"] == "cycle"]["coop_rate_overall"].dropna()
                if len(star):
                    ax.scatter(np.full(len(star), j - 0.14), star, s=14,
                               color="#4c72b0", alpha=0.65, zorder=3,
                               label="star" if (r == 0 and j == 0) else None)
                    ax.hlines(star.mean(), j - 0.28, j, color="#4c72b0",
                              lw=2, zorder=4)
                if len(cyc):
                    ax.scatter(np.full(len(cyc), j + 0.14), cyc, s=14,
                               color="#dd8452", alpha=0.65, zorder=3,
                               label="cycle" if (r == 0 and j == 0) else None)
                    ax.hlines(cyc.mean(), j, j + 0.28, color="#dd8452",
                              lw=2, zorder=4)
            ax.set_ylim(-0.05, 1.05)
            ax.set_ylabel(model, fontsize=8)
            ax.grid(axis="y", alpha=0.3)
        axes[-1][0].set_xticks(range(len(cells)))
        axes[-1][0].set_xticklabels(cells, rotation=40, ha="right", fontsize=8)
        handles, labels = axes[0][0].get_legend_handles_labels()
        fig.legend(handles, labels, loc="lower center", ncol=2,
                   bbox_to_anchor=(0.5, -0.02), fontsize=9)
        fig.suptitle(f"star vs cycle, every run shown -- {game.upper()}",
                     fontsize=12)
        plt.tight_layout()
        out = os.path.join(out_dir, f"topology_contrast_{game}.png")
        fig.savefig(out, dpi=120, bbox_inches="tight")
        plt.close(fig)
        print(f"  -> {out}")


# ---------- Trajectory (needs raw JSONs) ----------

def collect_trajectories(roots: list[str]):
    """Walk roots; per (model, topology, cell, game, round), collect coop rates."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    # summarise_run / cell_label -- never the removed local derive_scenario.
    from cross_model_analysis import (
        discover_records, normalise_model_id, cell_label,
    )
    from analysis import summarise_run
    from games import GAMES

    rows = []
    for path, data in discover_records(roots):
        cfg = data.get("config", {})
        model_id = normalise_model_id(cfg.get("model", {}).get("model_id", "unknown"))
        summary = summarise_run(data)
        cell = cell_label(summary["scenario"], summary["condition"])
        topology = summary["topology"]
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
                "topology": topology,
                "cell": cell,
                "game": game_name,
                "round": r.get("round", -1),
                "coop_rate": n_coop / len(valid_actions),
            })
    return pd.DataFrame(rows)


def plot_trajectories(traj_df: pd.DataFrame, out_dir: str, topo: str):
    """One panel per cell; lines coloured by model. Separate PNG per game."""
    for game in ["pd", "sh"]:
        sub = traj_df[(traj_df["game"] == game) & (traj_df["topology"] == topo)]
        if sub.empty:
            continue
        cells = order_cells(sub["cell"].unique())
        models = sorted(sub["model_id"].unique().tolist())

        ncols = 3 if len(cells) > 2 else max(1, len(cells))
        nrows = (len(cells) + ncols - 1) // ncols
        fig, axes = plt.subplots(nrows, ncols, figsize=(ncols * 4.4, nrows * 2.8),
                                 squeeze=False)
        colors = plt.cm.tab10(np.linspace(0, 1, len(models)))

        for idx, cell in enumerate(cells):
            ax = axes[idx // ncols][idx % ncols]
            for color, model in zip(colors, models):
                sm = sub[(sub["cell"] == cell) & (sub["model_id"] == model)]
                if sm.empty:
                    continue
                grp = sm.groupby("round")["coop_rate"].mean()
                ax.plot(grp.index, grp.values, marker="o", markersize=3,
                        linewidth=1.2, color=color, label=model)
            ax.set_title(cell, fontsize=8)
            ax.set_xlabel("Round")
            ax.set_ylabel("Coop rate")
            ax.set_ylim(-0.05, 1.05)
            ax.grid(alpha=0.3)
            ax.set_xticks(range(1, 17, 3))
        for j in range(len(cells), nrows * ncols):
            axes[j // ncols][j % ncols].axis("off")

        handles, labels = axes[0][0].get_legend_handles_labels()
        if handles:
            fig.legend(handles, labels, loc="lower center",
                       ncol=len(models), bbox_to_anchor=(0.5, -0.02), fontsize=9)
        fig.suptitle(f"Cooperation trajectory by round -- {game.upper()}, {topo}",
                     fontsize=12, y=1.0)
        plt.tight_layout()
        out = os.path.join(out_dir, f"trajectory_per_cell_{game}_{topo}.png")
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
    ap.add_argument("--topology", nargs="+", default=None,
                    help="Restrict to these topologies (default: every one present).")
    args = ap.parse_args()

    out_dir = args.out_dir or args.in_dir
    os.makedirs(out_dir, exist_ok=True)

    agg_path = os.path.join(args.in_dir, "cross_model_aggregated.csv")
    delta_path = os.path.join(args.in_dir, "cross_model_delta.csv")
    master_path = os.path.join(args.in_dir, "cross_model_master.csv")
    if not os.path.exists(agg_path):
        print(f"Missing {agg_path}. Run cross_model_analysis.py first.")
        return
    agg = _cell_axis(pd.read_csv(agg_path))
    delta_df = (_cell_axis(pd.read_csv(delta_path))
                if os.path.exists(delta_path) else pd.DataFrame())
    master = (_cell_axis(pd.read_csv(master_path))
              if os.path.exists(master_path) else pd.DataFrame())

    topos = args.topology or topologies_in(agg)
    print(f"Topologies: {topos}")

    for topo in topos:
        print(f"\n=== {topo} ===")
        print("Coop-rate heatmaps...")
        plot_coop_rate_heatmaps(agg, out_dir, topo)
        if not delta_df.empty:
            print("Delta heatmaps...")
            plot_delta_heatmaps(delta_df, out_dir, topo)
            print("Delta bar charts...")
            plot_delta_bars(delta_df, out_dir, topo)
        print("Hub-exploitation heatmap...")
        plot_hub_exploit_heatmap(agg, out_dir, topo)

    print("\n=== across topologies ===")
    print("Two-channel dissociation...")
    plot_two_channel_dissociation(agg, out_dir)
    if not master.empty:
        print("Topology contrast...")
        plot_topology_contrast(master, out_dir)

    if args.roots:
        print("\nCollecting per-round trajectories (re-reading JSONs)...")
        traj_df = collect_trajectories(args.roots)
        print(f"  loaded {len(traj_df)} round-level rows")
        for topo in topos:
            plot_trajectories(traj_df, out_dir, topo)


if __name__ == "__main__":
    main()
