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

This module is a LIBRARY, not a command. Two functions are its whole public
surface -- `scenario_of(record)` and `summarise_run(record)` -- and six modules
import them, `cross_model_analysis.py` first among them. The single-model CLI
and the keyword analysis that used to live here were removed on 2026-09-20/21;
the note at the foot of the file says why.

    from analysis import summarise_run, scenario_of
"""
from __future__ import annotations

from collections import defaultdict
from statistics import mean

from games import GAMES


# ---------- Loading ----------

def scenario_of(record: dict) -> str:
    """The analysis-level scenario label for one run record.

    Runs produced from 2026-07 onwards carry `config["scenario"]` (the runner's
    label). The runner calls the no-comm + cheap-talk pair a single "baseline"
    scenario, while the analysis wants the two arms as separate cells, so that
    one label is split by condition here.

    Older records have no stored label and are derived from the config. The
    derivation MUST look at context_framing first: a framing_*_context run uses
    message_policy="meaningful", exactly like baseline, so ignoring it silently
    files those runs under baseline -- contaminating the very cell every
    cheap-talk delta is measured against.
    """
    cfg = record["config"]
    cond = cfg["condition"]

    stored = cfg.get("scenario") or ""
    if stored:
        if stored == "baseline":
            return "no_comm" if cond == "no_comm" else "baseline_cheap_talk"
        return stored

    # --- legacy records ---
    ctx = cfg.get("context_framing", "none")
    if ctx and ctx != "none":
        return f"framing_{ctx}_context"
    if cond == "no_comm":
        return "no_comm"
    policy = cfg.get("message_policy", "meaningful")
    if policy == "meaningful":
        return "baseline_cheap_talk"
    if policy in ("no_sense", "irrelevant"):
        return "no_sense"
    if policy == "framing":
        return f"framing_{cfg.get('framing_type', 'unknown')}"
    return policy  # silence, counterfactual


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
    # hub_id exists only in star records; clique/line/cycle have no privileged
    # node, so every hub/leaf metric is NaN for them.
    topo = record["topology"]
    topo_type = topo.get("type", "star")
    hub_id = topo.get("hub_id")
    is_star = hub_id is not None
    n_agents = topo["n_agents"]
    leaf_ids = [i for i in range(n_agents) if i != hub_id] if is_star else []
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
            elif is_star:
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
            elif is_star:
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

    return {
        "run_id": record["run_id"],
        "condition": record["config"]["condition"],
        "game": game_name,
        "topology": topo_type,
        "scenario": scenario_of(record),
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
        "hub_total_payoff": hub_payoff if is_star else float("nan"),
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
    }


# The single-model CLI that used to live here was removed on 2026-09-20.
# Its load_runs() globbed results/{no_comm,cheap_talk}/*.json, a layout the
# runner stopped writing in July (it writes <out>/<scenario>/<condition>/),
# so `python analysis.py --results-dir ...` found zero runs in every current
# tree. This module is a library now: cross_model_analysis.py is the entry
# point, and six modules import summarise_run/scenario_of from here.
#
# Removed with it on 2026-09-21, once nothing called them: aggregate(),
# tokenize(), STOPWORDS and message_content_analysis(), plus the two
# per-run message lists summarise_run kept for that last one -- every
# message of every run, built 1,420 times and read by no one.
