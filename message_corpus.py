"""Flatten every logged cheap-talk message into one row, with its context.

This is the substrate for RQ4.  The corpus holds ~58k non-empty messages, and
the question RQ4 asks -- can the channel be modified to keep the coordination
benefit while blocking the harmful shift -- is answerable offline first: which
candidate filter fires often in the cells that harm and rarely in the cells that
help.  Only after that curve exists is it worth spending GPU on an in-the-loop
filtered condition.

Each row is one message, joined to what its sender actually did:

  own_action        the sender's action in the SAME round the message was sent.
                    A cooperative-sounding message paired with a defection is
                    the deception signal; this column is what makes it
                    measurable for every agent, not just the star's hub.
  next_action       the sender's action in the following round.
  n_recipients      how many neighbours actually received it.

Replacement-policy scenarios (no_sense, silence) are kept and flagged via
`message_policy`, because "what a filter would do to a canned message" is a
degenerate case worth seeing rather than silently dropping.

Usage:
    python message_corpus.py --roots <model folders> --out-dir cross_model_output_final
"""
from __future__ import annotations

import argparse
import os
import sys

import pandas as pd


def build(roots: list[str]) -> pd.DataFrame:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from cross_model_analysis import (
        discover_records, normalise_model_id, cell_label,
    )
    from analysis import summarise_run
    from games import GAMES

    rows = []
    n_runs = 0
    for path, data in discover_records(roots):
        cfg = data.get("config", {})
        if cfg.get("condition") != "cheap_talk":
            continue  # no message phase at all
        game_name = cfg.get("game")
        if game_name not in GAMES:
            continue
        summary = summarise_run(data)
        model = normalise_model_id(cfg.get("model", {}).get("model_id", "unknown"))
        cell = cell_label(summary["scenario"], summary["condition"])
        topology = summary["topology"]
        coop = GAMES[game_name].cooperative_action
        n_runs += 1

        history = data.get("history", [])
        # actions[round_index][agent] -> label, for the next_action join
        actions_by_round = [r.get("actions", {}) or {} for r in history]

        for idx, rnd in enumerate(history):
            messages = rnd.get("messages", {}) or {}
            seen_by = rnd.get("messages_seen_by", {}) or {}
            actions = rnd.get("actions", {}) or {}
            invalid = rnd.get("invalid", {}) or {}
            payoffs = rnd.get("payoffs", {}) or {}
            nxt = actions_by_round[idx + 1] if idx + 1 < len(actions_by_round) else {}

            for agent, text in messages.items():
                # how many neighbours had this sender's message in their view
                n_recipients = sum(
                    1 for receiver, seen in seen_by.items()
                    if isinstance(seen, dict) and agent in seen
                )
                own = actions.get(agent)
                rows.append({
                    "model_id": model,
                    "topology": topology,
                    "game": game_name,
                    "cell": cell,
                    "message_policy": cfg.get("message_policy", ""),
                    "framing_type": cfg.get("framing_type", ""),
                    "context_framing": cfg.get("context_framing", "none"),
                    "run_id": summary["run_id"],
                    "round": rnd.get("round", idx + 1),
                    "agent_id": agent,
                    "is_hub": bool(topology == "star" and str(agent) == "0"),
                    "n_recipients": n_recipients,
                    "message": text if isinstance(text, str) else "",
                    "own_action": own,
                    "own_is_coop": (own == coop) if own is not None else None,
                    "own_invalid": bool(invalid.get(agent, False)),
                    "own_payoff": payoffs.get(agent),
                    "next_action": nxt.get(agent),
                    "next_is_coop": (nxt.get(agent) == coop) if agent in nxt else None,
                    "path": path,
                })
    print(f"  {n_runs} cheap-talk runs -> {len(rows)} messages")
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--roots", nargs="+", required=True)
    ap.add_argument("--out-dir", default="cross_model_output_final")
    args = ap.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    df = build(args.roots)
    if df.empty:
        print("No cheap-talk messages found. Check the --roots paths.")
        return

    out = os.path.join(args.out_dir, "message_corpus.csv")
    df.to_csv(out, index=False)
    print(f"-> {out}")

    nonempty = df["message"].fillna("").str.strip().ne("").sum()
    print(f"\n{len(df)} messages, {nonempty} non-empty")
    print(f"models {df['model_id'].nunique()}  topologies {sorted(df['topology'].unique())}"
          f"  games {sorted(df['game'].unique())}  cells {df['cell'].nunique()}")
    print("\nmessages per cell:")
    print(df.groupby(["cell"]).size().sort_values(ascending=False).to_string())


if __name__ == "__main__":
    main()
