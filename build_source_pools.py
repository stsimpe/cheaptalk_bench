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
about its network. Messages with wording about the game's length
(verify_prompts' horizon pattern: "final round", "16 rounds", ...) are
dropped as well, so the source never hints at the horizon; none of the pools
committed before 2026-11-21 holds one, so the rule removes nothing from them.

With --first-round, only the cooperative pool, from round 1 alone
(`<model>_cooperative_r1.json`): the replay of docs/replay_plan.md puts these
messages into first-round contexts, where a line like "let's keep
cooperating" would point to a past that does not exist.

With --roots, the result trees given are read in place of the corpus layout,
for one model: the lab server's grids live elsewhere. The Qwen3.5-122B-A10B
pools came from its star grid at the 4096 cap, and rebuild byte for byte with
--roots <pharos_runs>/tok4096/grid/Qwen3.5-122B-A10B.

Usage:
    python build_source_pools.py --corpus <diplomatikh folder> \
        --models Qwen2.5-7B-Instruct Llama-3.1-8B-Instruct --out pools
    python build_source_pools.py ... --first-round
    python build_source_pools.py --roots <pharos_runs>/tok4096/grid/Qwen3.8-27B-FP8 \
        --models Qwen3.8-27B-FP8 --out pools
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
# The same pattern as verify_prompts.HORIZON.
HORIZON = re.compile(r'\b16 rounds|\bof 16\b|sixteen|total (number of )?rounds|'
                     r'final round|rounds remain|remaining rounds', re.I)
F1 = MESSAGE_FILTERS["F1_competitive"]


COOP_WORDS = re.compile(r"cooperat|collaborat|together|mutual|trust|partner", re.I)


def hostile(msg: str) -> bool:
    return bool(F1 & set(re.findall(r"[a-z']+", msg.lower())))


def purely_hostile(msg: str) -> bool:
    """Competitive register and no word of cooperation. The competitive cells
    also hold mixed lines ("Cooperate to gain edge, but watch your rivals");
    those would blur the hostile-words condition, so they stay out."""
    return hostile(msg) and not COOP_WORDS.search(msg)


def collect(corpus: str | None, model: str, first_round: bool = False,
            roots: list[str] | None = None) -> dict[str, list[str]]:
    if roots is None:
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
                          action_labels=cfg.get("action_labels", "standard"),
                          silent_topology=bool(cfg.get("silent_topology", False)))
        kind = {"framing_competitive": "hostile",
                "baseline_cheap_talk": "cooperative"}.get(cell)
        if kind is None:
            continue
        for r in d["history"][:1] if first_round else d["history"]:
            for msg in (r.get("messages") or {}).values():
                msg = str(msg).strip()
                if not msg or STAR_WORDS.search(msg) or HORIZON.search(msg):
                    continue
                if kind == "hostile" and purely_hostile(msg):
                    pools[kind].add(msg)
                elif kind == "cooperative" and is_signal(msg) and not hostile(msg):
                    pools[kind].add(msg)
    return {k: sorted(v) for k, v in pools.items()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", help="Folder holding star_runs/ and cycle_runs/.")
    ap.add_argument("--roots", nargs="+", default=None,
                    help="Result trees to read instead of the corpus layout (one model).")
    ap.add_argument("--models", nargs="+", required=True)
    ap.add_argument("--out", default="pools")
    ap.add_argument("--first-round", action="store_true",
                    help="Only the cooperative pool, from round 1 (suffix _r1).")
    args = ap.parse_args()
    if (args.corpus is None) == (args.roots is None):
        raise SystemExit("Give either --corpus or --roots.")
    if args.roots and len(args.models) != 1:
        raise SystemExit("--roots holds one model's runs: give one name to --models.")
    os.makedirs(args.out, exist_ok=True)
    for m in args.models:
        pools = collect(args.corpus, m, args.first_round, args.roots)
        if args.first_round:
            pools = {"cooperative_r1": pools["cooperative"]}
        for kind, msgs in pools.items():
            if not msgs:
                raise SystemExit(f"{m} {kind}: empty pool -- check --corpus or --roots.")
            body = {"model": m, "kind": kind, "n": len(msgs), "messages": msgs}
            sha = hashlib.sha1("\n".join(msgs).encode("utf-8")).hexdigest()[:12]
            body["sha1"] = sha
            path = os.path.join(args.out, f"{m}_{kind}.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump(body, f, ensure_ascii=False, indent=1)
            print(f"{path}: {len(msgs)} messages (sha1 {sha})")


if __name__ == "__main__":
    main()
