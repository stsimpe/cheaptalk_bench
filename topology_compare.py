"""Star vs ring vs clique, per research question, PD.

Reads run folders directly (no CSV), so it is independent of the cell tagging
the cross-model pipeline applies to corrected-prompt runs.

Which ring: `--ring` picks the runs the comparison uses. `commfix` (default)
takes the September ablation runs, whose cheap-talk prompt describes the ring
and so matches the clique's; `grid` takes the original ring, whose cheap-talk
prompt described a star. The ablation covers only session A, so the framing
cells always come from the grid ring and are marked accordingly.

Usage:
    python topology_compare.py --star <star folders> --ring <ring folders>
        --ring-fix <ablation folders> --clique <clique folders>
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import statistics as st
from collections import defaultdict

from scipy.stats import binomtest, fisher_exact

from analysis import scenario_of, summarise_run
from cross_model_analysis import normalise_model_id

LOW = ["no_comm", "silence", "no_sense"]
FRAMES = ["competitive", "team", "business"]
MEANINGFUL = ["baseline_cheap_talk", "framing_business", "framing_team",
              "framing_business_context[cheap_talk]", "framing_team_context[cheap_talk]"]
DEGRADED = ["no_sense", "silence", "counterfactual"]
ADV_MSG = ["framing_competitive"]
ADV_PROMPT = ["framing_competitive_context[cheap_talk]"]
KIND = ({c: "meaningful" for c in MEANINGFUL} | {c: "degraded" for c in DEGRADED}
        | {c: "adversarial (messages)" for c in ADV_MSG}
        | {c: "adversarial (prompt)" for c in ADV_PROMPT})
BAND = 0.05
LAST = 5


def cell_of(rec: dict) -> str:
    """Scenario label, with the two arms of a context framing kept apart."""
    sc = scenario_of(rec)
    if sc.endswith("_context"):
        return f"{sc}[{rec['config']['condition']}]"
    return sc


def load(roots: list[str], game: str) -> dict:
    """{(model, cell): [run summaries]} over the given folders."""
    out = defaultdict(list)
    for root in roots:
        for p in glob.glob(f"{root}/**/*.json", recursive=True):
            if os.path.basename(p).startswith("_") or f"{os.sep}zips{os.sep}" in p:
                continue
            with open(p, encoding="utf-8") as f:
                rec = json.load(f)
            if "config" not in rec or rec["config"]["game"] != game:
                continue
            model = normalise_model_id(rec["config"]["model"]["model_id"])
            s = summarise_run(rec)
            acts = [a for x in rec["history"][-LAST:] for a in x["actions"].values()]
            valid = [a for a in acts if a in ("Cooperate", "Defect", "Stag", "Hare")]
            end = (sum(a in ("Cooperate", "Stag") for a in valid) / len(valid)) if valid else None
            out[(model, cell_of(rec))].append({"coop": s["coop_rate_overall"], "end": end})
    return out


def mean(data, model, cell, key="coop"):
    v = [r[key] for r in data.get((model, cell), []) if r[key] is not None]
    return st.fmean(v) if v else float("nan")


def share(data, model, cell):
    v = [r["end"] for r in data.get((model, cell), []) if r["end"] is not None]
    return (sum(x >= 0.5 for x in v), len(v)) if v else (0, 0)


def sign_test(diffs):
    pos, neg = sum(d > 0 for d in diffs), sum(d < 0 for d in diffs)
    p = binomtest(pos, pos + neg, 0.5).pvalue if pos + neg else float("nan")
    return pos, neg, len(diffs) - pos - neg, p


def rq1(topos, models):
    print("\n" + "=" * 78)
    print("RQ1 -- helpful or harmful, each cell against its OWN anchor (PD)")
    print("=" * 78)
    print(f"{'topology':10s} {'what flows':24s} {'cells':>6s} {'harmful':>8s} {'mean d':>8s}")
    for name, data in topos.items():
        for kind in ["meaningful", "degraded", "adversarial (prompt)", "adversarial (messages)"]:
            deltas = []
            for m in models:
                anchor = mean(data, m, "no_comm")
                if anchor != anchor:
                    continue
                for cell, k in KIND.items():
                    if k != kind:
                        continue
                    v = mean(data, m, cell)
                    if v == v:
                        deltas.append(v - anchor)
            if deltas:
                print(f"{name:10s} {kind:24s} {len(deltas):6d} "
                      f"{sum(d < -BAND for d in deltas):8d} {st.fmean(deltas):+8.2f}")


def rq2(topos, models):
    print("\n" + "=" * 78)
    print("RQ2 -- topology, low-communication PD cells")
    print("=" * 78)
    names = list(topos)
    print(f"{'model':22s} {'cell':10s}" + "".join(f"{n:>12s}" for n in names) + "   monotone?")
    mono = 0
    total = 0
    for m in models:
        for cell in LOW:
            vals = [mean(topos[n], m, cell) for n in names]
            ok = all(a <= b for a, b in zip(vals, vals[1:]))
            mono += ok
            total += 1
            print(f"{m:22s} {cell:10s}" + "".join(f"{v:12.3f}" for v in vals)
                  + f"   {'yes' if ok else 'no'}")
    print(f"\nmonotone {names[0]} <= ... <= {names[-1]}: {mono}/{total} cells")

    lowest = defaultdict(int)
    for m in models:
        for cell in LOW:
            vals = {n: mean(topos[n], m, cell) for n in names}
            lowest[min(vals, key=lambda n: vals[n])] += 1
    print("lowest cooperation, count of cells: "
          + ", ".join(f"{n} {c}" for n, c in lowest.items()))

    print("\npairwise, per model x cell: difference in the mean, and the share of runs")
    print("ending cooperative (Fisher, two-sided)")
    for a, b in [(names[0], names[-1]), (names[1], names[-1]), (names[0], names[1])]:
        diffs, ps = [], []
        for m in models:
            for cell in LOW:
                va, vb = mean(topos[a], m, cell), mean(topos[b], m, cell)
                if va != va or vb != vb:
                    continue
                diffs.append(vb - va)
                ka, na = share(topos[a], m, cell)
                kb, nb = share(topos[b], m, cell)
                if na and nb:
                    ps.append(fisher_exact([[ka, na - ka], [kb, nb - kb]])[1])
        pos, neg, tie, p = sign_test(diffs)
        print(f"  {b} minus {a}: {pos} higher, {neg} lower, sign test p={p:.3f}"
              f" | Fisher p<0.05 in {sum(x < 0.05 for x in ps)}/{len(ps)} cells")


def rq3(topos, models):
    print("\n" + "=" * 78)
    print("RQ3 -- where the frame lives (PD): prompt-closed, prompt-open, in the messages")
    print("=" * 78)
    for name, data in topos.items():
        rows, raises, inrange, overrides = 0, 0, 0, 0
        detail = []
        for m in models:
            for f in FRAMES:
                closed = mean(data, m, f"framing_{f}_context[no_comm]")
                openv = mean(data, m, f"framing_{f}_context[cheap_talk]")
                msg = mean(data, m, f"framing_{f}")
                if closed != closed or openv != openv:
                    continue
                rows += 1
                raises += openv > closed + 1e-9
                inrange += 0.79 <= openv <= 1.0
                if msg == msg:
                    overrides += openv - msg > 0
                detail.append((m, f, closed, openv, msg))
        if not rows:
            continue
        print(f"\n{name}: {rows} model x frame combinations")
        print(f"  open channel raises the prompt frame : {raises}/{rows}")
        print(f"  open channel lands in 0.79-1.00      : {inrange}/{rows}")
        print(f"  prompt-open above message placement  : {overrides}/{rows}")
        for m, f, c, o, g in detail:
            flag = "" if (o > c - 1e-9 and 0.79 <= o <= 1.0) else "   <-"
            print(f"    {m:22s} {f:12s} closed {c:5.2f}  open {o:5.2f}  msg {g:5.2f}{flag}")


def rq4(topos, models):
    print("\n" + "=" * 78)
    print("RQ4 -- rewiring as a lever: does any topology defuse an adversarial frame?")
    print("=" * 78)
    names = list(topos)
    print(f"{'model':22s} {'cell':34s}" + "".join(f"{n:>12s}" for n in names))
    for cell in ["framing_competitive", "framing_competitive_context[cheap_talk]"]:
        for m in models:
            vals = [mean(topos[n], m, cell) for n in names]
            print(f"{m:22s} {cell:34s}" + "".join(f"{v:12.3f}" for v in vals))
    print("\n(the comparison cell is baseline_cheap_talk, which every topology "
          "takes to the ceiling)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--star", nargs="+", required=True)
    ap.add_argument("--ring", nargs="+", required=True)
    ap.add_argument("--ring-fix", nargs="+", default=None)
    ap.add_argument("--clique", nargs="+", required=True)
    ap.add_argument("--game", default="pd")
    args = ap.parse_args()

    star, ring, clique = (load(args.star, args.game), load(args.ring, args.game),
                          load(args.clique, args.game))
    topos = {"star": star, "ring": ring, "clique": clique}
    if args.ring_fix:
        fix = load(args.ring_fix, args.game)
        # Session A only: fall back to the grid ring for every other cell.
        merged = defaultdict(list, {k: v for k, v in ring.items()})
        merged.update({k: v for k, v in fix.items()})
        topos["ring"] = merged
        print("[note] ring = ablation runs for session A cells, grid ring for the "
              "framing cells (the ablation did not cover them)")
    models = sorted({m for d in topos.values() for (m, _) in d})
    print(f"models: {len(models)}   topologies: {list(topos)}   game: {args.game.upper()}")
    rq1(topos, models)
    rq2(topos, models)
    rq3(topos, models)
    rq4(topos, models)


if __name__ == "__main__":
    main()
