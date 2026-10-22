"""Round-1 replay of the harm-source action calls (docs/replay_plan.md).

Every call to a model is stateless, so a first-round action call can be rebuilt
exactly from its run record and asked again with one part of it changed. No
game is played: the history of round 1 is empty, so the edited text is the
only difference between variants.

Contexts (PD, star, framing_competitive, harm-source trees):
  writer   block-all runs: the agent's own hostile message is quoted back to
           it, nothing is delivered
  reader   withheld-quotation runs: the agent's own message is hidden, its
           neighbours' hostile messages are delivered
  silence  block-all runs with the quotation withheld: recorded round-1
           actions only, the corpus value of W2

Variants:
  W0  writer, unchanged                      (reproduces the recorded round 1)
  W1  writer, action words deleted from its own message
  W2  writer, no quotation                   (silence: the reference of both routes)
  S1  writer, the same text shown as a neighbour's message instead of its own
  R0  reader, unchanged
  R1  reader, action words deleted from the received messages
  D0..D2  hub readers only: 0, 1 or 2 of the 3 received messages hostile, the
          rest replaced by first-round cooperative messages of the same model
          (pools/<model>_cooperative_r1.json; D3 is R0)

Usage:
    # once, locally: the round-1 contexts, committed as replay/contexts.json
    python replay.py extract --roots ../harm_source --out replay/contexts.json
    # per model, on a GPU
    python replay.py run --model Qwen/Qwen2.5-7B-Instruct --out replay_out/Qwen2.5-7B-Instruct.jsonl
    python replay.py run --model ... --dry-run     # list contexts and variants, call nothing
"""
from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import os
import random
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import ExperimentConfig, ModelConfig  # noqa: E402
from cross_model_analysis import discover_records, normalise_model_id  # noqa: E402

ACTION_WORD = re.compile(r"\b(defect\w*|cooperat\w*)\b", re.I)
HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CONTEXTS = os.path.join(HERE, "replay", "contexts.json")


def strip_action_words(text: str) -> str:
    """Delete every form of the two action words, then tidy the spacing.
    A message without them comes back as it was, character for character."""
    if not ACTION_WORD.search(str(text)):
        return str(text)
    t = ACTION_WORD.sub("", str(text))
    t = re.sub(r"\s+([,.;:!?])", r"\1", t)
    t = re.sub(r"([,;:])\s*([,.;:!?])", r"\2", t)
    t = re.sub(r"\s{2,}", " ", t).strip()
    return re.sub(r"^[,.;:!?\s]+", "", t)


def to_config(cfg: dict) -> ExperimentConfig:
    """The run's own configuration, as the engine that produced it read it."""
    fields = {f.name for f in dataclasses.fields(ExperimentConfig)}
    kw = {k: v for k, v in cfg.items() if k in fields and k != "model"}
    mfields = {f.name for f in dataclasses.fields(ModelConfig)}
    kw["model"] = ModelConfig(**{k: v for k, v in cfg["model"].items() if k in mfields})
    return ExperimentConfig(**kw)


def _kind(cfg: dict) -> str | None:
    if cfg.get("game") != "pd" or cfg.get("scenario") != "framing_competitive":
        return None
    if cfg.get("topology", "star") != "star" or cfg.get("policy_agents") is not None:
        return None
    filt = cfg.get("message_filter") or "none"
    hide = bool(cfg.get("hide_own_message"))
    return {("block_all", False): "writer", ("none", True): "reader",
            ("block_all", True): "silence"}.get((filt, hide))


def extract(roots: list[str], out: str):
    contexts, sources = [], []
    for path, d in discover_records(roots):
        cfg = d["config"]
        kind = _kind(cfg)
        if kind is None:
            continue
        with open(path, "rb") as f:
            sources.append({"file": os.path.relpath(path, os.path.commonpath(roots)).replace(os.sep, "/"),
                            "sha1": hashlib.sha1(f.read()).hexdigest()})
        r1 = d["history"][0]
        composed = r1.get("messages_composed") or r1.get("messages") or {}
        hub = str(d["topology"].get("hub_id", 0))
        for agent in sorted(r1["actions"], key=int):
            contexts.append({
                "kind": kind, "model": normalise_model_id(cfg["model"]["model_id"]),
                "run": os.path.basename(path), "run_id": d["run_id"], "agent": int(agent),
                "hub": agent == hub, "recorded": r1["actions"][agent],
                "own": composed.get(agent, "") if kind == "writer" else "",
                "received": [[int(k), v] for k, v in r1["messages_seen_by"][agent].items()],
                "cfg": cfg,
            })
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"sources": sorted(sources, key=lambda s: s["file"]), "contexts": contexts},
                  f, ensure_ascii=False, indent=1)
    from collections import Counter
    for (m, k), n in sorted(Counter((c["model"], c["kind"]) for c in contexts).items()):
        print(f"  {m:24s} {k:8s} {n:3d} contexts")
    print(f"{len(contexts)} contexts from {len(sources)} runs -> {out}")


def variants(ctx: dict, coop_pool: list[str]) -> list[tuple[str, str, dict, int | None]]:
    """(variant, own message, received messages, number of hostile received)."""
    own, rec = ctx["own"], dict((k, v) for k, v in ctx["received"])
    if ctx["kind"] == "writer":
        first = min(rec) if rec else None
        as_neighbour = {k: (own if k == first else v) for k, v in rec.items()}
        return [("W0", own, rec, None), ("W1", strip_action_words(own), rec, None),
                ("W2", "", rec, None), ("S1", "", as_neighbour, None)]
    out = [("R0", "", rec, len(rec)),
           ("R1", "", {k: strip_action_words(v) for k, v in rec.items()}, len(rec))]
    if ctx["hub"] and len(rec) == 3:
        senders = sorted(rec)
        for k in range(3):
            # Which senders stay hostile, and which cooperative messages fill
            # the rest, fixed per context and dose.
            # No line twice in one context: two leaves never send the same words.
            rng = random.Random(f"{ctx['run']}|{ctx['agent']}|D{k}")
            keep = set(rng.sample(senders, k))
            fill = iter(rng.sample(coop_pool, 3 - k))
            out.append((f"D{k}", "", {s: (rec[s] if s in keep else next(fill))
                                      for s in senders}, k))
    return out


def seed_of(*parts) -> int:
    return int(hashlib.sha1("|".join(map(str, parts)).encode()).hexdigest()[:8], 16)


def run(args):
    with open(args.contexts, encoding="utf-8") as f:
        allc = json.load(f)["contexts"]
    model = normalise_model_id(args.model)
    ctxs = [c for c in allc if c["model"] == model and c["kind"] in ("writer", "reader")]
    n_w = sum(c["kind"] == "writer" for c in ctxs)
    n_r = sum(c["kind"] == "reader" for c in ctxs)
    if not n_w or not n_r:
        raise SystemExit(f"{model}: {n_w} writer and {n_r} reader contexts in {args.contexts}")
    short = args.model.split("/")[-1]
    with open(os.path.join(args.pools, f"{short}_cooperative_r1.json"), encoding="utf-8") as f:
        coop_pool = json.load(f)["messages"]
    jobs = [(c, v) for c in ctxs for v in variants(c, coop_pool)]
    print(f"{args.model}: {n_w} writer and {n_r} reader contexts, "
          f"{len(jobs)} context-variants x {args.samples} samples = {len(jobs) * args.samples} calls")
    budgets = {c["cfg"]["model"]["max_tokens"] for c in ctxs}
    assert len(budgets) == 1, f"the contexts disagree on max_tokens: {budgets}"
    if args.dry_run:
        shown = set()
        for c, (name, own, rec, _) in jobs:
            if (c["kind"], name, c["hub"]) in shown:
                continue
            shown.add((c["kind"], name, c["hub"]))
            print(f"\n[{c['kind']} {name}] agent {c['agent']}{' (hub)' if c['hub'] else ''}"
                  f"\n  own:      {own!r}\n  received: {rec}")
        return

    done = set()
    if os.path.exists(args.out):
        with open(args.out, encoding="utf-8") as f:
            for line in f:
                r = json.loads(line)
                done.add((r["run"], r["agent"], r["variant"], r["sample"]))
        print(f"resuming: {len(done)} calls already in {args.out}")
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)

    from engine import make_engine
    from llm_client import make_client
    try:
        import torch
    except ImportError:
        torch = None
    client = make_client(to_config(ctxs[0]["cfg"]).model)
    agents = {}
    n = 0
    with open(args.out, "a", encoding="utf-8") as out:
        for c, (name, own, rec, hostile) in jobs:
            key = (c["run"], c["agent"])
            if key not in agents:
                engine = make_engine(to_config(c["cfg"]))
                agents[key] = engine.build_agents(client, run_id=c["run_id"])[c["agent"]]
            agent = agents[key]
            for s in range(args.samples):
                if (c["run"], c["agent"], name, s) in done:
                    continue
                if torch is not None:
                    torch.manual_seed(seed_of(c["run"], c["agent"], name, s))
                action, reasoning = agent.choose_action_cheap_talk([], 1, own, rec)
                calls = agent.drain_calls()
                out.write(json.dumps({
                    "model": model, "kind": c["kind"], "run": c["run"], "agent": c["agent"],
                    "hub": c["hub"], "variant": name, "sample": s, "n_hostile": hostile,
                    "action": action, "valid": action in ("Cooperate", "Defect"),
                    "recorded": c["recorded"], "own": own,
                    "received": [[k, v] for k, v in rec.items()],
                    "finish": [k.get("finish_reason") for k in calls],
                    "reasoning": str(reasoning)[:300],
                }, ensure_ascii=False) + "\n")
                out.flush()
                n += 1
            print(f"  {c['kind']} {c['run']} agent {c['agent']} {name}: done", flush=True)
    print(f"{n} new calls -> {args.out}")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    ex = sub.add_parser("extract", help="Round-1 contexts from the harm-source trees.")
    ex.add_argument("--roots", nargs="+", required=True)
    ex.add_argument("--out", default=DEFAULT_CONTEXTS)
    rn = sub.add_parser("run", help="Ask one model again, every context and variant.")
    rn.add_argument("--model", required=True, help="HuggingFace id, as in the run records.")
    rn.add_argument("--contexts", default=DEFAULT_CONTEXTS)
    rn.add_argument("--pools", default=os.path.join(HERE, "pools"),
                    help="Cooperative pools for the dose variants.")
    rn.add_argument("--samples", type=int, default=5)
    rn.add_argument("--out", required=True)
    rn.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    if args.cmd == "extract":
        extract(args.roots, args.out)
    else:
        run(args)


if __name__ == "__main__":
    main()
