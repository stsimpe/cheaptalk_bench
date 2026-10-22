"""Silent topology: does the star's deficit survive when nobody is told the network?

Reads the silent runs of docs/silent_topology_plan.md (star and ring, PD, the
three low-communication cells no_comm, silence and no_sense, five models) and
applies the plan's rule to the 15 model-cell pairs:

  k = cells where the ring cooperates more than the star, m = the reverse
  (ties dropped from the sign test)
  survives      k >= 12 and two-sided sign test p < 0.05
  vanishes      k <= 9
  inconclusive  otherwise

Also reports end states (last five rounds >= 0.5) by Fisher exact test, and,
when --announced-roots is given, the announced runs side by side
(descriptive: they were measured in another period).

Usage:
    python silent_topology_report.py --roots <silent trees> [--announced-roots <trees>]
"""
from __future__ import annotations

import argparse
import os
import sys

import pandas as pd
from scipy.stats import binomtest, fisher_exact

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analysis import summarise_run  # noqa: E402
from cross_model_analysis import discover_records, normalise_model_id  # noqa: E402

CELLS = {"no_comm": "no_comm", "silence": "silence", "no_sense": "no_sense"}
N_PAIRS = 15   # five models x three cells


def end_coop(d: dict) -> bool:
    last = d["history"][-5:]
    acts = [a for r in last for a in r["actions"].values() if a in ("Cooperate", "Defect")]
    return bool(acts) and sum(a == "Cooperate" for a in acts) / len(acts) >= 0.5


def collect(roots: list[str], silent: bool) -> pd.DataFrame:
    rows = []
    for path, d in discover_records(roots):
        cfg = d["config"]
        if cfg.get("game") != "pd" or bool(cfg.get("silent_topology", False)) != silent:
            continue
        if cfg.get("source_agent") is not None or cfg.get("n_agents", 4) != 4:
            continue
        s = summarise_run(d)
        cell = "no_comm" if s["condition"] == "no_comm" else s["scenario"]
        if cell not in CELLS or s["condition"] == "no_comm" and s["scenario"] not in ("no_comm", "baseline"):
            continue
        topo = s["topology"]
        if topo not in ("star", "cycle"):
            continue
        rows.append({"model": normalise_model_id(cfg["model"]["model_id"]), "topology": topo,
                     "cell": cell, "coop": s["coop_rate_overall"], "end": end_coop(d)})
    return pd.DataFrame(rows)


def rule(df: pd.DataFrame) -> dict | None:
    """None when one of the two networks has no runs yet (the rule needs both)."""
    means = df.groupby(["model", "cell", "topology"])["coop"].mean().unstack("topology")
    if not {"star", "cycle"} <= set(means.columns):
        return None
    means = means.dropna(subset=["star", "cycle"])
    diff = means["cycle"] - means["star"]
    k, m = int((diff > 0).sum()), int((diff < 0).sum())
    p = binomtest(k, k + m, 0.5).pvalue if k + m else 1.0
    if len(diff) < N_PAIRS:
        # The thresholds are counts out of 15: a missing model or cell would
        # make "vanishes" (k <= 9) easier to reach.
        verdict = f"not read: {len(diff)} of {N_PAIRS} model-cell pairs"
    elif k >= 12 and p < 0.05:
        verdict = "the star's deficit survives silence"
    elif k <= 9:
        verdict = "the star's deficit vanishes under silence"
    else:
        verdict = "inconclusive"
    ends = df.groupby("topology")["end"].agg(["sum", "size"])
    fisher = (fisher_exact([[ends.loc["cycle", "sum"], ends.loc["cycle", "size"] - ends.loc["cycle", "sum"]],
                            [ends.loc["star", "sum"], ends.loc["star", "size"] - ends.loc["star", "sum"]]])[1]
              if {"star", "cycle"} <= set(ends.index) else float("nan"))
    return {"means": means, "k": k, "m": m, "n_pairs": len(diff), "p": p,
            "verdict": verdict, "ends": ends, "fisher_end": fisher}


def show(label: str, r: dict):
    print(f"\n=== {label} ===")
    print(r["means"].round(2).rename(columns={"cycle": "ring"}).to_string())
    print(f"\nring above star in {r['k']} of {r['n_pairs']} cells, below in {r['m']}"
          f" (sign test p = {r['p']:.3f})")
    e = r["ends"]
    for t in ("star", "cycle"):
        if t in e.index:
            print(f"  cooperative end state, {'ring' if t == 'cycle' else t}: "
                  f"{int(e.loc[t, 'sum'])}/{int(e.loc[t, 'size'])}")
    print(f"  Fisher, end states ring against star: p = {r['fisher_end']:.3f}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--roots", nargs="+", required=True, help="Trees of the silent runs.")
    ap.add_argument("--announced-roots", nargs="+", default=None,
                    help="Announced star and ring trees, for a side-by-side view.")
    args = ap.parse_args()
    silent = collect(args.roots, silent=True)
    if silent.empty:
        raise SystemExit("No silent PD runs under --roots.")
    r = rule(silent)
    if r is None:
        # One network only (the first of the two Kaggle sessions): show what
        # there is; the rule is read once both networks are in.
        only = silent["topology"].iloc[0]
        print(f"\n=== Silent prompt, {'ring' if only == 'cycle' else only} only ===")
        g = silent.groupby(["model", "cell"])
        print(pd.DataFrame({"coop": g["coop"].mean(), "runs": g.size(),
                            "coop_end": g["end"].mean()}).round(2).to_string())
        print("\n-> rule: not read yet, it needs both networks")
        return
    show("Silent prompt", r)
    print(f"\n-> rule: {r['verdict']}")
    if args.announced_roots:
        ann = collect(args.announced_roots, silent=False)
        if not ann.empty and (a := rule(ann)) is not None:
            show("Announced prompt (another period: descriptive only)", a)


if __name__ == "__main__":
    main()
