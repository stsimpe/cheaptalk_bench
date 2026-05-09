"""Run all 4 conditions (no_comm + cheap_talk x pd + sh) for ONE model.

Designed for local/GPU inference where loading the model is expensive
(e.g. Kaggle T4 takes 1-3 min to load a 7B model). We build the client
ONCE, then iterate over all (game, condition) combinations in the same
Python process so the model stays warm in VRAM.

Saves results to:
    {out_dir}/no_comm/{ts}_{game}_nocomm_run{NN}.json
    {out_dir}/cheap_talk/{ts}_{game}_cheaptalk_run{NN}.json

Usage examples (each scenario is one command, run separately per model):

    # Baseline cheap-talk (default meaningful messages):
    python run_full_sweep.py --provider local \
        --model-id Qwen/Qwen2.5-7B-Instruct \
        --out-dir results/qwen-2.5-7b/baseline

    # No-sense (channel-only ablation):
    python run_full_sweep.py --provider local \
        --model-id Qwen/Qwen2.5-7B-Instruct \
        --message-policy no_sense --conditions cheap_talk \
        --out-dir results/qwen-2.5-7b/no_sense

    # Counterfactual messages:
    python run_full_sweep.py --provider local \
        --model-id Qwen/Qwen2.5-7B-Instruct \
        --message-policy counterfactual --conditions cheap_talk \
        --out-dir results/qwen-2.5-7b/counterfactual

    # Framing (business / team / competitive):
    python run_full_sweep.py --provider local \
        --model-id Qwen/Qwen2.5-7B-Instruct \
        --message-policy framing --framing-type business --conditions cheap_talk \
        --out-dir results/qwen-2.5-7b/framing_business

    # Smoke test (fits in ~5 min):
    python run_full_sweep.py --provider local --quick \
        --out-dir results/smoke
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime

from config import ExperimentConfig, ModelConfig, DEFAULT_MODELS
from engine import make_engine
from llm_client import make_client, preflight_probe, TokenBudgetExceeded


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--provider",
                   choices=["groq", "openai", "huggingface", "openrouter", "local"],
                   default="local")
    p.add_argument("--model-id", default=None,
                   help="Defaults to canonical model for the chosen provider.")
    p.add_argument("--n-runs", type=int, default=5)
    p.add_argument("--n-rounds", type=int, default=16)
    p.add_argument("--memory-window", type=int, default=10)
    p.add_argument("--n-agents", type=int, default=4)
    p.add_argument("--message-max-words", type=int, default=20)
    p.add_argument("--temperature", type=float, default=0.7)
    p.add_argument("--request-delay", type=float, default=None)
    p.add_argument("--out-dir", default="results")
    p.add_argument("--no-probe", action="store_true",
                   help="Skip preflight smoke-test call.")
    p.add_argument("--quick", action="store_true",
                   help="Reduced pilot: 2 runs x 8 rounds.")
    p.add_argument("--games", nargs="+", default=["pd", "sh"],
                   choices=["pd", "sh"])
    p.add_argument("--conditions", nargs="+",
                   default=["no_comm", "cheap_talk"],
                   choices=["no_comm", "cheap_talk"])
    # ---- Cheap-talk message-content controls (only applied when
    #      "cheap_talk" is in --conditions). Default policy is "meaningful".
    p.add_argument("--message-policy",
                   choices=["meaningful", "irrelevant", "no_sense",
                            "silence", "counterfactual", "framing"],
                   default="meaningful",
                   help="Cheap-talk message-content policy. See "
                        "message_policies.py for full descriptions.")
    p.add_argument("--framing-type",
                   choices=["business", "team", "competitive", "neutral"],
                   default="business",
                   help="Sub-knob for --message-policy framing.")
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

    print(f"=== Building client for {args.provider}:{model_id} ===")
    if "cheap_talk" in args.conditions:
        if args.message_policy == "framing":
            print(f"=== Cheap-talk policy: framing ({args.framing_type}) ===")
        else:
            print(f"=== Cheap-talk policy: {args.message_policy} ===")

    model_cfg = ModelConfig(
        provider=args.provider,
        model_id=model_id,
        temperature=args.temperature,
        request_delay_s=request_delay,
    )
    client = make_client(model_cfg)

    if not args.no_probe:
        try:
            preflight_probe(client, model_id, args.provider)
        except TokenBudgetExceeded as e:
            print(f"\n[FAIL-FAST] {e}\n")
            sys.exit(2)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    total_runs_done = 0
    total_runs_planned = len(args.games) * len(args.conditions) * n_runs

    for game in args.games:
        for condition in args.conditions:
            cfg = ExperimentConfig(
                game=game,
                condition=condition,
                n_agents=args.n_agents,
                n_rounds=n_rounds,
                n_runs=n_runs,
                memory_window=args.memory_window,
                model=model_cfg,
                message_max_words=args.message_max_words,
                message_policy=args.message_policy,
                framing_type=args.framing_type,
                out_dir=args.out_dir,
            )
            engine = make_engine(cfg)
            cond_dir = os.path.join(cfg.out_dir, condition)
            os.makedirs(cond_dir, exist_ok=True)

            print("\n" + "=" * 60)
            print(f"=== {condition} | game={game} | "
                  f"{n_runs} runs x {n_rounds} rounds ===")
            print("=" * 60)

            for run_id in range(1, n_runs + 1):
                print(f"\n--- run {run_id}/{n_runs} "
                      f"({total_runs_done + 1}/{total_runs_planned} overall) ---")
                try:
                    record = engine.run_one(run_id=run_id, client=client)
                except TokenBudgetExceeded as e:
                    print(f"\n[STOP] {e}")
                    print(f"  Completed {total_runs_done}/{total_runs_planned} "
                          f"runs total before quota wall.")
                    sys.exit(2)

                cond_short = "nocomm" if condition == "no_comm" else "cheaptalk"
                fname = f"{ts}_{game}_{cond_short}_run{run_id:02d}.json"
                with open(os.path.join(cond_dir, fname), "w") as f:
                    json.dump(record, f, indent=2)
                total_runs_done += 1
                tok = getattr(client, 'session_tokens', 0)
                print(f"  saved -> {fname}  "
                      f"(session tokens: {tok:,}, runs: {total_runs_done}/{total_runs_planned})")

    final_tok = getattr(client, 'session_tokens', 0)
    print(f"\n=== DONE: {total_runs_done}/{total_runs_planned} runs completed. "
          f"Total session tokens: {final_tok:,} ===")


if __name__ == "__main__":
    main()
