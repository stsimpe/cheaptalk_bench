"""Run ALL 7 cheap-talk scenarios in ONE process for ONE model.

Loads the model exactly once (huge time-saver vs running run_full_sweep.py
seven times -- saves ~2 min x 6 = 12 min of reload + cold-start overhead).

Scenarios executed in order:
  1. baseline             : no_comm + cheap_talk(meaningful)   [pd, sh]
  2. no_sense             : cheap_talk(no_sense)                [pd, sh]
  3. silence              : cheap_talk(silence)                 [pd, sh]
  4. counterfactual       : cheap_talk(counterfactual)          [pd, sh]
  5. framing_business     : cheap_talk(framing, business)       [pd, sh]
  6. framing_team         : cheap_talk(framing, team)           [pd, sh]
  7. framing_competitive  : cheap_talk(framing, competitive)    [pd, sh]

Each scenario writes JSONs into:
    {out_dir_base}/{scenario}/no_comm/   (only baseline; other scenarios skip no_comm)
    {out_dir_base}/{scenario}/cheap_talk/

Total LLM calls per model (5 runs x 16 rounds defaults):
  - baseline       : 64 + 128 = 192 calls/game x 2 games = 1,920 calls
  - no_sense       :   0 (template replacement, no LLM)
  - silence        :   0 (empty message, no LLM)
  - counterfactual : 128 calls/game x 2 = 1,280 calls
  - framing x 3    : 1,280 calls each x 3 = 3,840 calls
  TOTAL per model  : ~7,040 calls. On a T4 with 7B in 4-bit, ~5-6 hours.

Usage:
    # Smoke test (2x8, all 7 scenarios, ~10-15 min)
    python run_all_scenarios.py --provider local \
        --model-id Qwen/Qwen2.5-7B-Instruct \
        --out-dir-base results/qwen-2.5-7b --quick

    # Full sweep, all 7 scenarios
    python run_all_scenarios.py --provider local \
        --model-id Qwen/Qwen2.5-7B-Instruct \
        --out-dir-base results/qwen-2.5-7b

    # Skip baseline if already done in a previous session
    python run_all_scenarios.py --provider local \
        --model-id Qwen/Qwen2.5-7B-Instruct \
        --out-dir-base results/qwen-2.5-7b --skip-baseline
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime

from config import ExperimentConfig, ModelConfig, DEFAULT_MODELS
from engine import make_engine
from llm_client import make_client, preflight_probe, TokenBudgetExceeded


# Scenario manifest. Each tuple: (label, conditions, message_policy, framing_type).
SCENARIOS: list[tuple[str, list[str], str, str]] = [
    ("baseline",            ["no_comm", "cheap_talk"], "meaningful",     "neutral"),
    ("no_sense",            ["cheap_talk"],            "no_sense",       "neutral"),
    ("silence",             ["cheap_talk"],            "silence",        "neutral"),
    ("counterfactual",      ["cheap_talk"],            "counterfactual", "neutral"),
    ("framing_business",    ["cheap_talk"],            "framing",        "business"),
    ("framing_team",        ["cheap_talk"],            "framing",        "team"),
    ("framing_competitive", ["cheap_talk"],            "framing",        "competitive"),
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
    p.add_argument("--message-max-words", type=int, default=20)
    p.add_argument("--temperature", type=float, default=0.7)
    p.add_argument("--request-delay", type=float, default=None)
    p.add_argument("--out-dir-base", default="results",
                   help="Each scenario gets a subfolder under this dir.")
    p.add_argument("--no-probe", action="store_true")
    p.add_argument("--quick", action="store_true",
                   help="Reduced pilot: 2 runs x 8 rounds for smoke testing.")
    p.add_argument("--scenarios", nargs="+", default=None,
                   choices=[s[0] for s in SCENARIOS],
                   help="Only run these scenarios (default: all 7).")
    p.add_argument("--skip-baseline", action="store_true",
                   help="Skip the baseline scenario if you've already run it.")
    return p.parse_args()


def main():
    args = parse_args()
    model_id = args.model_id or DEFAULT_MODELS[args.provider]
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

    # Filter scenarios
    selected = SCENARIOS
    if args.scenarios:
        selected = [s for s in SCENARIOS if s[0] in args.scenarios]
    if args.skip_baseline:
        selected = [s for s in selected if s[0] != "baseline"]

    print(f"=== Model: {args.provider}:{model_id} ===")
    print(f"=== Scenarios planned: {[s[0] for s in selected]} ===")
    print(f"=== Per scenario: {n_runs} runs x {n_rounds} rounds, games=[pd,sh] ===\n")

    # BUILD CLIENT ONCE (this is the main reason this script exists).
    model_cfg = ModelConfig(
        provider=args.provider,
        model_id=model_id,
        temperature=args.temperature,
        request_delay_s=request_delay,
    )
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
    grand_total_runs = 0

    for sc_label, conditions, policy, framing_type in selected:
        sc_out_dir = os.path.join(args.out_dir_base, sc_label)
        print("\n" + "#" * 70)
        print(f"# SCENARIO: {sc_label}  (policy={policy}"
              f"{', framing=' + framing_type if policy == 'framing' else ''})")
        print(f"# Output: {sc_out_dir}")
        print("#" * 70)

        for game in ["pd", "sh"]:
            for condition in conditions:
                cfg = ExperimentConfig(
                    game=game,
                    condition=condition,
                    n_agents=args.n_agents,
                    n_rounds=n_rounds,
                    n_runs=n_runs,
                    memory_window=args.memory_window,
                    model=model_cfg,
                    message_max_words=args.message_max_words,
                    message_policy=policy,
                    framing_type=framing_type,
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
                        print(f"  Already saved: {grand_total_runs} runs total.")
                        sys.exit(2)
                    cond_short = "nocomm" if condition == "no_comm" else "cheaptalk"
                    fname = f"{ts}_{game}_{cond_short}_run{run_id:02d}.json"
                    with open(os.path.join(cond_dir, fname), "w") as f:
                        json.dump(record, f, indent=2)
                    grand_total_runs += 1
                    tok = getattr(client, 'session_tokens', 0)
                    print(f"    saved -> {fname}  (tokens: {tok:,})")

    final_tok = getattr(client, 'session_tokens', 0)
    elapsed = time.time() - t0
    print(f"\n{'#' * 70}")
    print(f"# DONE: {grand_total_runs} total runs across {len(selected)} scenarios.")
    print(f"# Elapsed: {elapsed/60:.1f} min ({elapsed/3600:.2f} h)")
    print(f"# Total tokens: {final_tok:,}")
    print(f"{'#' * 70}")


if __name__ == "__main__":
    main()
