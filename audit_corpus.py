"""Integrity audit of finished run folders: everything the logs can prove.

Run it on every new batch, next to `verify_prompts.py` (which rebuilds the
prompts) -- this one checks the recorded data itself:

  protocol      4 agents, 16 rounds numbered 1..16, memory 10, T=0.7, seed 42,
                <=20-word messages, action_retries 0
  topology      the record's type matches the folder and the config, and the
                edge list is the one the topology would produce
  payoffs       every round's payoffs recomputed from the actions
  delivery      messages_seen_by equals exactly the sender's neighbours
  content       silence delivers empty strings, no_sense only canned ones, and
                nothing is blocked unless a filter is on
  duplicates    no two runs anywhere share a history
  independence  no_sense replicates draw different template sequences (before
                2026-07-27 the per-run seed did not exist, so the star grid's
                five replicates share one sequence -- a known, reported flaw)
  budgets       max_tokens per (model, scenario, topology), so a mismatch like
                gemma-2-9b's framing_competitive is visible
  leakage       star vocabulary in the reasoning traces of non-star runs, the
                signature of the 2026-09-20 prompt bug
  invalid       cells above 10% unparseable actions

Usage:
    python audit_corpus.py <run folder> [<run folder> ...]
"""
from __future__ import annotations

import glob
import hashlib
import json
import os
import re
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from games import GAMES
from message_policies import IRRELEVANT_TEMPLATES
from topology import make_topology

STAR_WORDS = re.compile(r"\b(central agent|peripheral|hub)\b", re.I)
PROTOCOL = (("n_agents", 4), ("n_rounds", 16), ("memory_window", 10),
            ("seed", 42), ("message_max_words", 20), ("action_retries", 0))


def run_files(root: str):
    for p in sorted(glob.glob(f"{root}/**/*.json", recursive=True)):
        if os.path.basename(p).startswith("_") or f"{os.sep}zips{os.sep}" in p:
            continue
        try:
            with open(p, encoding="utf-8") as f:
                rec = json.load(f)
        except (json.JSONDecodeError, OSError, UnicodeDecodeError) as e:
            yield p, None, str(e)
            continue
        if "config" in rec and "history" in rec:
            yield p, rec, None


def audit(roots: list[str]) -> int:
    issues = defaultdict(list)
    budgets = defaultdict(set)
    invalid = defaultdict(lambda: [0, 0])
    histories = defaultdict(list)
    nosense = defaultdict(list)
    leak = defaultdict(lambda: [0, 0])
    flags = defaultdict(Counter)
    n_files = 0

    for root in roots:
        for path, rec, err in run_files(root):
            if err:
                issues[root].append(f"unreadable {path}: {err}")
                continue
            n_files += 1
            cfg, model, hist = rec["config"], rec["config"]["model"], rec["history"]
            rel = os.path.relpath(path, root)
            parts = rel.split(os.sep)
            topo_name = rec["topology"].get("type", "star")
            add = lambda m: issues[root].append(f"{m} [{rel}]")

            for key, want in PROTOCOL:
                if cfg.get(key, want) != want:
                    add(f"{key}={cfg.get(key)}")
            if model["temperature"] != 0.7:
                add(f"temperature={model['temperature']}")
            if len(hist) != 16 or [x["round"] for x in hist] != list(range(1, 17)):
                add(f"rounds={len(hist)}")
            if cfg.get("topology", "star") != topo_name:
                add(f"config topology {cfg.get('topology')} vs record {topo_name}")
            base = os.path.basename(root.rstrip(os.sep))
            for name in ("cycle", "clique", "line"):
                if f"_{name}" in base and topo_name != name:
                    add(f"folder says {name}, record says {topo_name}")
            topo = make_topology(topo_name, cfg["n_agents"])
            if sorted(map(tuple, rec["topology"]["edges"])) != sorted(topo.edges()):
                add("edge list does not match the topology")
            scenario = cfg.get("scenario") or parts[0]
            if len(parts) >= 2 and parts[-2] != cfg["condition"]:
                add(f"condition folder {parts[-2]} vs {cfg['condition']}")
            flags[root][(bool(cfg.get("topology_aware_comm_prompt", False)),
                         cfg.get("message_filter", "none"))] += 1
            budgets[(model["model_id"].split("/")[-1], scenario, topo_name)].add(
                model["max_tokens"])
            histories[hashlib.md5(json.dumps(hist, sort_keys=True).encode()).hexdigest()
                      ].append(path)

            game = GAMES[cfg["game"]]
            valid = set(game.action_labels)
            key = (root, scenario, cfg["condition"], cfg["game"])
            for x in hist:
                acts = {int(k): v for k, v in x["actions"].items()}
                pay = {i: 0 for i in acts}
                for u, v in topo.edges():
                    if acts.get(u) in valid and acts.get(v) in valid:
                        pay[u] += game.payoffs[(acts[u], acts[v])][0]
                        pay[v] += game.payoffs[(acts[v], acts[u])][0]
                if pay != {int(k): v for k, v in x["payoffs"].items()}:
                    add(f"payoff mismatch, round {x['round']}")
                    break
                invalid[key][0] += sum(1 for a in acts.values() if a not in valid)
                invalid[key][1] += len(acts)
                if topo_name != "star":
                    lk = leak[(root, cfg["condition"])]
                    for reason in x.get("reasonings", {}).values():
                        lk[1] += 1
                        lk[0] += bool(STAR_WORDS.search(str(reason)))
                if cfg["condition"] != "cheap_talk":
                    continue
                msgs = {int(k): v for k, v in x["messages"].items()}
                seen = {int(k): {int(s): t for s, t in d.items()}
                        for k, d in x["messages_seen_by"].items()}
                if seen != {i: {s: msgs[s] for s in topo.neighbors(i)} for i in msgs}:
                    add(f"delivery mismatch, round {x['round']}")
                    break
                policy = cfg["message_policy"]
                if policy == "silence" and any(v for v in msgs.values()):
                    add("silence delivered a non-empty message")
                elif policy in ("no_sense", "irrelevant"):
                    if any(v not in IRRELEVANT_TEMPLATES for v in msgs.values()):
                        add("no_sense delivered something that is not a template")
                else:
                    if any(len(v.split()) > 20 for v in msgs.values()):
                        add("a message is longer than 20 words")
                    if (cfg.get("message_filter", "none") == "none"
                            and any(x.get("messages_blocked", {}).values())):
                        add("a message was blocked with no filter configured")
            if cfg["condition"] == "cheap_talk" and cfg["message_policy"] in (
                    "no_sense", "irrelevant"):
                nosense[(root, cfg["game"])].append(
                    tuple(tuple(sorted(x["messages"].items())) for x in hist))

    print(f"{n_files} run files in {len(roots)} folder(s)\n")
    for root in roots:
        print(f"{root:58s} flags {dict(flags[root])}")

    print("\nISSUES")
    total = sum(len(v) for v in issues.values())
    for root, found in issues.items():
        print(f"  {root}: {len(found)}")
        for one in found[:5]:
            print("     ", one)
    if not total:
        print("  none")

    dups = [v for v in histories.values() if len(v) > 1]
    print(f"\nduplicate histories: {len(dups)}")
    for v in dups[:5]:
        print("   ", v)

    print("\nno_sense replicates sharing one template sequence")
    shared = {k: (len(set(v)), len(v)) for k, v in nosense.items() if len(set(v)) != len(v)}
    for k, (u, n) in sorted(shared.items()):
        print(f"   {k[0]} [{k[1]}]: {u} distinct of {n}")
    print(f"   checked {len(nosense)} cell(s), {len(shared)} affected")

    print("\nmax_tokens that differ within a (model, scenario)")
    by = defaultdict(dict)
    for (model, scenario, topo), vals in budgets.items():
        by[(model, scenario)][topo] = sorted(vals)
    for k, d in sorted(by.items()):
        allv = {v for vals in d.values() for v in vals}
        if len(allv) > 1:
            print("  ", k, d)

    print("\nstar vocabulary in reasonings of non-star runs")
    for (root, cond), (hits, n) in sorted(leak.items()):
        print(f"   {root:48s} {cond:10s} {hits:6d}/{n:6d} = {hits / n if n else 0:.3f}")

    print("\ninvalid-action rate above 10%")
    worst = [(k, a, b) for k, (a, b) in sorted(invalid.items()) if b and a / b > 0.10]
    for k, a, b in worst:
        print(f"   {k}  {a}/{b} = {a / b:.2f}")
    if not worst:
        print("   none")
    return 1 if total or dups else 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    raise SystemExit(audit(sys.argv[1:]))
