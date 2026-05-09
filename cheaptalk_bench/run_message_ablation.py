"""Message ablation experiment runner.

Tests whether cheap talk's effect depends on message CONTENT or just on
the presence of a communication CHANNEL.

Three policies: meaningful / irrelevant / silence.

Usage:
    python run_message_ablation.py --game pd --policy meaningful
    python run_message_ablation.py --game sh --policy irrelevant
    python run_message_ablation.py --game pd --policy silence
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime

from config import ExperimentConfig, ModelConfig, DEFAULT_MODELS, MessagePolicy
from engine import make_engine
from llm_client import make_client, preflight_probe, TokenBudgetExceeded


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--game", choices=["pd", "sh"], required=True)
    p.add_argument("--policy", choices=["meaningful", "irrelevant", "silence"], required=True)
    p.add_argument("--n-runs", type=int, default=5)
    p.add_argument("--n-rounds", type=int, default=16)
    p.add_argument("--memory-window", type=int, default=10)
    p.add_argument("--n-agents", type=int, default=4)
    p.add_argument("--provider", choices=["groq", "openai", "huggingface", "openrouter", "local"], default="groq")
    p.add_argument("--model-id", default=None)
    p.add_argument("--temperature", type=float, default=0.7)
    p.add_argument("--request-delay", type=float, default=None)
    p.add_argument("--out-dir", default="results")
    p.add_argument("--quick", action="store_true",
                   help="Reduced pilot: 2 runs x 8 rounds.")
    p.add_argument("--no-probe", action="store_true")
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

    cfg = ExperimentConfig(
        game=args.game,
        condition="cheap_talk",
        n_agents=args.n_agents,
        n_rounds=n_rounds,
        n_runs=n_runs,
        memory_window=args.memory_window,
        model=ModelConfig(
            provider=args.provider,
            model_id=model_id,
            temperature=args.temperature,
            request_delay_s=request_delay,
        ),
        message_policy=args.policy,
        out_dir=args.out_dir,
    )
    print(
        f"Provider: {cfg.model.provider} | Model: {cfg.model.model_id} | "
        f"Rounds: {cfg.n_rounds} (memory window: {cfg.memory_window}) | "
        f"Runs: {cfg.n_runs} | Policy: {cfg.message_policy} | "
        f"Throttle: {cfg.model.request_delay_s}s/call"
    )

    client = make_client(cfg.model)
    if not args.no_probe:
        try:
            preflight_probe(client, model_id, cfg.model.provider)
        except TokenBudgetExceeded as e:
            print(f"\n[FAIL-FAST] {e}\n")
            sys.exit(2)
    engine = make_engine(cfg)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = os.path.join(cfg.out_dir, "message_ablation", cfg.message_policy)
    os.makedirs(out_dir, exist_ok=True)

    runs_completed = 0
    for run_id in range(1, cfg.n_runs + 1):
        print(f"\n=== message_ablation | policy={cfg.message_policy} | game={cfg.game} | run {run_id}/{cfg.n_runs} ===")
        try:
            record = engine.run_one(run_id=run_id, client=client)
        except TokenBudgetExceeded as e:
            print(f"\n[STOP] {e}")
            print(f"  Completed {runs_completed}/{cfg.n_runs} run(s) before quota wall.")
            print(f"  Resume tomorrow -- already-saved JSONs in {out_dir} are intact.")
            sys.exit(2)
        fname = f"{ts}_{cfg.game}_{cfg.message_policy}_run{run_id:02d}.json"
        with open(os.path.join(out_dir, fname), "w") as f:
            json.dump(record, f, indent=2)
        runs_completed += 1
        print(f"  saved -> {fname}  (session tokens so far: "
              f"{getattr(client, 'session_tokens', 0):,})")

    print(f"\nDONE: {runs_completed}/{cfg.n_runs} runs completed. "
          f"Total session tokens: {getattr(client, 'session_tokens', 0):,}")


if __name__ == "__main__":
    main()
