"""Message pools for the scripted source of the contagion experiment.

The source agent of the words-versus-deeds design does not call a model: it
plays a fixed action and sends a message drawn from a pool. Drawing the pool
from the corpus, per model, keeps the source's words in the register and
style that model actually writes, and keeps the dose under control.

  hostile      framing_competitive messages of that model that carry the
               competitive register (they trip the F1 lexicon) and say
               nothing about cooperating
  cooperative  baseline_cheap_talk messages of that model that advocate
               cooperation (signal_rules.is_signal)

Only PD, star and ring grid runs. Messages that name a star-network role
("hub", "central agent", "leaves", ...) are dropped: the experiment runs on
a line, and a message about a hub would tell the reader something false
about its network.

Usage:
    python build_source_pools.py --corpus <diplomatikh folder> \
        --models Qwen2.5-7B-Instruct Llama-3.1-8B-Instruct --out pools
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analysis import summarise_run  # noqa: E402
from cross_model_analysis import cell_label, discover_records  # noqa: E402
from message_policies import MESSAGE_FILTERS  # noqa: E402
from signal_rules import is_signal  # noqa: E402

STAR_WORDS = re.compile(
    r"\b(hub|hubs|central|centre|center|peripheral|periphery|leaf|leaves|"
    r"broadcast\w*|spoke|spokes|star)\b", re.I)
F1 = MESSAGE_FILTERS["F1_competitive"]


COOP_WORDS = re.compile(r"cooperat|collaborat|together|mutual|trust|partner", re.I)


def hostile(msg: str) -> bool:
    return bool(F1 & set(re.findall(r"[a-z']+", msg.lower())))


def purely_hostile(msg: str) -> bool:
    """Competitive register and no word of cooperation. The competitive cells
    also hold mixed lines ("Cooperate to gain edge, but watch your rivals");
    those would blur the hostile-words condition, so they stay out."""
    return hostile(msg) and not COOP_WORDS.search(msg)


def collect(corpus: str, model: str) -> dict[str, list[str]]:
    roots = [os.path.join(corpus, "star_runs", f"{model}_star"),
             os.path.join(corpus, "cycle_runs", f"{model}_cycle")]
    pools: dict[str, set[str]] = {"hostile": set(), "cooperative": set()}
    for _, d in discover_records(roots):
        cfg = d["config"]
        if cfg.get("game") != "pd" or cfg.get("condition") != "cheap_talk":
            continue
        s = summarise_run(d)
        cell = cell_label(s["scenario"], s["condition"],
                          cfg.get("message_filter", "none"),
                          bool(cfg.get("topology_aware_comm_prompt", False)),
                          action_labels=cfg.get("action_labels", "standard"))
        kind = {"framing_competitive": "hostile",
                "baseline_cheap_talk": "cooperative"}.get(cell)
        if kind is None:
            continue
        for r in d["history"]:
            for msg in (r.get("messages") or {}).values():
                msg = str(msg).strip()
                if not msg or STAR_WORDS.search(msg):
                    continue
                if kind == "hostile" and purely_hostile(msg):
                    pools[kind].add(msg)
                elif kind == "cooperative" and is_signal(msg) and not hostile(msg):
                    pools[kind].add(msg)
    return {k: sorted(v) for k, v in pools.items()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True, help="Folder holding star_runs/ and cycle_runs/.")
    ap.add_argument("--models", nargs="+", required=True)
    ap.add_argument("--out", default="pools")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    for m in args.models:
        for kind, msgs in collect(args.corpus, m).items():
            if not msgs:
                raise SystemExit(f"{m} {kind}: empty pool -- check --corpus.")
            body = {"model": m, "kind": kind, "n": len(msgs), "messages": msgs}
            sha = hashlib.sha1("\n".join(msgs).encode("utf-8")).hexdigest()[:12]
            body["sha1"] = sha
            path = os.path.join(args.out, f"{m}_{kind}.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump(body, f, ensure_ascii=False, indent=1)
            print(f"{path}: {len(msgs)} messages (sha1 {sha})")


if __name__ == "__main__":
    main()
