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
]


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
    p.add_argument("--no-probe", action="store_true")
    p.add_argument("--quick", action="store_true")
    p.add_argument("--scenarios", nargs="+", default=None,
                   choices=[s[0] for s in SCENARIOS])
    p.add_argument("--skip-baseline", action="store_true")
    p.add_argument("--zip-after-each", action="store_true", default=True,
                   help="Write a per-scenario zip after each scenario finishes.")
    p.add_argument("--zip-mirror", default=None,
                   help="Extra location to ALSO copy zips to (e.g. /kaggle/working). "
                        "Helps when out-dir-base is somewhere ephemeral.")
    return p.parse_args()


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
    model_id = args.model_id or DEFAULT_MODELS[args.provider]

    # Keep non-star data in its own tree so star aggregations never mix in
    # clique/line runs by accident.
    if args.topology != "star" and not args.out_dir_base.endswith(args.topology):
        args.out_dir_base = f"{args.out_dir_base}_{args.topology}"

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

    os.makedirs(args.out_dir_base, exist_ok=True)
    zips_dir = os.path.join(args.out_dir_base, "zips")
    os.makedirs(zips_dir, exist_ok=True)
    progress_path = os.path.join(zips_dir, "_progress.json")

    print(f"=== Model: {args.provider}:{model_id} ===")
    print(f"=== Scenarios: {[s[0] for s in selected]} ===")
    print(f"=== Per scenario: {n_runs} runs x {n_rounds} rounds, games=[pd,sh] ===")
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
        for game in ["pd", "sh"]:
            for condition in conditions:
                cfg = ExperimentConfig(
                    game=game, condition=condition,
                    topology=args.topology,
                    n_agents=args.n_agents, n_rounds=n_rounds, n_runs=n_runs,
                    memory_window=args.memory_window, model=model_cfg,
                    message_max_words=args.message_max_words,
                    message_policy=policy, framing_type=framing_type,
                    context_framing=context_framing,
                    action_retries=args.action_retries,
                    out_dir=sc_out_dir,
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
        progress["scenarios_done"].append({
            "name": sc_label, "runs": runs_in_scenario,
            "tokens_so_far": getattr(client, "session_tokens", 0),
        })
        progress["current_scenario"] = None
        write_progress(progress_path, progress)
        print(f"  [scenario done] {sc_label}: {runs_in_scenario} runs saved + zipped")

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
