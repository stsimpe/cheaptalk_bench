"""The Stag Hunt on the clique, read by the rules fixed before it ran.

`kaggle_clique_sh.ipynb` ran the fourteen cells of the clique in the Stag Hunt
(350 runs, 2026-10-07/08). Its reading rules were written into the notebook
on 2026-10-07, before any run, and this script applies exactly those:

  1  Ledger replication, on the clique alone. Delta = cell minus the clique's
     no_comm anchor of the same model, band +-0.05, categories as in
     harm_ledger.py. It holds if (a) adversarial content in the messages is
     the most negative category, (b) meaningful content stays within the
     band, and (c) at least 2/3 of the harmful cells are in the two Gemma
     models -- computed with every cell and again without the cells above
     15% invalid, and claimed only if both agree.
  2  Topology, over the 15 low-communication cells (no_comm, silence,
     no_sense x 5 models): a sign test of the clique against the ring and
     against the star. An effect is declared only if both give at least 12 of
     15 cells in one direction, ties counting against.
  3  Cells above 15% invalid are reported with a reservation.

Star and ring get the same ledger quantities for comparison, and the totals
over the three topologies are the ones the thesis quotes.

    python clique_sh_report.py --root .

`--root` is the project root; the run folders are found in either layout
(`star_runs/<model>_star` or `<model>_star`). Stag Hunt runs only.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import statistics as st
from math import comb

from analysis import model_dir, scenario_of, summarise_run
from harm_ledger import BAND, KIND

MODELS = ["Llama-3.1-8B-Instruct", "Qwen2.5-7B-Instruct", "Qwen3-4B",
          "gemma-2-2b-it", "gemma-2-9b-it"]
GEMMA = {"gemma-2-2b-it", "gemma-2-9b-it"}
TOPOLOGIES = {"star": "star", "ring": "cycle", "clique": "clique"}
KINDS = ["meaningful", "degraded", "adversarial (prompt)", "adversarial (messages)"]
LOW = ["no_comm", "silence", "no_sense"]
INVALID_CUT = 0.15


def cell_label(rec: dict) -> str:
    """scenario_of, with the arm of a context framing appended, as the ledger uses."""
    cell = scenario_of(rec)
    if cell.endswith("_context"):
        cell += f"[{rec['config']['condition']}]"
    return cell


def load(root: str, topology: str, model: str) -> dict:
    """cell -> (mean of run cooperation, mean of run invalid rate, runs), Stag Hunt."""
    folder = model_dir(root, model, topology)
    if not os.path.isdir(folder):
        raise SystemExit(f"no run folder {folder} -- pass the project root as --root")
    runs: dict = {}
    for p in glob.glob(os.path.join(folder, "**", "*_sh_*.json"), recursive=True):
        with open(p, encoding="utf-8") as f:
            rec = json.load(f)
        if rec["config"]["game"] != "sh":
            raise SystemExit(f"{p} is named _sh_ but records game {rec['config']['game']!r}")
        s = summarise_run(rec)
        runs.setdefault(cell_label(rec), []).append((s["coop_rate_overall"], s["invalid_rate"]))
    return {c: (st.fmean(v[0] for v in vals), st.fmean(v[1] for v in vals), len(vals))
            for c, vals in runs.items()}


def ledger(data: dict, drop_invalid: bool = False) -> list[tuple]:
    """(model, cell, kind, delta) for every open-channel cell of one topology."""
    rows = []
    for m in MODELS:
        cells = data[m]
        anchor, anchor_invalid, _ = cells["no_comm"]
        if drop_invalid and anchor_invalid > INVALID_CUT:
            continue
        for c, kind in KIND.items():
            if c not in cells:
                continue
            value, invalid, _ = cells[c]
            if drop_invalid and invalid > INVALID_CUT:
                continue
            rows.append((m, c, kind, value - anchor))
    return rows


def report_ledger(rows: list[tuple], title: str) -> bool:
    harmful = [r for r in rows if r[3] < -BAND]
    helpful = sum(r[3] > BAND for r in rows)
    print(f"\n{title}: {len(rows)} cells -- helpful {helpful}, "
          f"neutral {len(rows) - helpful - len(harmful)}, harmful {len(harmful)}")
    means = {}
    for kind in KINDS:
        k = [r for r in rows if r[2] == kind]
        if k:
            means[kind] = st.fmean(r[3] for r in k)
            print(f"   {kind:24s} mean delta {means[kind]:+.3f}   "
                  f"harmful {sum(r[3] < -BAND for r in k)}/{len(k)}")
    gemma = sum(r[0] in GEMMA for r in harmful)
    print(f"   harmful cells in the two Gemma models: {gemma}/{len(harmful)}")
    a = min(means, key=means.get) == "adversarial (messages)"
    b = abs(means["meaningful"]) <= BAND
    c = bool(harmful) and gemma / len(harmful) >= 2 / 3
    print(f"   (a) messages most negative: {a}   (b) meaningful in band: {b}   "
          f"(c) Gemma >= 2/3 of harm: {c}")
    return a and b and c


def sign_p(k: int, n: int) -> float:
    """Two-sided exact binomial p for k of n in one direction."""
    tail = sum(comb(n, i) for i in range(max(k, n - k), n + 1)) / 2 ** n
    return min(1.0, 2 * tail)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=".")
    args = ap.parse_args()
    data = {t: {m: load(args.root, folder, m) for m in MODELS}
            for t, folder in TOPOLOGIES.items()}
    for m in MODELS:
        n = sum(v[2] for v in data["clique"][m].values())
        if n != 70:
            raise SystemExit(f"{m}: {n} Stag Hunt runs on the clique, expected 70")

    print("=" * 78)
    print("RULE 1 -- ledger replication on the clique")
    print("=" * 78)
    full = report_ledger(ledger(data["clique"]), "clique, every cell")
    clean = report_ledger(ledger(data["clique"], drop_invalid=True),
                          f"clique, cells above {INVALID_CUT:.0%} invalid removed")
    print(f"\n   RULE 1 HOLDS: {full and clean}")
    for t in ("star", "ring"):
        report_ledger(ledger(data[t]), f"{t}, every cell (for comparison)")

    print("\n" + "=" * 78)
    print("Totals over the three topologies (the thesis's Stag Hunt ledger)")
    print("=" * 78)
    rows = [r for t in TOPOLOGIES for r in ledger(data[t])]
    harmful = [r for r in rows if r[3] < -BAND]
    helpful = sum(r[3] > BAND for r in rows)
    print(f"{len(rows)} cells -- helpful {helpful}, neutral {len(rows) - helpful - len(harmful)}, "
          f"harmful {len(harmful)}")
    for kind in KINDS:
        k = [r for r in rows if r[2] == kind]
        print(f"   {kind:24s} mean delta {st.fmean(r[3] for r in k):+.3f}   "
              f"harmful {sum(r[3] < -BAND for r in k)}/{len(k)}")
    print("   harmful by model: " + ", ".join(
        f"{m} {sum(r[0] == m for r in harmful)}" for m in MODELS))
    by_topo = {t: {(r[0], r[1]) for r in ledger(data[t]) if r[3] < -BAND} for t in TOPOLOGIES}
    core = by_topo["star"] & by_topo["ring"] & by_topo["clique"]
    print(f"   harmful on all three topologies: {len(core)}, "
          f"{sum(m in GEMMA for m, _ in core)} of them in the Gemma models")
    for m, c in sorted(by_topo["clique"] - by_topo["star"] - by_topo["ring"]):
        print(f"   harmful on the clique only: {m} {c}")

    print("\n" + "=" * 78)
    print("RULE 2 -- topology, the 15 low-communication cells")
    print("=" * 78)
    print(f"{'model':24s} {'cell':9s} {'star':>6s} {'ring':>6s} {'clique':>7s}")
    tally = {"ring": [0, 0, 0], "star": [0, 0, 0]}
    for m in MODELS:
        for c in LOW:
            s, r, q = (data[t][m][c][0] for t in ("star", "ring", "clique"))
            print(f"{m:24s} {c:9s} {s:6.2f} {r:6.2f} {q:7.2f}")
            for other, o in (("ring", r), ("star", s)):
                tally[other][0 if q > o else 1 if q < o else 2] += 1
    for other, (hi, lo, tie) in tally.items():
        print(f"clique against {other}: higher {hi}, lower {lo}, tied {tie}   "
              f"(two-sided sign p {sign_p(max(hi, lo), 15):.3f})")
    effect = all(max(hi, lo) >= 12 for hi, lo, _ in tally.values()) and \
        (tally["ring"][0] >= 12) == (tally["star"][0] >= 12)
    print(f"\n   TOPOLOGY EFFECT DECLARED: {effect}")

    print("\n" + "=" * 78)
    print(f"RULE 3 -- clique cells above {INVALID_CUT:.0%} invalid (reported with a reservation)")
    print("=" * 78)
    for m in MODELS:
        for c, (value, invalid, n) in sorted(data["clique"][m].items()):
            if invalid > INVALID_CUT:
                print(f"   {m:24s} {c:40s} {invalid:.0%} invalid (cooperation {value:.2f}, n={n})")


if __name__ == "__main__":
    main()
