"""Analysis aligned with thesis Research Questions.

For each completed run we compute metrics that map to specific RQs:

  RQ1 (Direction):
    - coop_rate_overall: did the system end up cooperative or not?
    - coop_rate_by_game: did the answer differ between PD and SH?
    - cheap_talk_delta: how much did communication shift cooperation
                        (cheap_talk - no_comm) per game?

  RQ2 (Topology):
    - coop_rate_hub vs coop_rate_leaf: hub-vs-leaf cooperation asymmetry
    - hub_total_payoff vs leaf_avg_payoff: who captures the gains?
    - hub_leadership_correlation: does the hub's action in round t-1
      predict the leaves' action in round t? (rough proxy for "hub
      drives the system")
    - hub_exploitation_rate: in cheap-talk PD specifically, how often
      does the hub defect after sending a cooperative-sounding message?

  RQ1 message content (qualitative, cheap-talk only):
    - top_cooperative_keywords: most frequent words in messages of
      rounds where the sender then cooperated
    - keyword_action_correlation: P(cooperate | "stag" in message), etc.

Usage:
    python analysis.py --results-dir results
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
from collections import Counter, defaultdict
from statistics import mean, stdev

import pandas as pd

from games import GAMES


# ---------- Loading ----------

def load_runs(results_dir: str) -> list[dict]:
    """Return list of all run records, each tagged with file path."""
    runs: list[dict] = []
    
    # Baseline experiments
    for condition_dir in ("no_comm", "cheap_talk"):
        pattern = os.path.join(results_dir, condition_dir, "*.json")
        for path in sorted(glob.glob(pattern)):
            with open(path) as f:
                rec = json.load(f)
            rec["_path"] = path
            rec["_experiment_group"] = "baseline"
            runs.append(rec)
    
    # Message ablation experiments
    ablation_root = os.path.join(results_dir, "message_ablation")
    if os.path.exists(ablation_root):
        for policy in ("meaningful", "irrelevant", "silence"):
            pattern = os.path.join(ablation_root, policy, "*.json")
            for path in sorted(glob.glob(pattern)):
                with open(path) as f:
                    rec = json.load(f)
                rec["_path"] = path
                rec["_experiment_group"] = f"ablation_{policy}"
                runs.append(rec)
    
    return runs


# ---------- Per-run summary ----------

def _normalize_dict_keys_to_int(d: dict) -> dict:
    """JSON dumps int keys as strings; restore them for cleaner downstream code."""
    return {int(k) if isinstance(k, str) and k.lstrip("-").isdigit() else k: v
            for k, v in d.items()}


def summarise_run(record: dict) -> dict:
    """Compute per-run aggregate metrics aligned with RQs."""
    game_name = record["config"]["game"]
    game = GAMES[game_name]
    coop_label = game.cooperative_action
    valid_set = set(game.action_labels)
    hub_id = record["topology"]["hub_id"]
    n_agents = record["topology"]["n_agents"]
    leaf_ids = [i for i in range(n_agents) if i != hub_id]
    is_cheap_talk = record["config"]["condition"] == "cheap_talk"

    # Counters
    total_coop = total_valid = 0
    hub_coop = hub_valid = 0
    leaf_coop = leaf_valid = 0
    invalid_count = 0
    all_coop_rounds = 0
    hub_payoff = 0
    leaf_payoffs: list[int] = []
    round_coop_rates: list[float] = []

    # RQ2: hub leadership — for each round t > 1, did leaves match the hub's
    # action from t-1? We average a 0/1 indicator across all leaf-rounds.
    hub_lead_hits = 0
    hub_lead_total = 0

    # RQ2: hub exploitation in PD with cheap talk — hub sends a message
    # mentioning cooperation but then defects.
    hub_exploit_count = 0
    hub_exploit_opportunities = 0

    # RQ1 (qualitative): track messages per agent action
    msgs_when_coop: list[str] = []
    msgs_when_defect: list[str] = []

    history = record["history"]
    n_rounds = len(history)

    prev_hub_action: str | None = None

    for r in history:
        actions = _normalize_dict_keys_to_int(r["actions"])
        payoffs = _normalize_dict_keys_to_int(r["payoffs"])
        round_valid_coop = round_valid_total = 0
        all_coop_this_round = True

        for i, act in actions.items():
            if act not in valid_set:
                invalid_count += 1
                all_coop_this_round = False
                continue
            is_coop = act == coop_label
            total_coop += int(is_coop)
            total_valid += 1
            round_valid_coop += int(is_coop)
            round_valid_total += 1
            if not is_coop:
                all_coop_this_round = False
            if i == hub_id:
                hub_coop += int(is_coop)
                hub_valid += 1
            else:
                leaf_coop += int(is_coop)
                leaf_valid += 1

        if round_valid_total:
            round_coop_rates.append(round_valid_coop / round_valid_total)
        if all_coop_this_round and round_valid_total == n_agents:
            all_coop_rounds += 1

        # Hub leadership: does each leaf's action in round t match the hub's
        # action in round t-1?
        if prev_hub_action is not None and prev_hub_action in valid_set:
            for leaf in leaf_ids:
                leaf_act = actions.get(leaf)
                if leaf_act in valid_set:
                    hub_lead_hits += int(leaf_act == prev_hub_action)
                    hub_lead_total += 1

        prev_hub_action = actions.get(hub_id)

        # Payoffs
        for i, pay in payoffs.items():
            if i == hub_id:
                hub_payoff += pay
            else:
                leaf_payoffs.append(pay)

        # RQ2: hub exploitation (PD + cheap talk only)
        if is_cheap_talk and game_name == "pd":
            messages = _normalize_dict_keys_to_int(r.get("messages", {}))
            hub_msg = messages.get(hub_id, "").lower()
            hub_act = actions.get(hub_id)
            if hub_msg and hub_act in valid_set:
                hub_exploit_opportunities += 1
                # "Exploitation" heuristic: hub message mentions cooperation
                # (or "cooperate"/"work together"/etc.) but hub then defects.
                signals_coop = any(
                    kw in hub_msg
                    for kw in ("cooperate", "cooperation", "together", "trust",
                               "honest", "mutual", "both")
                )
                if signals_coop and hub_act == "Defect":
                    hub_exploit_count += 1

        # RQ1 (qualitative): message-action pairing
        if is_cheap_talk:
            messages = _normalize_dict_keys_to_int(r.get("messages", {}))
            for i, msg in messages.items():
                act = actions.get(i)
                if act not in valid_set:
                    continue
                if act == coop_label:
                    msgs_when_coop.append(msg)
                else:
                    msgs_when_defect.append(msg)

    return {
        "run_id": record["run_id"],
        "condition": record["config"]["condition"],
        "game": game_name,
        "model_id": record["config"]["model"]["model_id"],
        "experiment_group": record.get("_experiment_group", "baseline"),
        "message_policy": record["config"].get("message_policy", "N/A"),
        "n_rounds": n_rounds,
        # RQ1
        "coop_rate_overall": total_coop / total_valid if total_valid else float("nan"),
        # RQ2
        "coop_rate_hub": hub_coop / hub_valid if hub_valid else float("nan"),
        "coop_rate_leaf": leaf_coop / leaf_valid if leaf_valid else float("nan"),
        "hub_minus_leaf_coop": (
            (hub_coop / hub_valid) - (leaf_coop / leaf_valid)
            if hub_valid and leaf_valid else float("nan")
        ),
        "hub_total_payoff": hub_payoff,
        "leaf_avg_payoff": mean(leaf_payoffs) if leaf_payoffs else float("nan"),
        "hub_leadership_rate": (
            hub_lead_hits / hub_lead_total if hub_lead_total else float("nan")
        ),
        "hub_exploitation_rate": (
            hub_exploit_count / hub_exploit_opportunities
            if hub_exploit_opportunities else float("nan")
        ),
        # General
        "invalid_rate": invalid_count / (n_rounds * n_agents) if n_rounds else float("nan"),
        "full_coop_rate": all_coop_rounds / n_rounds if n_rounds else float("nan"),
        "round_coop_rates": round_coop_rates,
        "_msgs_when_coop": msgs_when_coop,
        "_msgs_when_defect": msgs_when_defect,
    }


# ---------- Cross-run aggregation ----------

def aggregate(summaries: list[dict]) -> dict:
    """Aggregate (mean, sd) over multiple runs of same condition+game+model."""
    if not summaries:
        return {}
    keys = [
        "coop_rate_overall",
        "coop_rate_hub",
        "coop_rate_leaf",
        "hub_minus_leaf_coop",
        "hub_total_payoff",
        "leaf_avg_payoff",
        "hub_leadership_rate",
        "hub_exploitation_rate",
        "invalid_rate",
        "full_coop_rate",
    ]
    out = {"n_runs": len(summaries)}
    for k in keys:
        vals = [s[k] for s in summaries if s[k] == s[k]]  # drop NaN
        out[k + "_mean"] = mean(vals) if vals else float("nan")
        out[k + "_sd"] = stdev(vals) if len(vals) > 1 else 0.0
    return out


# ---------- RQ1 message content analysis ----------

STOPWORDS = {
    "the", "a", "an", "i", "you", "to", "and", "or", "but", "if", "is",
    "are", "was", "were", "be", "been", "being", "of", "in", "on", "at",
    "for", "with", "as", "by", "from", "this", "that", "it", "we", "they",
    "my", "your", "our", "will", "shall", "would", "should", "let", "us",
    "have", "has", "had", "do", "does", "did", "all", "so", "not", "no",
    "yes", "me", "him", "her", "them", "what", "when", "where", "how",
}


def tokenize(text: str) -> list[str]:
    """Lowercase, split on non-letters, drop stopwords and 1-letter tokens."""
    tokens = re.findall(r"[a-zA-Z]+", text.lower())
    return [t for t in tokens if len(t) > 1 and t not in STOPWORDS]


def message_content_analysis(msgs_coop: list[str], msgs_defect: list[str], top_k: int = 10) -> dict:
    """Frequencies of words in messages preceding cooperate vs defect."""
    coop_counter = Counter(tok for m in msgs_coop for tok in tokenize(m))
    def_counter = Counter(tok for m in msgs_defect for tok in tokenize(m))

    # Words that signal cooperation: high relative frequency in coop msgs.
    n_coop = sum(coop_counter.values()) or 1
    n_def = sum(def_counter.values()) or 1

    coop_freq = {w: c / n_coop for w, c in coop_counter.most_common(50)}
    def_freq = {w: def_counter.get(w, 0) / n_def for w in coop_freq}

    # Lift = P(word | coop) / P(word | defect). High lift = strong coop signal.
    lift_scores = []
    for w, fc in coop_freq.items():
        fd = def_freq.get(w, 0)
        lift = fc / fd if fd > 0 else float("inf")
        lift_scores.append((w, fc, fd, lift, coop_counter[w]))

    # Sort by raw count in coop msgs, but show lift too.
    lift_scores.sort(key=lambda x: -x[4])
    top_words = lift_scores[:top_k]

    return {
        "n_coop_msgs": len(msgs_coop),
        "n_defect_msgs": len(msgs_defect),
        "top_coop_words": [
            {
                "word": w,
                "count_in_coop": c_count,
                "freq_in_coop": round(fc, 3),
                "freq_in_defect": round(fd, 3),
                "lift": round(lift, 2) if lift != float("inf") else "inf",
            }
            for w, fc, fd, lift, c_count in top_words
        ],
    }


# ---------- Main ----------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results-dir", default="results")
    args = ap.parse_args()

    runs = load_runs(args.results_dir)
    if not runs:
        print(f"No runs found under {args.results_dir}/{{no_comm,cheap_talk}}/")
        return

    # Per-run summaries
    summaries = [summarise_run(r) for r in runs]

    # Group by (condition, game, model) and aggregate
    groups: dict[tuple, list[dict]] = defaultdict(list)
    for s in summaries:
        groups[(s["condition"], s["game"], s["model_id"])].append(s)

    rows = []
    for (cond, game, model), summs in sorted(groups.items()):
        agg = aggregate(summs)
        row = {"condition": cond, "game": game, "model_id": model, **agg}
        rows.append(row)

    df = pd.DataFrame(rows)
    pd.set_option("display.float_format", lambda x: f"{x:0.3f}")

    # ---------- RQ1 main table: cheap talk effect by game ----------
    print("\n=== RQ1: Direction × Game structure ===")
    print("(Did cheap talk push toward cooperation, and does it depend on PD vs SH?)\n")
    cols_rq1 = [
        "condition", "game", "model_id", "n_runs",
        "coop_rate_overall_mean", "coop_rate_overall_sd",
        "full_coop_rate_mean",
    ]
    print(df[cols_rq1].to_string(index=False))

    # ---------- RQ2 main table: hub vs leaf asymmetry ----------
    print("\n=== RQ2: Topology — hub vs leaf asymmetry ===")
    print("(Does the hub behave differently from leaves? Does cheap talk amplify it?)\n")
    cols_rq2 = [
        "condition", "game", "model_id",
        "coop_rate_hub_mean", "coop_rate_leaf_mean", "hub_minus_leaf_coop_mean",
        "hub_total_payoff_mean", "leaf_avg_payoff_mean",
        "hub_leadership_rate_mean", "hub_exploitation_rate_mean",
    ]
    print(df[cols_rq2].to_string(index=False))

    # ---------- Cheap-talk Δ (RQ1, headline number) ----------
    print("\n=== Headline: cheap talk Δ in cooperation ===")
    for game in ("pd", "sh"):
        no_comm = df[(df["condition"] == "no_comm") & (df["game"] == game)]
        ct = df[(df["condition"] == "cheap_talk") & (df["game"] == game)]
        if not no_comm.empty and not ct.empty:
            delta = ct["coop_rate_overall_mean"].iloc[0] - no_comm["coop_rate_overall_mean"].iloc[0]
            print(f"  {game.upper()}: no_comm={no_comm['coop_rate_overall_mean'].iloc[0]:.1%} "
                  f"→ cheap_talk={ct['coop_rate_overall_mean'].iloc[0]:.1%}  "
                  f"(Δ = {delta:+.1%})")

    # ---------- RQ1 message content (cheap talk only) ----------
    print("\n=== RQ1: Message content analysis (cheap talk runs only) ===")
    for game in ("pd", "sh"):
        ct_summs = [s for s in summaries
                    if s["condition"] == "cheap_talk" and s["game"] == game]
        if not ct_summs:
            continue
        all_coop_msgs = [m for s in ct_summs for m in s["_msgs_when_coop"]]
        all_def_msgs = [m for s in ct_summs for m in s["_msgs_when_defect"]]
        if not all_coop_msgs and not all_def_msgs:
            continue
        analysis = message_content_analysis(all_coop_msgs, all_def_msgs)
        print(f"\n  {game.upper()}: {analysis['n_coop_msgs']} coop msgs, "
              f"{analysis['n_defect_msgs']} defect msgs")
        print("  Top words preceding cooperation:")
        for w in analysis["top_coop_words"][:8]:
            lift = w["lift"]
            print(f"    {w['word']:15s} count={w['count_in_coop']:3d}  "
                  f"P(w|coop)={w['freq_in_coop']:.3f}  "
                  f"P(w|defect)={w['freq_in_defect']:.3f}  "
                  f"lift={lift}")

    # ---------- Save aggregated CSV ----------
    out_path = os.path.join(args.results_dir, "aggregated_metrics.csv")
    df.to_csv(out_path, index=False)
    print(f"\n→ Aggregated metrics saved to {out_path}")


if __name__ == "__main__":
    main()
