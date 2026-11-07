"""Size or generation: the reading rules of docs/qwen35_scale_plan.md.

Reads grid trees (sessions A, B and C of run_all_scenarios.py) and prints:

  the grid    mean of run means over valid decisions, per model, cell, game
              and topology, as the Qwen3.5-122B table in TRACK_RECORD.md
  markers     the plan's three Prisoner's Dilemma markers, per model:
                M1 talk        baseline_cheap_talk           star, ring, clique
                M2 no channel  no_comm, silence, no_sense     star, ring, clique
                M3 frame gap   framing_team_context[cheap_talk] - framing_team
                                                             star, clique
              (each a plain mean of cell values over the topologies listed:
              the topologies where the corpus has the cells under the same
              prompt as the lab server's runs)
  verdict     for the target model, each marker read against the large model
              and the range of the five corpus models, then the plan's verdict

Only plain grid runs count (no filter, nothing hidden, no scripted or framed
subset of agents, standard action names, the network described). A cell is
named as in TRACK_RECORD.md: no_comm, baseline_cheap_talk, the single-arm
scenarios by name, and the two arms of a *_context scenario as
scenario[no_comm] and scenario[cheap_talk].

Usage:
    python scale_report.py --roots <trees> [--target Qwen3.5-9B]
                           [--large Qwen3.5-122B-A10B]
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from games import GAMES  # noqa: E402
from intent_report import plain_grid  # noqa: E402

CORPUS = ("Llama-3.1-8B-Instruct", "Qwen2.5-7B-Instruct", "Qwen3-4B", "gemma-2-2b-it", "gemma-2-9b-it")
MAX_INVALID = 0.10          # rule 1: invalid decisions on any topology, as audit_corpus.py flags
CELLS = ("no_comm", "baseline_cheap_talk", "no_sense", "silence", "counterfactual",
         "framing_business", "framing_team", "framing_competitive",
         "framing_business_context[no_comm]", "framing_business_context[cheap_talk]",
         "framing_team_context[no_comm]", "framing_team_context[cheap_talk]",
         "framing_competitive_context[no_comm]", "framing_competitive_context[cheap_talk]")
TOPOS = ("star", "cycle", "clique")
ALL3, STAR_CLIQUE = ("star", "cycle", "clique"), ("star", "clique")
# name, cells, topologies. A marker is the mean of its cells, except the frame
# gap: the second cell minus the first.
MARKERS = (
    ("M1 talk", ("baseline_cheap_talk",), ALL3),
    ("M2 no channel", ("no_comm", "silence", "no_sense"), ALL3),
    ("M3 frame gap", ("framing_team", "framing_team_context[cheap_talk]"), STAR_CLIQUE),
)


def cell_name(cfg: dict) -> str:
    sc, cond = cfg.get("scenario"), cfg.get("condition")
    if sc == "baseline":
        return "no_comm" if cond == "no_comm" else "baseline_cheap_talk"
    if sc and sc.endswith("_context"):
        return f"{sc}[{cond}]"
    return sc


def load(roots: list[str]):
    """{(model, game, topology, cell): [run means]} over plain grid runs, with
    rule 1's counts: decisions and invalid decisions per (model, topology), and
    the round-1 message prompt tokens of baseline_cheap_talk per (model,
    topology)."""
    by, seen = defaultdict(list), set()
    decisions, invalid, tokens = defaultdict(int), defaultdict(int), defaultdict(set)
    for root in roots:
        for f in sorted(glob.glob(os.path.join(root, "**", "*_run*.json"), recursive=True)):
            path = os.path.abspath(f)
            if f"{os.sep}zips{os.sep}" in path or path in seen:
                continue
            seen.add(path)
            try:
                with open(f, encoding="utf-8") as fh:
                    d = json.load(fh)
                cfg = d["config"]
            except (json.JSONDecodeError, KeyError, UnicodeDecodeError):
                continue
            # The corpus star runs of June 2026 record neither the scenario nor
            # the topology: the scenario is the folder above the arm's folder
            # (<tree>/<scenario>/<arm>/<run>), and the star was then the only
            # topology.
            cfg = dict(cfg,
                       scenario=cfg.get("scenario") or os.path.basename(os.path.dirname(os.path.dirname(path))),
                       condition=cfg.get("condition") or os.path.basename(os.path.dirname(path)),
                       topology=cfg.get("topology") or "star")
            if not plain_grid(cfg) or cfg.get("n_agents", 4) != 4 or cell_name(cfg) not in CELLS:
                continue
            game = GAMES[cfg["game"]]
            model = cfg["model"]["model_id"].split("/")[-1]
            every = [a for r in d["history"] for a in r["actions"].values()]
            decisions[(model, cfg["topology"])] += len(every)
            invalid[(model, cfg["topology"])] += sum(a not in game.action_labels for a in every)
            if cell_name(cfg) == "baseline_cheap_talk" and d["history"]:
                for calls in d["history"][0].get("llm_calls", {}).values():
                    tokens[(model, cfg["topology"])].update(
                        c["prompt_tokens"] for c in calls
                        if c.get("phase") == "message" and c.get("prompt_tokens") is not None)
            acts = [a for a in every if a in game.action_labels]
            if not acts:
                continue
            key = (model, cfg["game"], cfg["topology"], cell_name(cfg))
            by[key].append(sum(a == game.cooperative_action for a in acts) / len(acts))
    return by, decisions, invalid, tokens


def mean(xs):
    xs = list(xs)
    return sum(xs) / len(xs) if xs else float("nan")


def cell(by, model, game, topo, c):
    v = by.get((model, game, topo, c))
    return mean(v) if v else float("nan")


def marker(by, model, cells, topos):
    """The marker's value for one model; nan if any cell is missing."""
    vals = []
    for t in topos:
        cv = [cell(by, model, "pd", t, c) for c in cells]
        if any(x != x for x in cv):
            return float("nan")
        vals.append(cv[1] - cv[0] if len(cells) == 2 and cells[0] == "framing_team" else mean(cv))
    return mean(vals)


def read(target, large, corpus):
    """One marker for the target: like the large model, like the corpus,
    between, or not informative (the large model inside the corpus range)."""
    lo, hi = min(corpus), max(corpus)
    if large < lo:
        mid = (large + lo) / 2
        return ("like the large model" if target <= mid else "like the corpus" if target >= lo
                else "between"), mid
    if large > hi:
        mid = (large + hi) / 2
        return ("like the large model" if target >= mid else "like the corpus" if target <= hi
                else "between"), mid
    return "not informative", float("nan")


def f2(x):
    return " -  " if x != x else f"{x:.2f}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--roots", nargs="+", required=True)
    ap.add_argument("--target", default="Qwen3.5-9B")
    ap.add_argument("--large", default="Qwen3.5-122B-A10B")
    args = ap.parse_args()
    by, decisions, invalid, tokens = load(args.roots)
    models = sorted({k[0] for k in by})
    if not models:
        raise SystemExit("no plain grid runs under these roots")

    ok = False
    if args.target in models:
        print(f"######## rule 1 for {args.target}: invalid decisions (at most {MAX_INVALID:.0%} on every "
              f"topology) and round-1 message prompt tokens of baseline_cheap_talk against {args.large}")
        ok = True
        for t in TOPOS:
            n, bad = decisions[(args.target, t)], invalid[(args.target, t)]
            same = tokens[(args.target, t)] == tokens[(args.large, t)] and bool(tokens[(args.target, t)])
            ok &= bool(n) and bad <= MAX_INVALID * n and same
            print(f"   {t:6}: invalid {bad}/{n} = {bad / n if n else float('nan'):.3f}; tokens "
                  f"{sorted(tokens[(args.target, t)])} against {sorted(tokens[(args.large, t)])}"
                  f" -> {'equal' if same else 'NOT EQUAL'}")
        print("   -> " + ("passes these two checks; rule 1 also needs verify_prompts.py and "
                          "audit_corpus.py, which this script does not run" if ok
                          else "FAILS: nothing else is read"))

    for m in [x for x in (args.large, args.target) if x in models] + [x for x in models if x not in (args.large, args.target)]:
        n = sum(len(v) for k, v in by.items() if k[0] == m)
        print(f"\n######## {m}: the grid ({n} runs), mean of run means over valid decisions")
        print(f"{'cell':42}" + "".join(f"{g.upper()} {t:7}" for g in ("pd", "sh") for t in TOPOS))
        for c in CELLS:
            row = [cell(by, m, g, t, c) for g in ("pd", "sh") for t in TOPOS]
            if all(x != x for x in row):
                continue
            print(f"{c:42}" + "".join(f"{f2(x):11}" for x in row))
        ns = sorted({len(v) for k, v in by.items() if k[0] == m})
        print(f"   runs per cell: {ns}")

    print("\n######## the markers (PD)")
    print(f"{'model':24}" + "".join(f"{name:16}" for name, *_ in MARKERS))
    vals = {m: [marker(by, m, cells, topos) for _, cells, topos in MARKERS] for m in models}
    for m in models:
        print(f"{m:24}" + "".join(f"{f2(v):16}" for v in vals[m]))
    for name, cells, topos in MARKERS:
        print(f"   {name}: {cells[1] + ' - ' + cells[0] if cells[0] == 'framing_team' else ', '.join(cells)}; "
              f"over {', '.join(topos)}")

    corpus = [m for m in CORPUS if m in vals]
    if args.target not in vals or args.large not in vals or len(corpus) < len(CORPUS):
        missing = [m for m in (args.target, args.large, *CORPUS) if m not in vals]
        print(f"\nverdict: not read; missing {missing}")
        return
    if not ok:
        print("\nverdict: not read; rule 1 fails")
        return
    print(f"\n######## the verdict for {args.target}, against {args.large} and the corpus ({len(corpus)} models)")
    counts = defaultdict(int)
    for i, (name, *_rest) in enumerate(MARKERS):
        cv = [vals[m][i] for m in corpus]
        t, lg = vals[args.target][i], vals[args.large][i]
        if t != t or lg != lg or any(x != x for x in cv):
            print(f"   {name}: a cell is missing; not read")
            counts["not read"] += 1
            continue
        res, mid = read(t, lg, cv)
        counts[res] += 1
        print(f"   {name}: {args.target} {t:.2f}; {args.large} {lg:.2f}; corpus {min(cv):.2f}-{max(cv):.2f}; "
              f"midpoint {f2(mid)} -> {res}")
    big, small = counts["like the large model"], counts["like the corpus"]
    verdict = ("generation: the target behaves as the large model" if big >= 2 and small == 0 else
               "size: the target behaves as the corpus" if small >= 2 and big == 0 else "mixed")
    print(f"   -> {big} like {args.large}, {small} like the corpus, {counts['between']} between, "
          f"{counts['not informative'] + counts['not read']} not informative or not read: {verdict}")


if __name__ == "__main__":
    main()
