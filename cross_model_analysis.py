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
        try:
            summary = summarise_run(data)
        except Exception as e:
            n_skipped += 1
            continue
        # Scenario and topology come from analysis.summarise_run, which calls
        # analysis.scenario_of. The local derive_scenario() below is kept only
        # for reference: it inspects message_policy and IGNORES context_framing,
        # so every framing_*_context run would be filed under no_comm /
        # baseline_cheap_talk -- contaminating the cells every delta is measured
        # against. Never reintroduce it.
        rows.append({
            "path": path,
            "model_id": normalise_model_id(model_id_raw),
            "model_id_raw": model_id_raw,
            "game": summary["game"],
            "topology": summary["topology"],
            "condition": summary["condition"],
            "scenario": summary["scenario"],
            "cell": cell_label(summary["scenario"], summary["condition"],
                               cfg.get("message_filter", "none"),
                               bool(cfg.get("topology_aware_comm_prompt", False))),
            "framing_type": cfg.get("framing_type", ""),
            # In the master table too, so a mixed cell is visible after the
            # fact instead of only at grouping time.
            "message_filter": cfg.get("message_filter", "none"),
            "comm_prompt": ("topology" if cfg.get("topology_aware_comm_prompt")
                            else "legacy_star"),
            "n_rounds": summary["n_rounds"],
            "n_runs_config": cfg.get("n_runs", -1),
            "run_id": summary["run_id"],
            **{m: summary.get(m, np.nan) for m in METRIC_COLS},
        })
    print(f"  discovered {n_total} json files, kept {len(rows)} runs ({n_skipped} skipped)")
    return pd.DataFrame(rows)


def cell_label(scenario: str, condition: str,
               message_filter: str = "none", comm_fix: bool = False) -> str:
    """Unique label for one experimental cell.

    A cell is an experimental condition, so anything that changes the
    condition has to be in the label. Two knobs used to be invisible here,
    and both are silent failures rather than errors: a filtered run and its
    unfiltered twin both record `scenario="framing_competitive"`, and a run
    with the corrected communication prompt records the same scenario as the
    run with the star sentence. Passing both trees to `--roots` averaged
    them into one cell -- 15 runs of Qwen2.5 `framing_competitive` came out
    as 0.23, a value none of the three arms has. Separate directories are
    not protection: they only hold as long as nobody types a parent path.

    The three `framing_*_context` scenarios were run under BOTH conditions:
    the frame in the system prompt with the channel closed (`no_comm`), and
    the same frame with messages on (`cheap_talk`). Those are two different
    experiments -- the whole two-channel result is the contrast between them
    -- so they must never be averaged into one cell. Grouping on `scenario`
    alone silently did exactly that. Every other scenario has exactly one
    condition, so its label is just the scenario name.

    Both knobs are tagged only on the OPEN arm, because neither can reach a
    closed one: a `no_comm` run has no message phase, so the filter never
    runs, and build_system_prompt ignores `communication_text` for that
    condition -- the two prompts come out byte-identical. Tagging it anyway
    split one experiment into `no_comm` and `no_comm+commfix`: the first bug
    mirrored, a silent split instead of a silent merge, and it fragmented the
    anchor that every delta below is measured against.
    """
    label = f"{scenario}[{condition}]" if scenario.endswith("_context") else scenario
    if condition != "cheap_talk":
        return label
    tags = []
    if message_filter and message_filter != "none":
        tags.append(message_filter.split("_")[0])   # F3_relative_gain -> F3
    if comm_fix:
        tags.append("commfix")
    return f"{label}+{'+'.join(tags)}" if tags else label


def base_cell(cell: str) -> str:
    """The cell without its variant tags: `silence+commfix` -> `silence`.

    Use this wherever a list of cell names asks "which scenario family is
    this?", never where it asks "which experimental condition is this?".
    Tagging the label (2026-09-20) stopped filtered and corrected-prompt runs
    from merging into their untagged twins, but it also broke every membership
    test written as `cell in SOME_SET`: `no_sense+commfix` is not in
    {"no_sense", "silence"}, so 24 canned messages leaked into the judge's
    input before this helper existed.
    """
    return cell.split("+", 1)[0]


def aggregate(master: pd.DataFrame) -> pd.DataFrame:
    rows = []
    grouped = master.groupby(["model_id", "topology", "cell", "game"])
    for (model, topology, cell, game), sub in grouped:
        row = {
            "model_id": model,
            "topology": topology,
            "cell": cell,
            "scenario": sub["scenario"].iloc[0],
            "condition": sub["condition"].iloc[0],
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
    """Open-arm Δ vs the no_comm anchor, per (model, topology, game, cell).

    The anchor is selected on `cell`, the same key aggregate() groups on.
    It used to be selected on `scenario`, which was the same set of rows
    until the filter/commfix tags existed and then stopped being: the guard
    below skips the string "no_comm" while the anchor matched anything whose
    scenario was no_comm, tagged or not.

    When a run generation brought its own no_comm arm, that arm is the
    anchor. The corrected-prompt ablation re-ran `baseline`, so its closed
    arm is a fresh measurement of an unchanged prompt -- which is exactly
    what commfix_report.py calls the noise floor, and the reason it exists:
    the same cell measured 26 days apart moved 0.109 -> 0.241. Anchoring a
    commfix cell on the old session's no_comm would fold that drift into
    every delta. Generations that ran no closed arm at all -- the F1/F3
    filter cells are framing_competitive only -- fall back to the pooled
    anchor, and `anchor_comm_prompt` records which of the two was used.
    """
    rows = []
    has_gen = "comm_prompt" in master.columns
    for (model, topology, game), sub in master.groupby(["model_id", "topology", "game"]):
        anchor_pool = sub[sub["cell"] == "no_comm"]
        if anchor_pool["coop_rate_overall"].dropna().empty:
            continue
        for cell, sc_sub in sub.groupby("cell"):
            if cell == "no_comm":
                continue
            ct_vals = sc_sub["coop_rate_overall"].dropna().values
            if len(ct_vals) == 0:
                continue
            anchor, anchor_gen = anchor_pool, "pooled"
            if has_gen:
                gen = sc_sub["comm_prompt"].iloc[0]
                same = anchor_pool[anchor_pool["comm_prompt"] == gen]
                if not same["coop_rate_overall"].dropna().empty:
                    anchor, anchor_gen = same, gen
            no_comm = anchor["coop_rate_overall"].dropna().values
            nc_mean, nc_lo, nc_hi = bootstrap_ci(no_comm)
            ct_mean, ct_lo, ct_hi = bootstrap_ci(ct_vals)
            rows.append({
                "model_id": model,
                "topology": topology,
                "game": game,
                "cell": cell,
                "scenario": sc_sub["scenario"].iloc[0],
                "condition": sc_sub["condition"].iloc[0],
                "no_comm_mean": nc_mean,
                "no_comm_ci_lo": nc_lo,
                "no_comm_ci_hi": nc_hi,
                # "open arm", not "cheap talk": for a framing_*_context[no_comm]
                # row this holds the CLOSED-channel arm measured against the
                # same anchor. The delta was always right; the name was not.
                "open_arm_mean": ct_mean,
                "open_arm_ci_lo": ct_lo,
                "open_arm_ci_hi": ct_hi,
                "delta": ct_mean - nc_mean,
                "anchor_comm_prompt": anchor_gen,
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
            index="cell",
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
            index="cell",
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
            index="cell",
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
            index="cell",
            columns=["model_id", "game"],
            values="hub_exploitation_rate_mean",
            aggfunc="first",
        ).round(3)
        lines.append(he_pivot.to_markdown() + "\n\n")
    except Exception as e:
        lines.append(f"_(hub-exploit pivot failed: {e})_\n\n")

    # Per-(model, scenario) summary with CIs
    lines.append("## Detailed coop_rate with 95% bootstrap CI\n\n")
    lines.append("| model | topology | scenario | game | n | coop% (95% CI) |\n")
    lines.append("|---|---|---|---|---|---|\n")
    for _, r in aggregated.sort_values(["model_id", "topology", "game", "scenario"]).iterrows():
        m = r.get("coop_rate_overall_mean", np.nan)
        lo = r.get("coop_rate_overall_ci_lo", np.nan)
        hi = r.get("coop_rate_overall_ci_hi", np.nan)
        if np.isnan(m):
            continue
        lines.append(
            f"| {r['model_id']} | {r['topology']} | {r['scenario']} | {r['game']} | {int(r['n_runs'])} | "
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
    counts = master.groupby(["model_id", "topology", "cell", "game"]).size().unstack(level=-1, fill_value=0)
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
        for _, r in baseline_ct.sort_values(
                ["model_id", "topology", "game"]).iterrows():
            print(f"  {r['model_id']:24s} {r['topology']:6s} {r['game']:3s}: "
                  f"no_comm={r['no_comm_mean']:.1%}  → open arm={r['open_arm_mean']:.1%}  "
                  f"(Δ = {r['delta']:+.1%})")


if __name__ == "__main__":
    main()
