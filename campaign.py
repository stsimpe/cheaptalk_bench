"""One-command campaign launcher for Kaggle.

Why this exists: the Kaggle notebook executes the copy of the cells living in
your Kaggle workspace, NOT the notebook stored in this repo. A `git pull` in a
notebook cell therefore updates this code but never the cells themselves, so a
bug in a cell survives every fix until you hand-edit the notebook. Keeping the
whole campaign here means the notebook is a two-line launcher that never needs
touching again:

    import subprocess, sys
    subprocess.run([sys.executable, "campaign.py",
                    "--model", "google/gemma-2-2b-it", "--session", "A"], check=True)

What it does:
  1. resolves the per-model / per-session parameters of the campaign plan
  2. runs run_all_scenarios.py with them
  3. verifies the runs that were actually produced (count + topology)
  4. zips the results for download

Exit codes: 0 success, 2 the sweep failed, 3 the output failed verification.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import shlex
import shutil
import subprocess
import sys
import time
from collections import Counter


# Scenario groups. Session A is the four "core" scenarios, session B the three
# framings; splitting them keeps every session inside the Kaggle time budget.
SESSION_SCENARIOS: dict[str, list[str]] = {
    "A": ["baseline", "no_sense", "silence", "counterfactual"],
    "B": ["framing_business", "framing_team", "framing_competitive"],
    "ALL": ["baseline", "no_sense", "silence", "counterfactual",
            "framing_business", "framing_team", "framing_competitive"],
    # Session C is the framing-without-cheap-talk control. The framing_*
    # scenarios of session B shape only the MESSAGES, so they exist solely
    # under cheap_talk and cannot separate "the frame changed behaviour" from
    # "the frame changed the messages, and the messages changed behaviour".
    # These put the frame in the system prompt instead, so each one runs a
    # no_comm arm as well -- twice the cells of session B, hence the cost.
    "C": ["framing_business_context", "framing_team_context",
          "framing_competitive_context"],
}

# max_new_tokens per model, per session, copied from the star campaign so a
# star-vs-<topology> comparison carries no extra confound. These are NOT tidy
# on purpose -- they are what the existing 380 runs used.
MAX_NEW_TOKENS: dict[str, dict[str, int]] = {
    "meta-llama/Llama-3.1-8B-Instruct": {"A": 192, "B": 192},
    "Qwen/Qwen2.5-7B-Instruct":         {"A": 512, "B": 256},
    "Qwen/Qwen3-4B":                    {"A": 256, "B": 256},
    "google/gemma-2-2b-it":             {"A": 256, "B": 192},
    "google/gemma-2-9b-it":             {"A": 160, "B": 192},
}

def _conditions_per_scenario() -> dict[str, int]:
    """How many condition arms each scenario runs, read from the runner itself.

    Derived rather than hardcoded: baseline and the framing_*_context
    scenarios run both a no_comm and a cheap_talk arm, everything else only
    cheap_talk. A hardcoded copy silently under-counts the moment a scenario
    gains an arm, and an under-count makes verification reject a perfectly
    good session.
    """
    from run_all_scenarios import SCENARIOS
    return {label: len(conditions) for label, conditions, *_ in SCENARIOS}


def expected_runs(scenarios: list[str], n_runs: int) -> int:
    """Every scenario is (arms x 2 games x n_runs) run files."""
    arms = _conditions_per_scenario()
    return sum(arms[s] * 2 * n_runs for s in scenarios)


def plan(model: str, session: str, topology: str, n_runs: int,
         n_rounds: int, out_root: str, max_new_tokens: int | None = None,
         only: list[str] | None = None) -> dict:
    if session not in SESSION_SCENARIOS:
        raise SystemExit(f"Unknown session {session!r}; choose from {sorted(SESSION_SCENARIOS)}")
    if max_new_tokens is None:
        if model not in MAX_NEW_TOKENS:
            raise SystemExit(
                f"No max_new_tokens on record for {model!r}. Pass --max-new-tokens "
                f"explicitly, or add the model to MAX_NEW_TOKENS in campaign.py.\n"
                f"Known models: {sorted(MAX_NEW_TOKENS)}"
            )
        # "ALL" and "C" use the session-A value: A and C both send ordinary
        # (message_policy="meaningful") messages, so they inherit the cap the
        # star baseline used. Only the session-B framings differ, for the
        # models whose star framing runs used a smaller cap.
        key = "A" if session in ("ALL", "C") else session
        max_new_tokens = MAX_NEW_TOKENS[model][key]

    scenarios = SESSION_SCENARIOS[session]
    if only:
        unknown = [s for s in only if s not in scenarios]
        if unknown:
            raise SystemExit(
                f"{unknown} are not part of session {session} ({scenarios}). "
                f"Pick the session that owns them, or fix the spelling."
            )
        scenarios = [s for s in scenarios if s in only]  # keep the canonical order
    short = model.split("/")[-1]
    out_dir_base = os.path.join(out_root, short)
    # run_all_scenarios.py appends the topology suffix itself for non-star runs.
    result_dir = out_dir_base if topology == "star" else f"{out_dir_base}_{topology}"
    return {
        "model": model, "session": session, "topology": topology,
        "scenarios": scenarios, "n_runs": n_runs, "n_rounds": n_rounds,
        "max_new_tokens": max_new_tokens,
        "out_dir_base": out_dir_base, "result_dir": result_dir,
        "expected_runs": expected_runs(scenarios, n_runs),
        "zip_base": os.path.join(out_root, "..", f"{short}_{topology}_session{session}"),
    }


def build_cmd(p: dict, zip_mirror: str | None) -> list[str]:
    cmd = [
        sys.executable, "run_all_scenarios.py",
        "--provider", "local",
        "--model-id", p["model"],
        "--topology", p["topology"],
        "--n-runs", str(p["n_runs"]),
        "--n-rounds", str(p["n_rounds"]),
        "--max-new-tokens", str(p["max_new_tokens"]),
        "--out-dir-base", p["out_dir_base"],
        "--no-probe",
    ]
    if zip_mirror:
        cmd += ["--zip-mirror", zip_mirror]
    cmd += ["--scenarios", *p["scenarios"]]
    return cmd


def verify(result_dir: str, expected: int, topology: str,
           scenarios: list[str] | None = None) -> tuple[bool, dict]:
    """Check what was actually produced: count, topology, and scenario labels.

    Each record now carries config["scenario"], so the label it claims can be
    cross-checked against the directory it landed in and against what was
    requested. That catches a run written under the wrong scenario before the
    data reaches the analysis, where a mislabelled framing_*_context run would
    quietly merge into baseline.
    """
    files = [f for f in glob.glob(os.path.join(result_dir, "**", "*.json"), recursive=True)
             if not os.path.basename(f).startswith("_progress")]
    per_scenario: Counter = Counter()
    topologies: Counter = Counter()
    unreadable: list[str] = []
    mislabelled: list[str] = []
    for f in files:
        try:
            with open(f, encoding="utf-8") as fh:
                rec = json.load(fh)
            topologies[rec["topology"]["type"]] += 1
            folder = os.path.relpath(f, result_dir).split(os.sep)[0]
            per_scenario[folder] += 1
            recorded = rec["config"].get("scenario", "")
            if recorded and recorded != folder:
                mislabelled.append(f"{f}: records {recorded!r}, sits in {folder!r}")
        except Exception:
            unreadable.append(f)

    unexpected = sorted(set(per_scenario) - set(scenarios)) if scenarios else []
    missing = sorted(set(scenarios) - set(per_scenario)) if scenarios else []

    report = {"found": len(files), "expected": expected,
              "per_scenario": dict(per_scenario), "topologies": dict(topologies),
              "unreadable": unreadable, "mislabelled": mislabelled,
              "unexpected_scenarios": unexpected, "missing_scenarios": missing}
    ok = (bool(files)
          and not unreadable
          and not mislabelled
          and not unexpected
          and not missing
          and set(topologies) == {topology}
          and len(files) == expected)
    return ok, report


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", required=True, help="HuggingFace model id")
    ap.add_argument("--session", default="A", choices=sorted(SESSION_SCENARIOS))
    ap.add_argument("--topology", default="cycle",
                    choices=["star", "clique", "line", "cycle"])
    ap.add_argument("--n-runs", type=int, default=5)
    ap.add_argument("--n-rounds", type=int, default=16)
    ap.add_argument("--max-new-tokens", type=int, default=None,
                    help="Override the per-model value from the campaign table.")
    ap.add_argument("--out-root", default="/kaggle/working/results")
    ap.add_argument("--zip-mirror", default="/kaggle/working")
    ap.add_argument("--scenarios", nargs="+", default=None,
                    help="Run only these scenarios from the session. Needed when a "
                         "whole session does not fit in the runtime limit, and to "
                         "resume after a session is killed part-way: pass the "
                         "scenarios that have not been produced yet.")
    ap.add_argument("--dry-run", action="store_true",
                    help="Print the plan and the command, run nothing.")
    args = ap.parse_args()

    p = plan(args.model, args.session, args.topology, args.n_runs,
             args.n_rounds, args.out_root, args.max_new_tokens, args.scenarios)
    cmd = build_cmd(p, args.zip_mirror)

    print("=" * 70)
    print(f"model        : {p['model']}")
    print(f"session {p['session']:<4} : {p['scenarios']}")
    print(f"topology     : {p['topology']}  (runs={p['n_runs']} rounds={p['n_rounds']} "
          f"max_new_tokens={p['max_new_tokens']})")
    print(f"expecting    : {p['expected_runs']} run files")
    print(f"results ->   : {p['result_dir']}")
    print("=" * 70)
    print("RUN:", " ".join(shlex.quote(c) for c in cmd), flush=True)

    if args.dry_run:
        print("\n[dry-run] nothing executed.")
        return 0

    t0 = time.time()
    rc = subprocess.run(cmd).returncode
    elapsed = time.time() - t0
    print(f"\nsweep exit code {rc} after {elapsed/60:.1f} min ({elapsed/3600:.2f} h)")
    if rc != 0:
        print("[FAIL] the sweep failed; nothing will be packaged.")
        return 2

    ok, report = verify(p["result_dir"], p["expected_runs"], p["topology"],
                        p["scenarios"])
    print(f"\nruns found : {report['found']}  (expected {report['expected']})")
    print(f"topologies : {report['topologies']}")
    for k in sorted(report["per_scenario"]):
        print(f"   {k:<24} {report['per_scenario'][k]} runs")
    if report["unreadable"]:
        print(f"[FAIL] {len(report['unreadable'])} unreadable file(s): "
              f"{report['unreadable'][:3]}")
    if report["missing_scenarios"]:
        print(f"[FAIL] no runs at all for: {report['missing_scenarios']}")
    if report["unexpected_scenarios"]:
        print(f"[FAIL] runs for scenarios that were not requested: "
              f"{report['unexpected_scenarios']} -- is this directory reused "
              f"from an earlier session?")
    if report["mislabelled"]:
        print(f"[FAIL] {len(report['mislabelled'])} run(s) record a scenario "
              f"that disagrees with their directory: {report['mislabelled'][:3]}")
    if not ok:
        print("[FAIL] output did not verify -- not packaging. "
              "Check the scenario counts above.")
        return 3

    zip_base = os.path.normpath(p["zip_base"])
    shutil.make_archive(zip_base, "zip", p["result_dir"])
    size_mb = os.path.getsize(zip_base + ".zip") / 1e6
    print(f"\n[OK] download this: {zip_base}.zip  ({size_mb:.1f} MB)")
    print(f"[OK] wall time {elapsed/3600:.2f} h -- note it in TRACK_RECORD.md "
          f"to recalibrate the remaining estimates.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
