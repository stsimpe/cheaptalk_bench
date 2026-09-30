"""Where the harm of an adversarial instruction is produced.

The competitive frame inside the messages is the one systematic route to a
harmful equilibrium. Three purpose-built cells take it apart, all against the
plain grid cells of the same model and topology:

  block_all           everyone writes adversarially, nothing is delivered
                      -> is a reader needed at all?
  block_all+hideown   the same, and the writer is not shown its own message
                      -> does re-reading its own words matter?
  agents0             one instructed writer, three ordinary ones
                      -> how far does it travel, and through what?

The last one is run on the star and on the clique, because on a star the
writer is every reader's only partner and a reader's fall cannot be told
apart from ordinary reciprocity.

Usage:
    python harm_source_report.py --harm-dir harm_source --grid-root .
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import statistics as st
from collections import defaultdict

from analysis import summarise_run

MODELS = ["Llama-3.1-8B-Instruct", "Qwen2.5-7B-Instruct", "Qwen3-4B",
          "gemma-2-2b-it", "gemma-2-9b-it"]
GOOD = {"Cooperate", "Stag"}
VALID = GOOD | {"Defect", "Hare"}


def records(root: str):
    for p in glob.glob(f"{root}/**/*.json", recursive=True):
        if os.path.basename(p).startswith("_") or f"{os.sep}zips{os.sep}" in p:
            continue
        with open(p, encoding="utf-8") as f:
            rec = json.load(f)
        if "config" in rec and rec["config"]["game"] == "pd":
            yield rec


def mean_coop(root: str) -> float:
    v = [summarise_run(r)["coop_rate_overall"] for r in records(root)]
    return st.fmean(v) if v else float("nan")


def cell(grid_root: str, model: str, topology: str, scenario: str,
         condition: str = "cheap_talk") -> float:
    root = os.path.join(grid_root, f"{model}_{topology}", scenario, condition)
    v = [summarise_run(json.load(open(p, encoding="utf-8")))["coop_rate_overall"]
         for p in glob.glob(f"{root}/*_pd_*.json")]
    return st.fmean(v) if v else float("nan")


def writer_readers(root: str) -> tuple[float, float]:
    """Cooperation of agent 0 and of agents 1-3, averaged over runs."""
    w, r = [], []
    for rec in records(root):
        acts = [x["actions"] for x in rec["history"]]
        wa = [a["0"] for a in acts if a["0"] in VALID]
        ra = [a[str(i)] for a in acts for i in (1, 2, 3) if a[str(i)] in VALID]
        w.append(sum(a in GOOD for a in wa) / len(wa) if wa else float("nan"))
        r.append(sum(a in GOOD for a in ra) / len(ra) if ra else float("nan"))
    return (st.fmean(w), st.fmean(r)) if w else (float("nan"), float("nan"))


def conditional(root: str) -> tuple[float, float, int, int]:
    """Reader cooperation at t, given the writer's action at t-1."""
    after = {"Cooperate": [0, 0], "Defect": [0, 0]}
    for rec in records(root):
        acts = [x["actions"] for x in rec["history"]]
        for t in range(1, len(acts)):
            prev = acts[t - 1]["0"]
            if prev not in VALID:
                continue
            for i in (1, 2, 3):
                cur = acts[t][str(i)]
                if cur in VALID:
                    after[prev][1] += 1
                    after[prev][0] += cur in GOOD
    f = lambda a: a[0] / a[1] if a[1] else float("nan")
    return f(after["Cooperate"]), f(after["Defect"]), after["Cooperate"][1], after["Defect"][1]


def line(label: str, values: list[float]) -> str:
    return f"{label:34s}" + "".join(f"{v:8.2f}" for v in values)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--harm-dir", default="harm_source")
    ap.add_argument("--grid-root", default=".")
    args = ap.parse_args()
    H, G = args.harm_dir, args.grid_root

    print("=" * 78)
    print("1. Does the harm need a reader?  (PD, star, cooperation rate)")
    print("=" * 78)
    rows = {
        "no_comm": [cell(G, m, "star", "baseline", "no_comm") for m in MODELS],
        "silence (nobody writes)": [cell(G, m, "star", "silence") for m in MODELS],
        "competitive (all delivered)": [cell(G, m, "star", "framing_competitive") for m in MODELS],
        "block_all (none delivered)": [mean_coop(f"{H}/{m}_block_all") for m in MODELS],
        "block_all + own hidden": [mean_coop(f"{H}/{m}_block_all_hideown") for m in MODELS],
        "baseline cheap talk": [cell(G, m, "star", "baseline") for m in MODELS],
    }
    print(f"{'cell':34s}" + "".join(f"{m.split('-')[0][:7]:>8s}" for m in MODELS))
    for k, v in rows.items():
        print(line(k, v))
    for a, b in [("block_all (none delivered)", "competitive (all delivered)"),
                 ("block_all (none delivered)", "silence (nobody writes)"),
                 ("block_all + own hidden", "block_all (none delivered)")]:
        d = [x - y for x, y in zip(rows[a], rows[b]) if x == x and y == y]
        if d:
            print(f"  {a} minus {b}: mean {st.fmean(d):+.2f}  {[round(x, 2) for x in d]}")

    print()
    print("=" * 78)
    print("2. How far does it travel?  One instructed writer among three ordinary")
    print("=" * 78)
    for topo, suffix in [("star", "_agents0"), ("clique", "_clique_commfix_agents0")]:
        print(f"\n{topo}")
        print(f"{'model':22s}{'writer':>8s}{'readers':>9s}{'baseline':>10s}"
              f"{'after writer C':>16s}{'after writer D':>16s}")
        for m in MODELS:
            root = f"{H}/{m}{suffix}"
            if not os.path.isdir(root):
                continue
            w, r = writer_readers(root)
            c, d, nc, nd = conditional(root)
            base = cell(G, m, topo, "baseline")
            print(f"{m:22s}{w:8.2f}{r:9.2f}{base:10.2f}{c:16.2f}{d:16.2f}")
        print("  (baseline cheap talk is the cell where every agent writes ordinary "
              "messages)")


if __name__ == "__main__":
    main()
