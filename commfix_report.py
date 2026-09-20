"""Did the corrected prompt change the ring cells? Tested, with a control.

The 2026-09 ablation re-runs four PD cycle cells with the routing sentence taken
from the topology instead of the hard-coded star one. Comparing the new mean to
the old one is not enough: five fresh runs of an unchanged cell also move,
because the seed does not fix sampling (see TRACK_RECORD, 2026-08-25).

The ablation therefore also re-runs the `no_comm` arm of `baseline`, which never
carried the wrong sentence and whose prompt is byte-identical to before. How far
THAT cell moves is what sampling alone does to this model in this session.

The verdict per cell is a two-sided Mann-Whitney over the runs; the control's
own drift is printed beside it, because a "significant" move smaller than the
drift of a cell that could not have changed is not evidence about the prompt.

    python cheaptalk_bench/commfix_report.py \\
        --old-roots <the ten grid folders> \\
        --new-roots rq4/commfix_cycle/*
"""
from __future__ import annotations

import argparse
import collections
import glob
import json
import os
import statistics

from scipy.stats import mannwhitneyu

from analysis import scenario_of, summarise_run
from cross_model_analysis import cell_label

CELLS = ["no_comm", "baseline_cheap_talk", "no_sense", "silence", "counterfactual"]


def collect(roots: list[str], game: str) -> dict:
    """(model, topology, cell) -> list of per-run cooperation rates."""
    out: dict[tuple[str, str, str], list[float]] = collections.defaultdict(list)
    for root in roots:
        for path in sorted(glob.glob(os.path.join(root, "**", "*.json"),
                                     recursive=True)):
            if os.path.basename(path).startswith("_"):
                continue
            with open(path, encoding="utf-8") as f:
                rec = json.load(f)
            if "history" not in rec or rec["config"]["game"] != game:
                continue
            cfg = rec["config"]
            # Deliberately without the filter/commfix tags: this script's whole
            # job is to line the two prompt generations up cell by cell.
            cell = cell_label(scenario_of(rec), cfg["condition"])
            model = cfg["model"]["model_id"].split("/")[-1]
            topo = rec["topology"].get("type", "star")
            out[(model, topo, cell)].append(summarise_run(rec)["coop_rate_overall"])
    return out


def mean(vals):
    return statistics.fmean(vals) if vals else float("nan")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--old-roots", nargs="+", required=True)
    ap.add_argument("--new-roots", nargs="+", required=True)
    ap.add_argument("--game", default="pd", choices=["pd", "sh"])
    args = ap.parse_args()

    old = collect(args.old_roots, args.game)
    new = collect(args.new_roots, args.game)
    if not new:
        raise SystemExit("No runs found under --new-roots; nothing to compare.")

    models = sorted({k[0] for k in new})
    print(f"game: {args.game}    models: {len(models)}\n")

    floors = {}
    for m in models:
        o, n = old.get((m, "cycle", "no_comm"), []), new.get((m, "cycle", "no_comm"), [])
        floors[m] = abs(mean(n) - mean(o)) if o and n else float("nan")

    print("NOISE FLOOR -- the arm whose prompt did not change (cycle, no_comm)")
    print(f"  {'model':24s} {'old':>6s} {'new':>6s} {'move':>7s}")
    for m in models:
        o, n = old.get((m, "cycle", "no_comm"), []), new.get((m, "cycle", "no_comm"), [])
        print(f"  {m:24s} {mean(o):6.3f} {mean(n):6.3f} {floors[m]:+7.3f}"
              f"   (n={len(o)} vs {len(n)})")

    print("\nTHE RE-RUN CELLS -- Mann-Whitney over runs, control drift beside it")
    header = (f"  {'model':24s} {'cell':22s} {'old':>6s} {'new':>6s} {'move':>7s} "
              f"{'floor':>6s} {'p':>6s}  verdict")
    print(header)
    verdicts = collections.Counter()
    for m in models:
        for cell in CELLS:
            if cell == "no_comm":
                continue
            o, n = old.get((m, "cycle", cell), []), new.get((m, "cycle", cell), [])
            if not n:
                continue
            move = mean(n) - mean(o)
            floor = floors[m]
            # The control is context, not a threshold. Using one n=5 cell as a
            # cutoff punished the models whose control happened to be stable:
            # gemma-2-9b drew a floor of 0.003, which called a move of -0.016
            # a change. The verdict is a two-sided Mann-Whitney at the run
            # level; the floor is printed beside it so a "significant" move
            # smaller than the control's own drift is visible for what it is.
            p = (mannwhitneyu(o, n, alternative="two-sided").pvalue
                 if len(set(o)) + len(set(n)) > 2 else float("nan"))
            if p != p:
                verdict = "identical"
            elif p < 0.05 and abs(move) > floor:
                verdict = "MOVED"
            elif p < 0.05:
                verdict = "p<0.05 but under the control's own drift"
            else:
                verdict = "no change"
            verdicts[verdict] += 1
            print(f"  {m:24s} {cell:22s} {mean(o):6.3f} {mean(n):6.3f} "
                  f"{move:+7.3f} {floor:6.3f} {p:6.3f}  {verdict}")
    print("  " + ", ".join(f"{v}: {c}" for v, c in verdicts.most_common()))

    print("\nRQ2 -- ring minus star, before and after")
    print(f"  {'model':24s} {'cell':22s} {'old d':>7s} {'new d':>7s}")
    by_model_old, by_model_new = collections.defaultdict(list), collections.defaultdict(list)
    for m in models:
        for cell in CELLS:
            star = old.get((m, "star", cell), [])
            o, n = old.get((m, "cycle", cell), []), new.get((m, "cycle", cell), [])
            if not star or not o:
                continue
            d_old = mean(o) - mean(star)
            by_model_old[m].append(d_old)
            if n:
                d_new = mean(n) - mean(star)
                by_model_new[m].append(d_new)
                print(f"  {m:24s} {cell:22s} {d_old:+7.3f} {d_new:+7.3f}")
            else:
                print(f"  {m:24s} {cell:22s} {d_old:+7.3f} {'--':>7s}  (not re-run)")

    print("\n  sign test unit = the model (cells within a model are not independent)")
    for label, data in (("old prompt", by_model_old), ("new prompt", by_model_new)):
        if not data:
            continue
        means = {m: mean(v) for m, v in data.items()}
        pos = sum(v > 0 for v in means.values())
        neg = sum(v < 0 for v in means.values())
        detail = ", ".join(f"{m.split('-')[0]}:{v:+.3f}" for m, v in sorted(means.items()))
        print(f"    {label:11s} {pos}+ / {neg}-   ({detail})")

    print("\nRead it as: a cell only counts as changed by the prompt if 'move' "
          "exceeds its model's floor.\nIf every cell is within noise, the "
          "reported RQ2 tendency stands as measured.")


if __name__ == "__main__":
    main()
