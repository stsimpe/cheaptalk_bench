"""Run ALL 7 cheap-talk scenarios in ONE process for ONE model.

Loads the model exactly once and saves a zip after EACH scenario, so a
mid-run session crash only loses the in-progress scenario's data.

Outputs:
    {out_dir_base}/{scenario}/{condition}/...json
    {out_dir_base}/zips/{scenario}.zip      <-- written as each scenario finishes
    {out_dir_base}/zips/_progress.json      <-- live progress log
    {out_dir_base}/all_results.zip          <-- final combined zip (after all done)
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import time
from datetime import datetime

from config import ExperimentConfig, ModelConfig, DEFAULT_MODELS
from engine import make_engine
from games import ACTION_LABEL_SCHEMES
from llm_client import make_client, preflight_probe, TokenBudgetExceeded


# (label, conditions, message_policy, framing_type, context_framing)
#
# The framing_* scenarios shape only the MESSAGES (message-phase instruction),
# so they exist only under cheap_talk. The framing_*_context scenarios put the
# framing in the SYSTEM prompt instead, which makes framing-without-cheap-talk
# testable: their no_comm arm isolates the effect of the social frame itself,
# and their cheap_talk arm gives the clean framed-context x communication cell.
SCENARIOS: list[tuple[str, list[str], str, str, str]] = [
    ("baseline",            ["no_comm", "cheap_talk"], "meaningful",     "neutral",     "none"),
    ("no_sense",            ["cheap_talk"],            "no_sense",       "neutral",     "none"),
    ("silence",             ["cheap_talk"],            "silence",        "neutral",     "none"),
    ("counterfactual",      ["cheap_talk"],            "counterfactual", "neutral",     "none"),
    ("framing_business",    ["cheap_talk"],            "framing",        "business",    "none"),
    ("framing_team",        ["cheap_talk"],            "framing",        "team",        "none"),
    ("framing_competitive", ["cheap_talk"],            "framing",        "competitive", "none"),
    ("framing_business_context",    ["no_comm", "cheap_talk"], "meaningful", "neutral", "business"),
    ("framing_team_context",        ["no_comm", "cheap_talk"], "meaningful", "neutral", "team"),
    ("framing_competitive_context", ["no_comm", "cheap_talk"], "meaningful", "neutral", "competitive"),
    # Contagion experiment (docs/contagion_plan.md): one scripted source among
    # ordinary agents. The others write ordinary messages, so the policy here
    # is theirs; the source's words and deeds come from SOURCE_SCENARIOS.
    ("source_cc", ["cheap_talk"], "meaningful", "neutral", "none"),
    ("source_hc", ["cheap_talk"], "meaningful", "neutral", "none"),
    ("source_cd", ["cheap_talk"], "meaningful", "neutral", "none"),
    ("source_hd", ["cheap_talk"], "meaningful", "neutral", "none"),
]

# scenario -> (source action, source message pool). The pool file is
# <source-pools>/<model short name>_<pool>.json (build_source_pools.py).
SOURCE_SCENARIOS: dict[str, tuple[str, str]] = {
    "source_cc": ("cooperate", "cooperative"),
    "source_hc": ("cooperate", "hostile"),
    "source_cd": ("defect", "cooperative"),
    "source_hd": ("defect", "hostile"),
}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--provider",
                   choices=["groq", "openai", "huggingface", "openrouter", "local"],
                   default="local")
    p.add_argument("--model-id", default=None)
    p.add_argument("--n-runs", type=int, default=5)
    p.add_argument("--n-rounds", type=int, default=16)
    p.add_argument("--memory-window", type=int, default=10)
    p.add_argument("--n-agents", type=int, default=4)
    p.add_argument("--topology", choices=["star", "clique", "line", "cycle"],
                   default="star",
                   help="Network topology. The star is the original design; "
                        "clique, line and cycle are the RQ2 comparison cases.")
    p.add_argument("--action-retries", type=int, default=0,
                   help="Resample an invalid action up to N times before "
                        "recording it as invalid. Use 1 for the Gemma-2-2B "
                        "cleanup runs.")
    p.add_argument("--message-max-words", type=int, default=20)
    p.add_argument("--temperature", type=float, default=0.7)
    p.add_argument("--max-new-tokens", type=int, default=None,
                   help="Override max output tokens per call. Default 512. "
                        "Lower (e.g. 256) speeds up T4 inference 1.5-2x.")
    p.add_argument("--request-delay", type=float, default=None)
    p.add_argument("--out-dir-base", default="results")
    p.add_argument("--message-filter", default="none",
                   choices=["none", "F1_competitive", "F3_relative_gain",
                            "block_all"],
                   help="RQ4 channel moderation: drop a composed message before "
                        "delivery when it trips the filter. Orthogonal to the "
                        "message policy, so it can be combined with any "
                        "scenario. 'none' reproduces every earlier run.")
    p.add_argument("--topology-aware-comm-prompt", action="store_true",
                   help="Describe message routing from the topology instead of "
                        "the hard-coded star sentence the cheap-talk prompt has "
                        "carried since the first campaign. Off reproduces every "
                        "earlier run byte-for-byte; on is the corrected prompt "
                        "(2026-09 ablation). Runs land in a separate tree.")
    p.add_argument("--silent-topology", action="store_true",
                   help="Say nothing about the network: the topology paragraph "
                        "and the routing sentence are replaced by text with no "
                        "shape and no size (docs/silent_topology_plan.md). "
                        "Both arms are affected. Own tree (suffix _silent).")
    p.add_argument("--allow-legacy-star-prompt", action="store_true",
                   help="Permit a non-star topology WITHOUT the corrected "
                        "prompt, i.e. with the star routing sentence. Only for "
                        "reproducing the pre-2026-09-20 ring grid byte-for-byte; "
                        "without it such a run is refused.")
    p.add_argument("--no-probe", action="store_true")
    p.add_argument("--quick", action="store_true")
    p.add_argument("--games", nargs="+", default=["pd", "sh"],
                   choices=["pd", "sh"],
                   help="Restrict to these games. The default runs both, which "
                        "is what every campaign so far did.")
    p.add_argument("--scenarios", nargs="+", default=None,
                   choices=[s[0] for s in SCENARIOS])
    p.add_argument("--skip-baseline", action="store_true")
    p.add_argument("--hide-own-message", action="store_true",
                   help="Do not quote the agent's own message back to it in "
                        "the action phase. Default off, as in every earlier "
                        "run. Own tree.")
    p.add_argument("--action-labels", default="standard",
                   choices=sorted(ACTION_LABEL_SCHEMES),
                   help="What the agents are told the two actions are called. "
                        "'standard' (Cooperate/Defect, Stag/Hare) is every "
                        "earlier run; 'neutral' shows J/F with the same payoffs. "
                        "The record keeps the game's own labels. Own tree.")
    p.add_argument("--policy-agents", nargs="+", type=int, default=None,
                   help="Apply the scenario's message policy only to these "
                        "agent ids; the others write ordinary messages. "
                        "Default: everyone, as in every earlier campaign. "
                        "Runs land in their own tree.")
    p.add_argument("--conditions", nargs="+", default=None,
                   choices=["no_comm", "cheap_talk"],
                   help="Run only these arms of each scenario. Default: every "
                        "arm, as every campaign so far. Used to add replicates "
                        "to a closed-channel anchor without re-running the open "
                        "arm; a restricted run lands in its own tree.")
    p.add_argument("--source-pools", default=None,
                   help="Folder holding the scripted source's message pools "
                        "(build_source_pools.py). Required by the source_* "
                        "scenarios, ignored by every other one.")
    p.add_argument("--source-agent", type=int, default=0,
                   help="Which agent is the scripted source in the source_* "
                        "scenarios. Default 0, an endpoint of the line.")
    p.add_argument("--zip-after-each", action="store_true", default=True,
                   help="Write a per-scenario zip after each scenario finishes.")
    p.add_argument("--zip-mirror", default=None,
                   help="Extra location to ALSO copy zips to (e.g. /kaggle/working). "
                        "Helps when out-dir-base is somewhere ephemeral.")
    return p.parse_args()


def conditions_tag(conditions: list[str]) -> str:
    """Directory/zip suffix for a run restricted to some arms, e.g. 'nocomm'."""
    return "_".join(c.replace("_", "") for c in sorted(conditions))


def write_progress(progress_path: str, payload: dict) -> None:
    """Atomic-ish JSON write. Survives kill mid-write better than open+write."""
    tmp = progress_path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(payload, f, indent=2)
    os.replace(tmp, progress_path)


def zip_scenario(scenario_dir: str, zip_path: str, mirror: str | None) -> None:
    """Zip a scenario folder. Optionally also copy to a mirror location."""
    if not os.path.exists(scenario_dir):
        return
    shutil.make_archive(zip_path, "zip", scenario_dir)
    print(f"    [zip] saved: {zip_path}.zip")
    if mirror:
        os.makedirs(mirror, exist_ok=True)
        dst = os.path.join(mirror, os.path.basename(zip_path) + ".zip")
        shutil.copy(zip_path + ".zip", dst)
        print(f"    [zip] mirrored to: {dst}")


def main():
    args = parse_args()
    # The prompt bug of 2026-09-20 was this exact combination running silently:
    # a non-star topology with the legacy routing sentence. It is now refused
    # unless asked for by name.
    # The silent prompt describes no routing at all, so it cannot be wrong.
    if (args.topology != "star" and not args.topology_aware_comm_prompt
            and not args.silent_topology and not args.allow_legacy_star_prompt):
        raise SystemExit(
            f"--topology {args.topology} without --topology-aware-comm-prompt would "
            f"tell every agent it sits in a star. Add --topology-aware-comm-prompt, "
            f"or --allow-legacy-star-prompt to reproduce the old ring grid on purpose.")
    model_id = args.model_id or DEFAULT_MODELS[args.provider]

    # Keep non-star data in its own tree so star aggregations never mix in
    # clique/line runs by accident.
    if args.topology != "star" and not args.out_dir_base.endswith(args.topology):
        args.out_dir_base = f"{args.out_dir_base}_{args.topology}"
    # Every earlier campaign had four agents; another size is another network.
    if args.n_agents != 4:
        args.out_dir_base = f"{args.out_dir_base}_n{args.n_agents}"
    # A filtered run is a different experimental cell from its unfiltered twin.
    # Keeping it in a separate tree means a later ingest cannot silently mix
    # the two into one cell, the way the legacy layouts once did.
    if args.message_filter != "none":
        args.out_dir_base = f"{args.out_dir_base}_{args.message_filter}"
    # Same reasoning for the corrected prompt: it is a different prompt
    # generation, and mixing the two inside one cell would be invisible later.
    if args.topology_aware_comm_prompt:
        args.out_dir_base = f"{args.out_dir_base}_commfix"
    # Extra replicates of one arm are the same cell, but a separate tree keeps
    # the session that produced them verifiable on its own, and keeps its zip
    # from overwriting the full session's.
    if args.conditions and set(args.conditions) != {"no_comm", "cheap_talk"}:
        args.out_dir_base = f"{args.out_dir_base}_{conditions_tag(args.conditions)}"
    # One adversarial writer among neutral neighbours is a different cell from
    # the scenario it borrows its policy from, so it gets its own tree too.
    if args.policy_agents is not None:
        args.out_dir_base = (f"{args.out_dir_base}_agents"
                             + "".join(str(a) for a in sorted(args.policy_agents)))
    if args.hide_own_message:
        args.out_dir_base = f"{args.out_dir_base}_hideown"
    # Renamed actions reach the closed arm as well, so a neutral-label tree
    # must never share a folder -- or a no_comm anchor -- with a standard one.
    if args.action_labels != "standard":
        args.out_dir_base = f"{args.out_dir_base}_{args.action_labels}"
    # The silent prompt reaches the closed arm too, so a silent tree must never
    # share a folder, or a no_comm anchor, with an announced one.
    if args.silent_topology:
        args.out_dir_base = f"{args.out_dir_base}_silent"

    if args.request_delay is not None:
        request_delay = args.request_delay
    elif args.provider == "groq":
        request_delay = 3.0
    elif args.provider == "openrouter":
        request_delay = 1.5
    else:
        request_delay = 0.0

    n_runs = 2 if args.quick else args.n_runs
    n_rounds = 8 if args.quick else args.n_rounds

    selected = SCENARIOS
    if args.scenarios:
        selected = [s for s in SCENARIOS if s[0] in args.scenarios]
    if args.skip_baseline:
        selected = [s for s in selected if s[0] != "baseline"]
    if args.conditions:
        selected = [(label, [c for c in conds if c in args.conditions], *rest)
                    for label, conds, *rest in selected]
        dropped = [s[0] for s in selected if not s[1]]
        if dropped:
            raise SystemExit(f"{dropped} have no {args.conditions} arm -- "
                             f"nothing would run for them.")

    # The source pools are Prisoner's Dilemma messages of one model: refuse
    # anything they were not built for before a model is loaded.
    model_short = model_id.split("/")[-1]
    source_cfg: dict[str, dict] = {}
    for label in [s[0] for s in selected if s[0] in SOURCE_SCENARIOS]:
        if args.games != ["pd"]:
            raise SystemExit(f"{label} is a Prisoner's Dilemma cell; pass --games pd.")
        if not args.source_pools:
            raise SystemExit(f"{label} needs --source-pools (build_source_pools.py).")
        if not 0 <= args.source_agent < args.n_agents:
            raise SystemExit(f"--source-agent {args.source_agent} is not one of "
                             f"the {args.n_agents} agents.")
        action, pool = SOURCE_SCENARIOS[label]
        path = os.path.join(args.source_pools, f"{model_short}_{pool}.json")
        if not os.path.exists(path):
            raise SystemExit(f"{label}: no pool at {path} for {model_short}.")
        with open(path, encoding="utf-8") as f:
            body = json.load(f)
        source_cfg[label] = dict(
            source_agent=args.source_agent, source_action=action,
            source_pool=f"{model_short}_{pool}", source_pool_sha=body["sha1"],
            source_pool_file=os.path.abspath(path))

    os.makedirs(args.out_dir_base, exist_ok=True)
    zips_dir = os.path.join(args.out_dir_base, "zips")
    os.makedirs(zips_dir, exist_ok=True)
    progress_path = os.path.join(zips_dir, "_progress.json")

    print(f"=== Model: {args.provider}:{model_id} ===")
    print(f"=== Scenarios: {[s[0] for s in selected]} ===")
    print(f"=== Per scenario: {n_runs} runs x {n_rounds} rounds, games={args.games} ===")
    print(f"=== Output: {args.out_dir_base} ===")
    print(f"=== Per-scenario zips: {zips_dir} ===\n")

    model_cfg_kwargs = dict(
        provider=args.provider,
        model_id=model_id,
        temperature=args.temperature,
        request_delay_s=request_delay,
    )
    if args.max_new_tokens is not None:
        model_cfg_kwargs["max_tokens"] = args.max_new_tokens
    model_cfg = ModelConfig(**model_cfg_kwargs)
    print("=== Loading model... ===")
    t0 = time.time()
    client = make_client(model_cfg)
    print(f"=== Model loaded in {time.time()-t0:.1f}s ===\n")

    if not args.no_probe:
        try:
            preflight_probe(client, model_id, args.provider)
        except TokenBudgetExceeded as e:
            print(f"\n[FAIL-FAST] {e}\n")
            sys.exit(2)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    progress = {
        "started_at": ts, "model": model_id, "scenarios_planned": [s[0] for s in selected],
        "scenarios_done": [], "current_scenario": None, "session_tokens": 0,
    }
    write_progress(progress_path, progress)

    grand_total_runs = 0

    for sc_label, conditions, policy, framing_type, context_framing in selected:
        sc_out_dir = os.path.join(args.out_dir_base, sc_label)
        progress["current_scenario"] = sc_label
        write_progress(progress_path, progress)

        print("\n" + "#" * 70)
        print(f"# SCENARIO: {sc_label}  (policy={policy}"
              f"{', framing=' + framing_type if policy == 'framing' else ''}"
              f"{', context=' + context_framing if context_framing != 'none' else ''})")
        print(f"# Output: {sc_out_dir}")
        print("#" * 70)

        scenario_started_runs = grand_total_runs
        scenario_t0 = time.time()
        for game in args.games:
            for condition in conditions:
                cfg = ExperimentConfig(
                    game=game, condition=condition,
                    topology=args.topology,
                    n_agents=args.n_agents, n_rounds=n_rounds, n_runs=n_runs,
                    memory_window=args.memory_window, model=model_cfg,
                    message_max_words=args.message_max_words,
                    message_policy=policy, framing_type=framing_type,
                    context_framing=context_framing,
                    message_filter=args.message_filter,
                    policy_agents=args.policy_agents,
                    hide_own_message=args.hide_own_message,
                    action_labels=args.action_labels,
                    topology_aware_comm_prompt=args.topology_aware_comm_prompt,
                    silent_topology=args.silent_topology,
                    scenario=sc_label,
                    action_retries=args.action_retries,
                    out_dir=sc_out_dir,
                    **source_cfg.get(sc_label, {}),
                )
                engine = make_engine(cfg)
                cond_dir = os.path.join(sc_out_dir, condition)
                os.makedirs(cond_dir, exist_ok=True)

                print(f"\n  --- {sc_label} | {condition} | game={game} | "
                      f"{n_runs}x{n_rounds} ---")
                for run_id in range(1, n_runs + 1):
                    try:
                        record = engine.run_one(run_id=run_id, client=client)
                    except TokenBudgetExceeded as e:
                        print(f"\n[STOP] {e}")
                        # Try to save what we have so far for this scenario.
                        if args.zip_after_each:
                            zip_scenario(
                                sc_out_dir,
                                os.path.join(zips_dir, sc_label + "_PARTIAL"),
                                args.zip_mirror,
                            )
                        sys.exit(2)
                    cond_short = "nocomm" if condition == "no_comm" else "cheaptalk"
                    fname = f"{ts}_{game}_{cond_short}_run{run_id:02d}.json"
                    with open(os.path.join(cond_dir, fname), "w") as f:
                        json.dump(record, f, indent=2)
                    grand_total_runs += 1
                    tok = getattr(client, 'session_tokens', 0)
                    progress["session_tokens"] = tok
                    progress["last_save"] = os.path.join(cond_dir, fname)
                    write_progress(progress_path, progress)
                    print(f"    saved -> {fname}  (tokens: {tok:,})")

        # Scenario finished -- zip it NOW so a later crash can't lose it.
        runs_in_scenario = grand_total_runs - scenario_started_runs
        if args.zip_after_each:
            zip_scenario(
                sc_out_dir,
                os.path.join(zips_dir, sc_label),
                args.zip_mirror,
            )
        # Record wall time per scenario. Without it, planning how many
        # scenarios fit inside a runtime limit is guesswork -- and a bad guess
        # costs a whole session: the model matters far more than its parameter
        # count suggests, so the only reliable input is what it measured last
        # time.
        scenario_seconds = time.time() - scenario_t0
        progress["scenarios_done"].append({
            "name": sc_label, "runs": runs_in_scenario,
            "tokens_so_far": getattr(client, "session_tokens", 0),
            "seconds": round(scenario_seconds, 1),
            "seconds_per_run": round(scenario_seconds / runs_in_scenario, 1)
            if runs_in_scenario else None,
        })
        progress["current_scenario"] = None
        write_progress(progress_path, progress)
        print(f"  [scenario done] {sc_label}: {runs_in_scenario} runs saved + zipped "
              f"in {scenario_seconds/60:.1f} min "
              f"({scenario_seconds/max(runs_in_scenario,1):.0f} s/run)")

    # All scenarios done -- combined zip
    final_zip = os.path.join(args.out_dir_base, "all_results")
    shutil.make_archive(final_zip, "zip", args.out_dir_base)
    print(f"\n=== Combined zip: {final_zip}.zip ===")
    if args.zip_mirror:
        os.makedirs(args.zip_mirror, exist_ok=True)
        dst = os.path.join(args.zip_mirror, "all_results.zip")
        shutil.copy(final_zip + ".zip", dst)
        print(f"=== Mirrored to: {dst} ===")

    final_tok = getattr(client, "session_tokens", 0)
    elapsed = time.time() - t0
    print(f"\n{'#' * 70}")
    print(f"# DONE: {grand_total_runs} runs across {len(selected)} scenarios.")
    print(f"# Elapsed: {elapsed/60:.1f} min ({elapsed/3600:.2f} h)")
    print(f"# Total tokens: {final_tok:,}")
    print(f"{'#' * 70}")


if __name__ == "__main__":
    main()
