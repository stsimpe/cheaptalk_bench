"""The four log-only checks that bound the cheap-talk prompt bug.

Until 2026-09-20 the cheap-talk system prompt carried one routing sentence,
written for the star, on every topology (see prompts.STAR_COMMUNICATION_LEGACY).
Every ring run with an open channel was therefore told about a hub it did not
have. Delivery never reads the prompt, so the question is not whether the data
is real -- it is -- but whether the contradiction changed behaviour.

Each check bounds something different, and none of them needs a GPU:

  routing    did every agent actually receive what its topology implies?
  traces     did the contradiction enter the agents' private reasoning?
  messages   did it reach the channel, where other agents would see it?
  position   did agent 0 (the hub under the star) behave like a hub in a ring,
             where all four positions are exchangeable? The no_comm condition
             never carried the sentence, so it is the control.

Run before and after the corrected-prompt ablation so the comparison is one
command:

    python cheaptalk_bench/verify_prompt_bug.py --roots <the ten run folders>
    python cheaptalk_bench/verify_prompt_bug.py --roots <the commfix folders>
"""
from __future__ import annotations

import argparse
import collections
import glob
import json
import os
import re
import statistics

from games import GAMES

STAR_VOCAB = re.compile(
    r"central agent|\bhub\b|peripheral|the cent(er|re)|broadcast|"
    r"all three neighbou?rs", re.I)
RING_VOCAB = re.compile(
    r"\bring\b|\bcycle\b|adjacent|both neighbou?rs|two neighbou?rs", re.I)


def load(roots: list[str]):
    for root in roots:
        for path in sorted(glob.glob(os.path.join(root, "**", "*.json"),
                                     recursive=True)):
            if os.path.basename(path).startswith("_"):
                continue
            with open(path, encoding="utf-8") as f:
                rec = json.load(f)
            if "history" in rec and "config" in rec:
                yield path, rec


def traces(rec):
    for rnd in rec["history"]:
        for key in ("reasonings", "comm_reasonings"):
            for val in (rnd.get(key) or {}).values():
                if val:
                    yield str(val)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--roots", nargs="+", required=True)
    ap.add_argument("--game", default=None, choices=["pd", "sh"],
                    help="Restrict to one game (default: both).")
    args = ap.parse_args()

    routing_bad: list[str] = []
    agent_rounds = 0
    vocab: dict[tuple[str, str], list[int]] = collections.defaultdict(
        lambda: [0, 0, 0])          # traces, star hits, ring hits
    msgs: dict[str, list[int]] = collections.defaultdict(lambda: [0, 0])
    asym: dict[tuple[str, str, str], list[float]] = collections.defaultdict(list)
    counts: collections.Counter = collections.Counter()

    for path, rec in load(args.roots):
        cfg = rec["config"]
        if args.game and cfg["game"] != args.game:
            continue
        topo = rec["topology"]
        tname = topo.get("type", "star")
        cond = cfg["condition"]
        model = cfg["model"]["model_id"].split("/")[-1]
        counts[(model, tname, cond)] += 1

        # --- routing -------------------------------------------------------
        if cond == "cheap_talk":
            hub = topo.get("hub_id")
            degree = {a: 0 for a in range(topo["n_agents"])}
            for a, b in topo["edges"]:
                degree[a] += 1
                degree[b] += 1
            for rnd in rec["history"]:
                for aid, seen in (rnd.get("messages_seen_by") or {}).items():
                    agent_rounds += 1
                    want = degree[int(aid)]
                    if len(seen) != want:
                        routing_bad.append(
                            f"{path} r{rnd['round']} agent {aid}: "
                            f"{len(seen)} messages, degree {want}")
            for rnd in rec["history"]:
                for msg in (rnd.get("messages") or {}).values():
                    if msg:
                        msgs[tname][0] += 1
                        msgs[tname][1] += bool(STAR_VOCAB.search(str(msg)))

        # --- private traces ------------------------------------------------
        slot = vocab[(tname, cond)]
        for text in traces(rec):
            slot[0] += 1
            slot[1] += bool(STAR_VOCAB.search(text))
            slot[2] += bool(RING_VOCAB.search(text))

        # --- positional symmetry (ring only) --------------------------------
        if tname == "cycle":
            coop = GAMES[cfg["game"]].cooperative_action
            per = collections.defaultdict(lambda: [0, 0])
            for rnd in rec["history"]:
                for aid, act in rnd["actions"].items():
                    if (rnd.get("invalid") or {}).get(aid):
                        continue
                    per[int(aid)][0] += (act == coop)
                    per[int(aid)][1] += 1
            rate = {a: c / n for a, (c, n) in per.items() if n}
            if 0 in rate and len(rate) == topo["n_agents"]:
                others = statistics.fmean(v for a, v in rate.items() if a)
                asym[(model, cond, cfg["game"])].append(rate[0] - others)

    print(f"runs: {sum(counts.values())}")
    for key in sorted(counts):
        print(f"  {key[0]:24s} {key[1]:6s} {key[2]:11s} {counts[key]:4d}")

    print(f"\nROUTING   agent-rounds checked: {agent_rounds}   "
          f"violations: {len(routing_bad)}")
    for line in routing_bad[:5]:
        print("   ", line)

    print("\nTRACES    star vocabulary in private reasoning")
    for key in sorted(vocab):
        tot, star, ring = vocab[key]
        if not tot:
            continue
        print(f"  {key[0]:6s} {key[1]:11s} traces {tot:7d}   "
              f"star {star:5d} ({star/tot:6.2%})   ring {ring:6d} ({ring/tot:6.2%})")
    print("  (the no_comm rows never contained the sentence: that is the "
          "hallucination floor)")

    print("\nMESSAGES  star vocabulary in what was actually delivered")
    for tname in sorted(msgs):
        tot, star = msgs[tname]
        print(f"  {tname:6s} messages {tot:7d}   star {star:5d} ({star/max(tot,1):.2%})")

    print("\nPOSITION  ring: agent 0 minus the mean of the others")
    by_model = collections.defaultdict(lambda: collections.defaultdict(list))
    for (model, cond, _game), vals in asym.items():
        by_model[model][cond].extend(vals)
    for model in sorted(by_model):
        row = []
        for cond in ("cheap_talk", "no_comm"):
            vals = by_model[model].get(cond) or []
            row.append(f"{cond}: {statistics.fmean(vals):+.4f} (n={len(vals)})"
                       if vals else f"{cond}: --")
        print(f"  {model:24s} " + "   ".join(row))
    print("  (no_comm is the control; a hub effect would make cheap_talk larger)")


if __name__ == "__main__":
    main()
