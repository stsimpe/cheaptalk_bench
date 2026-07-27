"""Cross-model analysis of cheap-talk benchmark results.

Walks multiple result directories, identifies model + scenario + game from
each JSON's config (not from folder names -- folders are inconsistent across
runs), computes per-run metrics, and produces:

  - cross_model_master.csv      one row per saved run (raw metrics)
  - cross_model_aggregated.csv  mean + 95% bootstrap CI per (model, scenario, game)
  - cross_model_delta.csv       cheap-talk Δ vs no_comm baseline, per (model, game)
  - cross_model_report.md       human-readable markdown report

Usage:
    python cross_model_analysis.py \
        --roots \
            "C:/Users/tsimp/OneDrive/Υπολογιστής/diplomatikh/run1_qwen2.5_7b" \
            "C:/Users/tsimp/OneDrive/Υπολογιστής/diplomatikh/run2_qwen3_4b" \
            "C:/Users/tsimp/OneDrive/Υπολογιστής/diplomatikh/run_3_gemma_2_2b_it" \
            "C:/Users/tsimp/OneDrive/Υπολογιστής/diplomatikh/run_4_gemma_2_9b_it" \
            "C:/Users/tsimp/OneDrive/Υπολογιστής/diplomatikh/run5_llama_3.1_8b_instruct" \
        --out-dir cross_model_output

Notes:
  * Reads ALL *.json under the roots; ignores files that don't look like
    cheap-talk-bench result records.
  * Scenario is derived from the JSON's `config.message_policy` +
    `config.framing_type` + `config.condition` -- NOT from the folder name.
  * If you have multiple runs for the same (model, scenario, game), they are
    treated as independent samples.
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

# Pull in the per-run metrics function from analysis.py.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analysis import summarise_run


# ---------- Scenario normalisation ----------

def derive_scenario(cfg: dict) -> str:
    """Identify the scenario from config fields.

    Folder names are inconsistent across the project (`cheap_talk_baseline_1`,
    `cheap_talk_no_sense_qwen3_4b`, `framing_business`, `cf_qwen3_4b`...). The
    JSON's config block, however, is normalised. We use that.
    """
    condition = cfg.get("condition", "")
    policy = cfg.get("message_policy", "meaningful")
    framing = cfg.get("framing_type", "business")

    if condition == "no_comm":
        return "no_comm"
    # cheap_talk variants:
    if policy == "meaningful":
        return "baseline_cheap_talk"
    if policy in ("irrelevant", "no_sense"):
        return "no_sense"
    if policy == "silence":
        return "silence"
    if policy == "counterfactual":
        return "counterfactual"
    if policy == "framing":
        return f"framing_{framing}"
    return f"unknown_{policy}"


def normalise_model_id(model_id: str) -> str:
    """Map raw model ids to a canonical, short label."""
    aliases = {
        "llama-3.1-8b-instant": "Qwen2.5-7B-Instruct",  # Groq alias was used early; correct only if model_id was set explicitly
    }
    # Strip HF org prefix for readability ("meta-llama/Llama-3.1-8B-Instruct" -> "Llama-3.1-8B-Instruct").
    if "/" in model_id:
        model_id = model_id.split("/")[-1]
    return model_id


# ---------- Bootstrap CI ----------

def bootstrap_ci(values, n_resamples=1000, ci=95, seed=42):
    """Mean + bootstrap CI for a sample."""
    values = np.asarray(values, dtype=float)
    values = values[~np.isnan(values)]
    if len(values) == 0:
        return (np.nan, np.nan, np.nan)
    if len(values) == 1:
        v = float(values[0])
        return (v, v, v)
    rng = np.random.default_rng(seed)
    boot = rng.choice(values, size=(n_resamples, len(values)), replace=True).mean(axis=1)
    lo = float(np.percentile(boot, (100 - ci) / 2))
    hi = float(np.percentile(boot, 100 - (100 - ci) / 2))
    return (float(values.mean()), lo, hi)


# ---------- Discovery ----------

def is_cheaptalk_record(d: dict) -> bool:
    return (
        isinstance(d, dict)
        and "config" in d
        and "history" in d
        and isinstance(d["history"], list)
        and len(d["history"]) > 0
    )


def discover_records(roots: list[str]):
    """Walk roots, yield (path, json_data) for every cheap-talk-bench result."""
    seen_paths = set()
    for root in roots:
        if not os.path.exists(root):
            print(f"  [warn] root not found: {root}")
            continue
        pattern = os.path.join(root, "**", "*.json")
        for path in glob.glob(pattern, recursive=True):
            if path in seen_paths:
                continue
            seen_paths.add(path)
            try:
                with open(path, encoding="utf-8") as f:
                    data = json.load(f)
            except (json.JSONDecodeError, OSError, UnicodeDecodeError):
                continue
            if not is_cheaptalk_record(data):
                continue
            yield path, data


# ---------- Main analysis ----------

METRIC_COLS = [
    "coop_rate_overall",
    "coop_rate_hub",
    "coop_rate_leaf",
    "hub_minus_leaf_coop",
    "hub_total_payoff",
    "leaf_avg_payoff",
    "hub_leadership_rate",
    "hub_exploitation_rate",
    "invalid_rate",
    "full_coop_rate",
]


def build_master_dataframe(roots: list[str]) -> pd.DataFrame:
    rows = []
    n_total = 0
    n_skipped = 0
    for path, data in discover_records(roots):
        n_total += 1
        cfg = data.get("config", {})
        model_cfg = cfg.get("model", {})
        model_id_raw = model_cfg.get("model_id", "unknown")
        scenario = derive_scenario(cfg)
        try:
            summary = summarise_run(data)
        except Exception as e:
            n_skipped += 1
            continue
        rows.append({
            "path": path,
            "model_id": normalise_model_id(model_id_raw),
            "model_id_raw": model_id_raw,
            "game": summary["game"],
            "condition": summary["condition"],
            "scenario": scenario,
            "framing_type": cfg.get("framing_type", ""),
            "n_rounds": summary["n_rounds"],
            "n_runs_config": cfg.get("n_runs", -1),
            "run_id": summary["run_id"],
            **{m: summary.get(m, np.nan) for m in METRIC_COLS},
        })
    print(f"  discovered {n_total} json files, kept {len(rows)} runs ({n_skipped} skipped)")
    return pd.DataFrame(rows)


def aggregate(master: pd.DataFrame) -> pd.DataFrame:
    rows = []
    grouped = master.groupby(["model_id", "scenario", "game"])
    for (model, scenario, game), sub in grouped:
        row = {
            "model_id": model,
            "scenario": scenario,
            "game": game,
            "n_runs": len(sub),
        }
        for metric in METRIC_COLS:
            if metric not in sub.columns:
                continue
            vals = sub[metric].dropna().values
            mean, lo, hi = bootstrap_ci(vals)
            row[f"{metric}_mean"] = mean
            row[f"{metric}_ci_lo"] = lo
            row[f"{metric}_ci_hi"] = hi
        rows.append(row)
    return pd.DataFrame(rows)


def compute_deltas(master: pd.DataFrame) -> pd.DataFrame:
    """Cheap-talk Δ vs no_comm baseline, per (model, game, scenario)."""
    rows = []
    for (model, game), sub in master.groupby(["model_id", "game"]):
        no_comm = sub[sub["scenario"] == "no_comm"]["coop_rate_overall"].dropna().values
        if len(no_comm) == 0:
            continue
        nc_mean, nc_lo, nc_hi = bootstrap_ci(no_comm)
        for scenario, sc_sub in sub.groupby("scenario"):
            if scenario == "no_comm":
                continue
            ct_vals = sc_sub["coop_rate_overall"].dropna().values
            if len(ct_vals) == 0:
                continue
            ct_mean, ct_lo, ct_hi = bootstrap_ci(ct_vals)
            rows.append({
                "model_id": model,
                "game": game,
                "scenario": scenario,
                "no_comm_mean": nc_mean,
                "no_comm_ci_lo": nc_lo,
                "no_comm_ci_hi": nc_hi,
                "cheap_talk_mean": ct_mean,
                "cheap_talk_ci_lo": ct_lo,
                "cheap_talk_ci_hi": ct_hi,
                "delta": ct_mean - nc_mean,
                "n_no_comm": len(no_comm),
                "n_cheap_talk": len(ct_vals),
            })
    return pd.DataFrame(rows)


def write_markdown_report(
    out_path: str,
    master: pd.DataFrame,
    aggregated: pd.DataFrame,
    deltas: pd.DataFrame,
) -> None:
    lines: list[str] = []
    lines.append("# Cross-Model Cheap-Talk Analysis\n\n")
    lines.append(f"**Total runs analysed:** {len(master)}\n\n")
    lines.append(f"**Models:** {sorted(master['model_id'].unique().tolist())}\n\n")
    lines.append(f"**Scenarios:** {sorted(master['scenario'].unique().tolist())}\n\n")
    lines.append(f"**Games:** {sorted(master['game'].unique().tolist())}\n\n")
    lines.append("---\n\n")

    # Cooperation rate matrix
    lines.append("## Mean cooperation rate by (scenario × model × game)\n\n")
    try:
        pivot = aggregated.pivot_table(
            index="scenario",
            columns=["model_id", "game"],
            values="coop_rate_overall_mean",
            aggfunc="first",
        ).round(3)
        lines.append(pivot.to_markdown() + "\n\n")
    except Exception as e:
        lines.append(f"_(pivot failed: {e})_\n\n")

    # Cheap-talk Δ
    lines.append("## Cheap-talk Δ in cooperation (cheap_talk_x − no_comm)\n\n")
    try:
        delta_pivot = deltas.pivot_table(
            index="scenario",
            columns=["model_id", "game"],
            values="delta",
            aggfunc="first",
        ).round(3)
        lines.append(delta_pivot.to_markdown() + "\n\n")
    except Exception as e:
        lines.append(f"_(delta pivot failed: {e})_\n\n")

    # Hub-vs-leaf
    lines.append("## Hub minus leaf cooperation (within-star asymmetry)\n\n")
    try:
        hl_pivot = aggregated.pivot_table(
            index="scenario",
            columns=["model_id", "game"],
            values="hub_minus_leaf_coop_mean",
            aggfunc="first",
        ).round(3)
        lines.append(hl_pivot.to_markdown() + "\n\n")
    except Exception as e:
        lines.append(f"_(hub-leaf pivot failed: {e})_\n\n")

    # Hub exploitation
    lines.append("## Hub exploitation rate (PD cheap-talk only)\n\n")
    try:
        he_pivot = aggregated.pivot_table(
            index="scenario",
            columns=["model_id", "game"],
            values="hub_exploitation_rate_mean",
            aggfunc="first",
        ).round(3)
        lines.append(he_pivot.to_markdown() + "\n\n")
    except Exception as e:
        lines.append(f"_(hub-exploit pivot failed: {e})_\n\n")

    # Per-(model, scenario) summary with CIs
    lines.append("## Detailed coop_rate with 95% bootstrap CI\n\n")
    lines.append("| model | scenario | game | n | coop% (95% CI) |\n")
    lines.append("|---|---|---|---|---|\n")
    for _, r in aggregated.sort_values(["model_id", "game", "scenario"]).iterrows():
        m = r.get("coop_rate_overall_mean", np.nan)
        lo = r.get("coop_rate_overall_ci_lo", np.nan)
        hi = r.get("coop_rate_overall_ci_hi", np.nan)
        if np.isnan(m):
            continue
        lines.append(
            f"| {r['model_id']} | {r['scenario']} | {r['game']} | {int(r['n_runs'])} | "
            f"{m:.1%} [{lo:.1%}, {hi:.1%}] |\n"
        )

    with open(out_path, "w", encoding="utf-8") as f:
        f.writelines(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--roots", nargs="+", required=True,
                    help="Directories to scan recursively for *.json results.")
    ap.add_argument("--out-dir", default="cross_model_output")
    args = ap.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)

    print(f"Scanning {len(args.roots)} root(s)...")
    master = build_master_dataframe(args.roots)
    if master.empty:
        print("No cheap-talk-bench JSON results found. Check the --roots paths.")
        return

    print(f"\nModels: {sorted(master['model_id'].unique().tolist())}")
    print(f"Scenarios: {sorted(master['scenario'].unique().tolist())}")
    print(f"Games: {sorted(master['game'].unique().tolist())}")
    print(f"\nRuns per (model, scenario, game):")
    counts = master.groupby(["model_id", "scenario", "game"]).size().unstack(level=-1, fill_value=0)
    print(counts.to_string())

    master_path = os.path.join(args.out_dir, "cross_model_master.csv")
    master.to_csv(master_path, index=False)
    print(f"\n→ {master_path}")

    aggregated = aggregate(master)
    agg_path = os.path.join(args.out_dir, "cross_model_aggregated.csv")
    aggregated.to_csv(agg_path, index=False)
    print(f"→ {agg_path}")

    deltas = compute_deltas(master)
    delta_path = os.path.join(args.out_dir, "cross_model_delta.csv")
    deltas.to_csv(delta_path, index=False)
    print(f"→ {delta_path}")

    report_path = os.path.join(args.out_dir, "cross_model_report.md")
    write_markdown_report(report_path, master, aggregated, deltas)
    print(f"→ {report_path}")

    # Top-line summary
    print("\n=== HEADLINE: cheap-talk Δ per (model, game) ===")
    if not deltas.empty:
        baseline_ct = deltas[deltas["scenario"] == "baseline_cheap_talk"]
        for _, r in baseline_ct.sort_values(["model_id", "game"]).iterrows():
            print(f"  {r['model_id']:32s} {r['game']:3s}: "
                  f"no_comm={r['no_comm_mean']:.1%}  → cheap_talk={r['cheap_talk_mean']:.1%}  "
                  f"(Δ = {r['delta']:+.1%})")


if __name__ == "__main__":
    main()
