"""A private intention behind each message, read by the plan's rules.

Reads the cheap-talk runs of the `baseline` and `private_intent` scenarios
under the given roots (docs/private_intent_plan.md) and reports, per model,
game and topology: cooperation, promises and broken promises; and, for
private_intent, the plan's outcomes as its rules read them:

  R1  compliance   at least 90% of agent-rounds carry a valid intention,
                   pooled and on every topology
  R2  play         cooperation against the baseline of the same topology;
                   more than 0.20 apart counts as a change
  R3  P            premeditated / (premeditated + change of mind), pooled,
                   read from 20 broken promises: >= 0.50 mostly premeditated,
                   < 0.25 mostly a change of mind, mixed in between
  R4  L            share of the intended-defection rounds whose message
                   promises, with what followed (descriptive)
  R5  forecast     intention = action, the overturns, and what came before
                   each broken promise (descriptive)

A promise is a message that signal_rules.is_signal marks as advocating
cooperation now; for the Stag Hunt the same rules read "Stag" and "Hare" as
"cooperate" and "defect". The detector is not validated on every model, so
every valid LLM agent-round goes to --csv, with its message, for the hand
check the plan asks for.

Usage:
    python intent_report.py --roots <result trees> [--csv intent.csv]
"""
from __future__ import annotations

import argparse
import csv
import glob
import json
import os
import re
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from games import GAMES  # noqa: E402
from signal_rules import is_signal  # noqa: E402

STAG, HARE = re.compile(r"\bstag\b", re.I), re.compile(r"\bhare\b", re.I)
BLOCKS = ((1, 5), (6, 10), (11, 16))
CHANGE, MIN_BROKEN = 0.20, 20


def promise(message: str, game: str) -> bool:
    if not message:
        return False
    if game == "sh":
        message = HARE.sub("defect", STAG.sub("cooperate", message))
    return is_signal(message)


def category(intends_coop: bool | None, promised: bool, played_coop: bool) -> str:
    if intends_coop is None:
        return "no valid intention"
    if promised:
        return {(True, True): "kept", (True, False): "change of mind",
                (False, False): "premeditated", (False, True): "lie undone"}[(intends_coop, played_coop)]
    return {(True, True): "unannounced C", (True, False): "unannounced switch to D",
            (False, False): "honest D", (False, True): "switch to C"}[(intends_coop, played_coop)]


def plain_grid(cfg: dict) -> bool:
    """The grid as the baseline ran it: no filter, nothing hidden, everyone
    under the scenario's policy, standard names, the network described, and
    one model for every agent (a mixed population is no model's cell)."""
    return (cfg.get("message_filter", "none") == "none" and not cfg.get("hide_own_message")
            and cfg.get("policy_agents") is None and cfg.get("action_labels", "standard") == "standard"
            and not cfg.get("silent_topology") and cfg.get("source_agent") is None
            and not cfg.get("agent_models"))


def load_rows(roots: list[str]) -> list[dict]:
    rows = []
    for root in roots:
        for f in sorted(glob.glob(os.path.join(root, "**", "cheap_talk", "*_cheaptalk_run*.json"),
                                  recursive=True)):
            if f"{os.sep}zips{os.sep}" in f:
                continue
            with open(f, encoding="utf-8") as fh:
                d = json.load(fh)
            cfg = d["config"]
            if cfg.get("scenario") not in ("baseline", "private_intent") or not plain_grid(cfg):
                continue
            game = GAMES[cfg["game"]]
            coop = game.cooperative_action
            cell = (cfg["model"]["model_id"].split("/")[-1], cfg["game"], cfg["topology"],
                    bool(cfg.get("topology_aware_comm_prompt")))
            prev = None
            for r in d["history"]:
                intents = r.get("intentions")
                for a, act in r["actions"].items():
                    if act not in game.action_labels:
                        continue                  # invalid decisions are out, as everywhere
                    seen = r["messages_seen_by"].get(a, {})      # exactly the neighbours
                    it = intents.get(a) if intents is not None else None
                    row = dict(
                        model=cell[0], game=cell[1], topology=cell[2], commfix=cell[3],
                        scenario=cfg["scenario"], file=os.path.basename(f), run=d["run_id"],
                        round=r["round"], agent=int(a), hub=cell[2] == "star" and int(a) == 0,
                        intention="" if it is None else it,
                        intent_valid=it in game.action_labels if intents is not None else "",
                        promise=promise(r["messages"].get(a, ""), cfg["game"]),
                        action=act, coop=act == coop,
                        nb_all_promised=all(promise(m, cfg["game"]) for m in seen.values()),
                        nb_defected_before=prev is not None and any(
                            prev["actions"].get(nb) in game.action_labels
                            and prev["actions"].get(nb) != coop for nb in seen),
                        message=r["messages"].get(a, ""))
                    row["broken"] = row["promise"] and not row["coop"]
                    if intents is None:
                        row["category"] = ""
                    else:
                        ic = (it == coop) if it in game.action_labels else None
                        row["category"] = category(ic, row["promise"], row["coop"])
                    rows.append(row)
                prev = r
    return rows


def share(a: int, b: int) -> str:
    return f"{a}/{b} = {a / b:.2f}" if b else f"{a}/0"


def run_means(rows: list[dict]) -> list[float]:
    by = defaultdict(list)
    for x in rows:
        by[x["file"]].append(x["coop"])
    return [sum(v) / len(v) for _, v in sorted(by.items())]


def p_of(rows: list[dict]) -> tuple[int, int]:
    pre = sum(x["category"] == "premeditated" for x in rows)
    return pre, pre + sum(x["category"] == "change of mind" for x in rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--roots", nargs="+", required=True)
    ap.add_argument("--csv", default=None)
    args = ap.parse_args()
    rows = load_rows(args.roots)
    if not rows:
        raise SystemExit("no baseline or private_intent cheap-talk runs under these roots")
    if args.csv:
        with open(args.csv, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)
        print(f"{len(rows)} valid LLM agent-rounds -> {args.csv}")

    cells = defaultdict(list)
    for x in rows:
        cells[(x["model"], x["game"], x["topology"], x["commfix"], x["scenario"])].append(x)
    if not any(k[4] == "private_intent" for k in cells):
        print("no private_intent runs under these roots: nothing to read")
    for model, game in sorted({(k[0], k[1]) for k in cells}):
        intent = {k: v for k, v in cells.items() if k[:2] == (model, game) and k[4] == "private_intent"}
        if not intent:
            continue
        print(f"\n######## {model} {game.upper()}")
        pooled = [x for v in intent.values() for x in v]
        valid = [x for x in pooled if x["intent_valid"] is True]
        r1 = len(valid) >= 0.9 * len(pooled)
        print(f"R1 compliance: valid intentions {share(len(valid), len(pooled))}")
        for k, v in sorted(intent.items()):
            ok = sum(x["intent_valid"] is True for x in v)
            r1 = r1 and ok >= 0.9 * len(v)
            print(f"     {k[2]:6}: {share(ok, len(v))}")
        print(f"   -> {'passes' if r1 else 'FAILS: the field was not followed; R3-R5 are not read'}")

        print("R2 play, cooperation against the baseline of the same topology:")
        changed = set()
        for k, v in sorted(intent.items()):
            base = cells.get(k[:4] + ("baseline",), [])
            mi, mb = run_means(v), run_means(base)
            for lab, m, sel in (("private_intent", mi, v), ("baseline", mb, base)):
                if not m:
                    print(f"     {k[2]:6} {lab:14}: no runs")
                    continue
                prom = [x for x in sel if x["promise"]]
                print(f"     {k[2]:6} {lab:14}: {sum(m) / len(m):.2f} (runs {', '.join(f'{x:.2f}' for x in m)}); "
                      f"promises {share(len(prom), len(sel))}, broken {share(sum(x['broken'] for x in prom), len(prom))}")
            if mi and mb and abs(sum(mi) / len(mi) - sum(mb) / len(mb)) > CHANGE:
                changed.add(k[2])
        print(f"   -> {'the field changes play on: ' + ', '.join(sorted(changed)) if changed else 'no topology moves by more than 0.20'}")
        if not r1:
            continue

        pre, broken = p_of(pooled)
        print(f"R3 P, premeditated share of broken promises: {share(pre, broken)}")
        if broken < MIN_BROKEN:
            print(f"   -> too few broken promises to read (fewer than {MIN_BROKEN})")
        else:
            p = pre / broken
            verdict = ("mostly premeditated" if p >= 0.50 else
                       "mostly a change of mind in the action phase" if p < 0.25 else "mixed")
            print(f"   -> {verdict}")
        for k, v in sorted(intent.items()):
            print(f"     {k[2]:6}: {share(*p_of(v))}{'  (play changed here)' if k[2] in changed else ''}")
        print(f"     star hub: {share(*p_of([x for x in pooled if x['hub']]))}; "
              f"everyone else: {share(*p_of([x for x in pooled if not x['hub']]))}")
        for a, b in BLOCKS:
            print(f"     rounds {a}-{b}: {share(*p_of([x for x in pooled if a <= x['round'] <= b]))}")
        per_run = []
        by_run = defaultdict(list)
        for x in pooled:
            by_run[(x["topology"], x["run"])].append(x)
        for (topo, run), v in sorted(by_run.items()):
            a, b = p_of(v)
            if b:
                per_run.append(f"{topo}#{run} {a}/{b}")
        print(f"     per run: {'; '.join(per_run) or 'none broken'}")

        coop = GAMES[game].cooperative_action
        other = [x for x in valid if x["intention"] != coop]
        lied = [x for x in other if x["promise"]]
        print(f"R4 L, intended the other action and promised: {share(len(lied), len(other))}; "
              f"then played it {sum(not x['coop'] for x in lied)}, cooperated instead {sum(x['coop'] for x in lied)}")

        agree = sum(x["action"] == x["intention"] for x in valid)
        print(f"R5 intention = action {share(agree, len(valid))}; overturned "
              f"C->D {sum(x['intention'] == coop and not x['coop'] for x in valid)}, "
              f"D->C {sum(x['intention'] != coop and x['coop'] for x in valid)}")
        com = [x for x in pooled if x["category"] == "change of mind"]
        prem = [x for x in pooled if x["category"] == "premeditated"]
        print(f"     change of mind: every neighbour promised this round {sum(x['nb_all_promised'] for x in com)}, "
              f"some neighbour did not {sum(not x['nb_all_promised'] for x in com)}")
        print(f"     premeditated: a neighbour defected the round before {sum(x['nb_defected_before'] for x in prem)}, "
              f"none did {sum(not x['nb_defected_before'] for x in prem)}")
        print("     categories: " + "; ".join(f"{c} {n}" for c, n in Counter(x["category"] for x in pooled).most_common()))


if __name__ == "__main__":
    main()
