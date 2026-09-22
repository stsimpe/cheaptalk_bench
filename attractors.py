"""Attractor analysis: which state does each run end in, and do conditions differ?

Many cells are bimodal -- each run ends near full cooperation or near full
defection -- so a cell mean is a mixture of two states and its bootstrap CI
over n=5 runs is too narrow to mean much. This reads each run by the state it
ends in and compares conditions by the SHARE of runs in the cooperative state.

Definitions, fixed before looking at the comparisons:
  end state   cooperation over the last 5 rounds (valid decisions only);
              "cooperative" if >= 0.5, else "defecting"
  test        two-sided Fisher exact test on the 2x2 of (condition x state)
  families    each family is Holm-corrected on its own:
    RQ1   baseline cheap talk vs its no_comm anchor, per model x topology
    RQ2   star vs ring, per model, in the three low-communication PD cells
          (no_comm, silence, no_sense) -- where topology can show at all

Usage:
    python attractors.py --roots <the ten run folders> [--game pd]
"""
from __future__ import annotations

import argparse
import os

import pandas as pd
from scipy.stats import binomtest, fisher_exact

from analysis import scenario_of
from cross_model_analysis import discover_records, normalise_model_id

LAST = 5
THRESHOLD = 0.5


def end_state(record: dict) -> float | None:
    valid = {"Cooperate", "Stag", "Defect", "Hare"}
    good = {"Cooperate", "Stag"}
    acts = [a for x in record["history"][-LAST:] for a in x["actions"].values() if a in valid]
    if not acts:
        return None
    return sum(a in good for a in acts) / len(acts)


def holm(pvals: list[float]) -> list[float]:
    order = sorted(range(len(pvals)), key=lambda i: pvals[i])
    adj = [0.0] * len(pvals)
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (len(pvals) - rank) * pvals[i]))
        adj[i] = running
    return adj


def load(roots: list[str], game: str) -> pd.DataFrame:
    rows = []
    for path, rec in discover_records(roots):
        cfg = rec["config"]
        if cfg["game"] != game:
            continue
        s = end_state(rec)
        if s is None:
            continue
        rows.append({
            "model_id": normalise_model_id(cfg["model"]["model_id"]),
            "topology": rec["topology"].get("type", "star"),
            "cell": scenario_of(rec),
            "end_coop": s,
            "cooperative": s >= THRESHOLD,
        })
    return pd.DataFrame(rows)


def fisher(a: pd.Series, b: pd.Series) -> tuple[float, int, int, int, int]:
    ka, na, kb, nb = int(a.sum()), len(a), int(b.sum()), len(b)
    _, p = fisher_exact([[ka, na - ka], [kb, nb - kb]])
    return p, ka, na, kb, nb


def family(tests: list[dict], title: str) -> pd.DataFrame:
    d = pd.DataFrame(tests)
    if d.empty:
        return d
    d["p_holm"] = holm(d["p"].tolist())
    print(f"\n=== {title} -- {len(d)} tests, Holm-corrected ===")
    for _, r in d.iterrows():
        flag = "  *" if r["p_holm"] < 0.05 else ""
        print(f"  {r['model_id']:22s} {r['label']:34s} {r['a']:>5s} vs {r['b']:<5s}"
              f" p={r['p']:.3f}  p_holm={r['p_holm']:.3f}{flag}")
    print(f"  significant after Holm: {int((d['p_holm'] < 0.05).sum())}/{len(d)}")
    frac = lambda x: int(x.split("/")[0]) / int(x.split("/")[1])
    diff = [frac(a) - frac(b) for a, b in zip(d["a"], d["b"])]
    pos, neg = sum(x > 0 for x in diff), sum(x < 0 for x in diff)
    p = binomtest(pos, pos + neg, 0.5).pvalue if pos + neg else float("nan")
    print(f"  sign test across strata: {pos} first > second, {neg} second > first, "
          f"{len(diff) - pos - neg} tied -> p={p:.4f} (two-sided)")
    return d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--roots", nargs="+", required=True)
    ap.add_argument("--game", default="pd")
    ap.add_argument("--out-dir", default="cross_model_output_final")
    args = ap.parse_args()

    runs = load(args.roots, args.game)
    share = (runs.groupby(["model_id", "topology", "cell"])["cooperative"]
             .agg(cooperative_runs="sum", runs="size").reset_index())
    share["share"] = share["cooperative_runs"] / share["runs"]
    mixed = runs[(runs["end_coop"] > 0.2) & (runs["end_coop"] < 0.8)]
    print(f"{len(runs)} runs; {len(mixed)} ({len(mixed)/len(runs):.0%}) end between "
          f"0.2 and 0.8, the rest in one of the two states")

    tests = []
    for (model, topo), sub in runs.groupby(["model_id", "topology"]):
        a = sub[sub["cell"] == "baseline_cheap_talk"]["cooperative"]
        b = sub[sub["cell"] == "no_comm"]["cooperative"]
        if len(a) and len(b):
            p, ka, na, kb, nb = fisher(a, b)
            tests.append({"model_id": model, "label": f"{topo}: cheap talk vs no_comm",
                          "a": f"{ka}/{na}", "b": f"{kb}/{nb}", "p": p})
    rq1 = family(tests, "RQ1 -- cooperative end state, cheap talk vs anchor")

    tests = []
    for model, sub in runs.groupby("model_id"):
        for cell in ["no_comm", "silence", "no_sense"]:
            a = sub[(sub["cell"] == cell) & (sub["topology"] == "star")]["cooperative"]
            b = sub[(sub["cell"] == cell) & (sub["topology"] == "cycle")]["cooperative"]
            if len(a) and len(b):
                p, ka, na, kb, nb = fisher(a, b)
                tests.append({"model_id": model, "label": f"{cell}: star vs ring",
                              "a": f"{ka}/{na}", "b": f"{kb}/{nb}", "p": p})
    rq2 = family(tests, "RQ2 -- cooperative end state, star vs ring")

    os.makedirs(args.out_dir, exist_ok=True)
    share.to_csv(os.path.join(args.out_dir, "attractor_share.csv"), index=False)
    pd.concat([rq1.assign(family="RQ1"), rq2.assign(family="RQ2")]).to_csv(
        os.path.join(args.out_dir, "attractor_tests.csv"), index=False)
    print(f"\n-> {args.out_dir}/attractor_share.csv, attractor_tests.csv")


if __name__ == "__main__":
    main()
