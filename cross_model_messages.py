"""Cross-model message content analysis.

Walks all result JSONs, extracts cheap-talk messages, and produces:

  - top_words_per_scenario.csv         lexical fingerprint per (model, scenario)
  - cross_model_lexicon.md             markdown report with top words side-by-side
  - hub_deception_examples.md          actual examples where the hub sent a
                                       cooperative-sounding message and then defected
  - sample_messages.md                 5 random sample messages per (model, scenario)

This file complements cross_model_analysis.py: that one computes numeric
metrics; this one looks at WHAT the agents actually said.

Usage:
    python cross_model_messages.py \
        --roots <root1> <root2> ... \
        --out-dir cross_model_output
"""
from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
from collections import Counter, defaultdict

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cross_model_analysis import (
    discover_records, normalise_model_id,
)
from analysis import scenario_of
from games import GAMES

# NOTE: this script does NOT split results by topology -- star and cycle runs
# of the same (model, scenario) are pooled. That was harmless when only the star
# campaign existed; it is wrong for the current corpus. Split by
# summarise_run()["topology"] before trusting any aggregate produced here.


# Words to ignore when computing top vocabulary.
STOPWORDS = {
    "the", "a", "an", "i", "you", "to", "and", "or", "but", "if", "is",
    "are", "was", "were", "be", "been", "being", "of", "in", "on", "at",
    "for", "with", "as", "by", "from", "this", "that", "it", "we", "they",
    "my", "your", "our", "their", "us", "them", "his", "her", "its", "will",
    "shall", "would", "should", "let", "have", "has", "had", "do", "does",
    "did", "all", "so", "not", "no", "yes", "me", "him", "what", "when",
    "where", "how", "can", "could", "may", "might", "must", "go", "going",
    "than", "then", "also", "here", "there", "into", "out", "up", "down",
    "any", "some", "every", "each", "both", "either", "neither", "more",
    "most", "less", "least", "very", "just", "only", "even", "still", "yet",
    "round", "rounds", "neighbor", "neighbors", "agent", "agents",
}

# Cooperation-signalling words (used to detect "deceptive" hub messages).
COOP_SIGNAL_WORDS = {
    "cooperate", "cooperation", "cooperating", "cooperative", "together",
    "trust", "honest", "mutual", "both", "team", "partner", "partnership",
    "shared", "collaborate", "collaboration", "support", "stag",  # stag is coop in SH
    "commit", "committed", "loyalty", "agreement", "promise",
}


def tokenize(text: str) -> list[str]:
    """Lowercase, split on non-letters, drop stopwords and short tokens."""
    if not text:
        return []
    toks = re.findall(r"[a-zA-Z]+", text.lower())
    return [t for t in toks if len(t) > 2 and t not in STOPWORDS]


def collect_messages(roots: list[str]):
    """Return:
        msgs_by_scenario: {(model, scenario, game): [(sender_role, action, message)]}
        hub_records:      [(model, scenario, game, round, message, action, payoff)]
    """
    msgs_by_scenario: dict[tuple, list[tuple]] = defaultdict(list)
    hub_records: list[dict] = []

    for path, data in discover_records(roots):
        cfg = data.get("config", {})
        model_id = normalise_model_id(cfg.get("model", {}).get("model_id", "unknown"))
        scenario = scenario_of(data)
        game_name = cfg.get("game")
        if game_name not in GAMES:
            continue
        if cfg.get("condition") != "cheap_talk":
            continue
        valid = set(GAMES[game_name].action_labels)
        hub_id = data.get("topology", {}).get("hub_id", 0)

        for r in data.get("history", []):
            actions = r.get("actions", {})
            payoffs = r.get("payoffs", {})
            messages = r.get("messages", {})
            if not messages:
                continue
            rnd = r.get("round", -1)
            for ag_id_str, msg in messages.items():
                try:
                    ag_id = int(ag_id_str)
                except ValueError:
                    continue
                role = "hub" if ag_id == hub_id else "leaf"
                act = actions.get(ag_id_str, actions.get(ag_id))
                if act not in valid:
                    continue
                msgs_by_scenario[(model_id, scenario, game_name)].append(
                    (role, act, msg)
                )
                if role == "hub":
                    hub_records.append({
                        "path": path,
                        "model_id": model_id,
                        "scenario": scenario,
                        "game": game_name,
                        "round": rnd,
                        "message": msg,
                        "action": act,
                        "payoff": payoffs.get(ag_id_str, payoffs.get(ag_id, 0)),
                        "is_coop": act == GAMES[game_name].cooperative_action,
                    })
    return msgs_by_scenario, hub_records


def top_words_per_group(msgs_by_scenario: dict, top_k: int = 10) -> pd.DataFrame:
    rows = []
    for (model, scenario, game), entries in msgs_by_scenario.items():
        counter = Counter()
        for _role, _act, msg in entries:
            counter.update(tokenize(msg))
        n_msgs = len(entries)
        top = counter.most_common(top_k)
        for rank, (word, count) in enumerate(top, start=1):
            rows.append({
                "model_id": model,
                "scenario": scenario,
                "game": game,
                "n_messages": n_msgs,
                "rank": rank,
                "word": word,
                "count": count,
                "freq": count / max(1, n_msgs),
            })
    return pd.DataFrame(rows)


def find_deceptive_hub_messages(hub_records: list[dict], game: str = "pd",
                                max_per_group: int = 5) -> pd.DataFrame:
    """Hub sent a message containing a coop-signal word but then defected."""
    rows = []
    grouped: dict[tuple, list[dict]] = defaultdict(list)
    for r in hub_records:
        if r["game"] != game or r["is_coop"]:
            continue
        msg_low = (r["message"] or "").lower()
        if any(w in msg_low for w in COOP_SIGNAL_WORDS):
            grouped[(r["model_id"], r["scenario"])].append(r)
    for key, recs in grouped.items():
        random.Random(42).shuffle(recs)
        for r in recs[:max_per_group]:
            rows.append({
                "model_id": r["model_id"],
                "scenario": r["scenario"],
                "round": r["round"],
                "message": r["message"],
                "hub_action": r["action"],
                "hub_payoff": r["payoff"],
                "path": os.path.basename(r["path"]),
            })
    return pd.DataFrame(rows)


def sample_messages_per_group(msgs_by_scenario: dict, k: int = 4,
                              seed: int = 7) -> pd.DataFrame:
    rng = random.Random(seed)
    rows = []
    for (model, scenario, game), entries in msgs_by_scenario.items():
        # Stratify by hub vs leaf, coop vs defect when possible.
        bucket: dict[tuple, list[tuple]] = defaultdict(list)
        for role, act, msg in entries:
            if not msg.strip():
                continue
            bucket[(role,)].append((role, act, msg))
        picks = []
        for key, lst in bucket.items():
            rng.shuffle(lst)
            picks.extend(lst[: max(1, k // max(1, len(bucket)))])
        rng.shuffle(picks)
        for role, act, msg in picks[:k]:
            rows.append({
                "model_id": model,
                "scenario": scenario,
                "game": game,
                "role": role,
                "action": act,
                "message": msg,
            })
    return pd.DataFrame(rows)


def write_markdown_lexicon(top_words: pd.DataFrame, out_path: str) -> None:
    lines = ["# Cross-Model Lexical Fingerprint\n\n"]
    lines.append("Top 8 content words per (model, scenario, game). "
                 "Stopwords and `round/neighbor` removed.\n\n")
    for scenario in top_words["scenario"].unique():
        lines.append(f"## Scenario: `{scenario}`\n\n")
        for game in ["pd", "sh"]:
            sub = top_words[(top_words["scenario"] == scenario) &
                            (top_words["game"] == game)]
            if sub.empty:
                continue
            lines.append(f"### Game: {game.upper()}\n\n")
            # Pivot: one column per model, rows = rank
            pivot = sub.pivot_table(
                index="rank", columns="model_id", values="word",
                aggfunc="first",
            ).head(8)
            lines.append(pivot.to_markdown())
            lines.append("\n\n")
    with open(out_path, "w", encoding="utf-8") as f:
        f.writelines(lines)


def write_markdown_deception(decept: pd.DataFrame, out_path: str) -> None:
    lines = ["# Hub Deception Examples (PD only)\n\n"]
    lines.append("Cases where the hub sent a message containing a "
                 "cooperative signal word (`cooperate`, `together`, `mutual`, "
                 "`trust`, `team`, etc.) but then DEFECTED in the same round.\n\n")
    if decept.empty:
        lines.append("_No deceptive messages found._\n")
    else:
        for (model, scenario), sub in decept.groupby(["model_id", "scenario"]):
            lines.append(f"## {model} — {scenario}\n\n")
            for _, r in sub.iterrows():
                lines.append(
                    f"- **Round {r['round']}** (payoff={r['hub_payoff']}, "
                    f"action=`{r['hub_action']}`):  \n"
                    f"  *\"{r['message']}\"*\n\n"
                )
    with open(out_path, "w", encoding="utf-8") as f:
        f.writelines(lines)


def write_markdown_samples(samples: pd.DataFrame, out_path: str) -> None:
    lines = ["# Sample Messages per (model, scenario, game)\n\n"]
    for (model, scenario, game), sub in samples.groupby(["model_id", "scenario", "game"]):
        lines.append(f"## {model} — `{scenario}` — {game.upper()}\n\n")
        for _, r in sub.iterrows():
            lines.append(
                f"- [{r['role']:4s} → {r['action']}] *\"{r['message']}\"*\n"
            )
        lines.append("\n")
    with open(out_path, "w", encoding="utf-8") as f:
        f.writelines(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--roots", nargs="+", required=True)
    ap.add_argument("--out-dir", default="cross_model_output")
    ap.add_argument("--top-k", type=int, default=10)
    args = ap.parse_args()
    os.makedirs(args.out_dir, exist_ok=True)

    print(f"Scanning {len(args.roots)} root(s)...")
    msgs, hub_records = collect_messages(args.roots)
    print(f"  collected {sum(len(v) for v in msgs.values())} total cheap-talk messages")
    print(f"  hub records: {len(hub_records)}")

    print("Computing top words per (model, scenario, game)...")
    top_words = top_words_per_group(msgs, top_k=args.top_k)
    tw_csv = os.path.join(args.out_dir, "top_words_per_scenario.csv")
    top_words.to_csv(tw_csv, index=False)
    print(f"  -> {tw_csv}")

    lex_md = os.path.join(args.out_dir, "cross_model_lexicon.md")
    write_markdown_lexicon(top_words, lex_md)
    print(f"  -> {lex_md}")

    print("Finding deceptive hub messages (PD)...")
    decept = find_deceptive_hub_messages(hub_records, game="pd", max_per_group=5)
    dec_csv = os.path.join(args.out_dir, "hub_deception_examples.csv")
    decept.to_csv(dec_csv, index=False)
    dec_md = os.path.join(args.out_dir, "hub_deception_examples.md")
    write_markdown_deception(decept, dec_md)
    print(f"  -> {dec_csv}")
    print(f"  -> {dec_md}  ({len(decept)} examples)")

    print("Sampling random messages per group...")
    samples = sample_messages_per_group(msgs, k=4)
    sm_md = os.path.join(args.out_dir, "sample_messages.md")
    write_markdown_samples(samples, sm_md)
    print(f"  -> {sm_md}  ({len(samples)} samples)")


if __name__ == "__main__":
    main()
