"""The line of eight: scripted and LLM sources, read by docs/line_n8_plan.md.

Reads PD cheap-talk runs on a line: the natural line and the four scripted
sources of session SRC (docs/contagion_plan.md), and the LLM sources at
agent 0 run with --policy-agents 0 (framing_competitive and framing_team of
session B, the manipulator of session MANIP, docs/manipulator_plan.md).
Every table is per model and per line length, so the line of six
(2026-11-02) and the line of eight never mix.

Description, for every model and length:
  - cooperation by distance d from agent 0, every cell;
  - agent 0: its cooperation, the share of its messages that signal
    cooperation (signal_rules.is_signal), the share of those signals followed
    by Defect in the same round, and its points per round;
  - agent 1 in rounds 1-5 and 12-16;
  - the F1 share of written messages by distance, and the median round of
    the first defection.

Rules of the plan, read on one length (--n-agents, default 8):
  2-4, sanity  contagion_report's R1-R3 and sanity, over --models (one model:
               its margins, no verdict)
  5  manipulation check (per model)
  6  harm beside the manipulator, against the scripted liar (per model)
  7  reach of each LLM source, against the natural line (per model)
  8  does it pay: agent 0's points per round (descriptive)
  9  the nearest scripted cell of each LLM source (descriptive)
  length  the line of eight against the line of six at d = 1-4, for a model
          with both under --roots (descriptive)
A rule is read only when the cells it needs hold 5 runs.

Runs with two models in the line (config `agent_models`) are left out:
liar_victim_report.py reads them (docs/line_n8_liar_victim_plan.md).

Usage:
    python line_report.py --roots <trees> [--models <ids>] [--n-agents 8] [--csv out.csv]
"""
from __future__ import annotations

import argparse
import os
import re
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from contagion_report import distances, hostile, rule_r1, rule_r2, rule_r3, sanity  # noqa: E402
from cross_model_analysis import discover_records, normalise_model_id  # noqa: E402
from signal_rules import is_signal  # noqa: E402

SRC_CELLS = ["baseline", "source_cc", "source_hc", "source_cd", "source_hd"]
SOURCE_CELLS = ["source_hc", "source_cd", "source_hd"]
LLM_CELLS = {"framing_competitive": "llm_competitive", "framing_team": "llm_team",
             "framing_manipulative_context": "llm_manipulator"}
CELLS = SRC_CELLS + list(LLM_CELLS.values())
NAMES = {"baseline": "natural line", "source_cc": "control", "source_hc": "loud",
         "source_cd": "liar", "source_hd": "open enemy", "llm_competitive": "competitive LLM",
         "llm_team": "team LLM", "llm_manipulator": "manipulator"}
MARGIN = 0.10
RUNS = 5
# Margins are compared after rounding away float noise: a gap of exactly 0.10
# (0.30 - 0.40 = -0.10000000000000003) is not "more than 0.10".
EPS_DIGITS = 9


def short(model: str) -> str:
    m = re.search(r"(\d+(?:\.\d+)?B)\b", model)
    return m.group(1) if m else model


def f2(v: float) -> str:
    """Two decimals as the tables print them (pandas rounds half to even)."""
    return f"{np.round(v, 2):.2f}"


def _get(d: dict, agent: int):
    """Run records key agents by string after a JSON round trip."""
    return d.get(str(agent), d.get(agent))


def _mean(xs):
    xs = list(xs)
    return sum(xs) / len(xs) if xs else float("nan")


def cell_of(cfg: dict) -> str | None:
    sc = cfg.get("scenario", "")
    if sc in SRC_CELLS:
        return None if cfg.get("policy_agents") else sc
    if sc in LLM_CELLS and cfg.get("policy_agents") == [0]:
        return LLM_CELLS[sc]
    return None


# ---------------------------------------------------------------- collection

def collect(roots: list[str]) -> pd.DataFrame:
    rows = []
    for path, d in discover_records(roots):
        cfg, topo = d["config"], d["topology"]
        if topo.get("type") != "line" or cfg.get("game") != "pd" or cfg.get("condition") != "cheap_talk":
            continue
        if cfg.get("agent_models"):
            continue
        cell = cell_of(cfg)
        if cell is None:
            continue
        model = normalise_model_id(cfg.get("model", {}).get("model_id", "?"))
        n, hist = topo["n_agents"], d["history"]
        for agent, dd in distances(topo["edges"], n, 0).items():
            acts, writes, first_def = [], [], None
            for r in hist:
                a = _get(r["actions"], agent)
                if a in ("Cooperate", "Defect") and not _get(r.get("invalid") or {}, agent):
                    acts.append(a == "Cooperate")
                    if a == "Defect" and first_def is None:
                        first_def = r["round"]
                msg = _get(r.get("messages") or {}, agent)
                if msg:
                    writes.append(hostile(msg))
            row = {"model": model, "n": n, "cell": cell, "run": os.path.basename(path), "d": dd,
                   "coop": _mean(acts), "coop_early": _mean(acts[:5]), "coop_late": _mean(acts[-5:]),
                   "n_msgs": len(writes), "f1_hits": sum(writes), "first_defect": first_def}
            if dd == 0:
                said = [(str(_get(r.get("messages") or {}, 0) or "").strip(), _get(r["actions"], 0))
                        for r in hist]
                signals = [a for m, a in said if m and is_signal(m)]
                row.update(msgs0=sum(1 for m, _ in said if m), signals=len(signals),
                           broken=sum(1 for a in signals if a == "Defect"),
                           points=_mean(float(_get(r["payoffs"], 0)) for r in hist))
            rows.append(row)
    return pd.DataFrame(rows)


def coop_runs(df, cell, d, model) -> list[float]:
    s = df[(df.cell == cell) & (df.d == d) & (df.model == model)]
    return s["coop"].tolist()


def n_runs(df, model, cell) -> int:
    return df[(df.model == model) & (df.cell == cell)]["run"].nunique()


# ---------------------------------------------------------------- the LLM rules

def manipulation_check(df, model) -> dict:
    s = df[(df.model == model) & (df.cell == "llm_manipulator") & (df.d == 0)]
    sig_share = s.signals.sum() / max(1, s.msgs0.sum())
    broken_share = s.broken.sum() / max(1, s.signals.sum())
    return {"signals": int(s.signals.sum()), "msgs": int(s.msgs0.sum()), "broken": int(s.broken.sum()),
            "sig_share": sig_share, "broken_share": broken_share,
            "passed": round(sig_share, EPS_DIGITS) >= 0.50 and round(broken_share, EPS_DIGITS) >= 0.25}


def harm_vs_liar(df, model) -> dict:
    m = _mean(coop_runs(df, "llm_manipulator", 1, model))
    liar = _mean(coop_runs(df, "source_cd", 1, model))
    gap = round(m - liar, EPS_DIGITS)
    verdict = ("more harm than the liar" if gap < -MARGIN else
               "less harm than the liar" if gap > MARGIN else "comparable to the liar")
    return {"manip": m, "liar": liar, "gap": gap, "verdict": verdict}


def reach_vs_natural(df, cell, model, dmax) -> dict:
    diffs = {d: round(_mean(coop_runs(df, cell, d, model)) - _mean(coop_runs(df, "baseline", d, model)),
                      EPS_DIGITS)
             for d in range(1, dmax + 1)}
    reach = 0
    for d in range(1, dmax + 1):
        if not diffs[d] < -MARGIN:
            break
        reach = d
    return {"diffs": diffs, "reach": reach}


def nearest(df, cell, model, dmax) -> dict:
    prof = {c: [_mean(coop_runs(df, c, d, model)) for d in range(1, dmax + 1)] for c in [cell] + SRC_CELLS}
    mad = {c: _mean(abs(a - b) for a, b in zip(prof[cell], prof[c])) for c in SRC_CELLS}
    return {"mad": mad, "nearest": min(mad, key=mad.get)}


# ---------------------------------------------------------------- report

def describe(df, model, n):
    s = df[(df.model == model) & (df.n == n)]
    cells = [c for c in CELLS if c in set(s.cell)]
    runs = s.groupby("cell")["run"].nunique()
    print(f"\n######## {model}, line of {n}  (runs: "
          + ", ".join(f"{c} {runs[c]}" for c in cells) + ")")
    t = s.groupby(["cell", "d"])["coop"].mean().unstack("d").reindex(cells)
    print("\ncooperation by distance from agent 0 (mean of run means; d = 0 is agent 0)")
    print(t.round(2).to_string())
    a0 = s[s.d == 0].groupby("cell").agg(coop=("coop", "mean"), msgs=("msgs0", "sum"),
                                         signals=("signals", "sum"), broken=("broken", "sum"),
                                         points=("points", "mean")).reindex(cells)
    print("\nagent 0: cooperation, signals of cooperation in its messages, signals broken in the "
          "same round, points per round")
    for c, r in a0.iterrows():
        sig = r.signals / r.msgs if r.msgs else float("nan")
        brk = r.broken / r.signals if r.signals else float("nan")
        print(f"  {c:<16} coop {r.coop:.2f}   signals {int(r.signals)}/{int(r.msgs)} = {sig:.0%}   "
              f"broken {int(r.broken)} = {brk:.0%}   points {r.points:.2f}")
    a1 = s[s.d == 1].groupby("cell").agg(early=("coop_early", "mean"), late=("coop_late", "mean")).reindex(cells)
    print("\nagent 1, rounds 1-5 -> rounds 12-16: "
          + "; ".join(f"{c} {r.early:.2f} -> {r.late:.2f}" for c, r in a1.iterrows()))
    f1 = s[s.d > 0].groupby(["cell", "d"]).agg(h=("f1_hits", "sum"), m=("n_msgs", "sum"))
    f1 = (f1.h / f1.m.where(f1.m > 0)).unstack("d").reindex(cells)
    print("\nF1 share of the messages written at distance d")
    print(f1.round(2).to_string())
    fd = s[s.d > 0].groupby(["cell", "d"])["first_defect"].median().unstack("d").reindex(cells)
    print("\nmedian round of the first defection at distance d (blank: no defection)")
    print(fd.to_string(na_rep=""))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--roots", nargs="+", required=True)
    ap.add_argument("--models", nargs="+", default=None,
                    help="Models the contagion rules read together (default: every model on the line).")
    ap.add_argument("--n-agents", type=int, default=8, help="The line length the rules read.")
    ap.add_argument("--csv", default=None)
    args = ap.parse_args()
    df = collect(args.roots)
    if df.empty:
        raise SystemExit("No line runs of the plan's cells under --roots.")
    for model in sorted(df.model.unique()):
        for n in sorted(df[df.model == model].n.unique()):
            describe(df, model, n)
    if args.csv:
        (df.groupby(["model", "n", "cell", "d"])
           .agg(runs=("run", "nunique"), coop=("coop", "mean"), f1_hits=("f1_hits", "sum"),
                msgs=("n_msgs", "sum"), first_defect=("first_defect", "median"))
           .reset_index().to_csv(args.csv, index=False))
        print(f"\n-> {args.csv}")

    n = args.n_agents
    dmax = n - 1
    dn = df[df.n == n]
    present = sorted(dn.model.unique())
    models = args.models or present
    missing = [m for m in models if m not in present]
    if missing:
        raise SystemExit(f"No line of {n} for {missing}.")
    tag = {m: short(m) for m in models}
    print(f"\n================ the rules, line of {n}; models: {', '.join(models)}")

    # ---- rules 2-4 and sanity: the contagion rules, over the models together
    short_cells = [f"{tag[m]} {c}: {n_runs(dn, m, c)}" for m in models for c in SRC_CELLS
                   if n_runs(dn, m, c) < RUNS]
    if short_cells:
        print(f"\n[rules 2-4 not read] they need {RUNS} runs of every SRC cell; short: "
              + ", ".join(short_cells))
    else:
        # With one model (the 9B read on its own) the margins are shown and no
        # verdict is given: the rules need every one of two models or more.
        verdict = len(models) >= 2
        if not verdict:
            print("\n[rules 2-4: margins only] one model gives no verdict; these rules need two models or more.")
        src = dn[dn.model.isin(models) & dn.cell.isin(SRC_CELLS)]
        print("\n=== Rule 2 (R1, reach): harm against source_cc, > 0.10 in every model, "
              f"Holm p < 0.05 over d = 1-{dmax} ===")
        for cell in SOURCE_CELLS:
            r = rule_r1(src, cell, models, dmax)
            for d in r["diffs"]:
                marg = ", ".join(f"{tag[m]} {v:+.2f}" for m, v in r["diffs"][d].items())
                print(f"  {cell}  d={d}: {marg}   Holm p={r['p_holm'][d]:.3f}"
                      + (f"  {'PASS' if r['passed'][d] else '-'}" if verdict else ""))
            if verdict:
                print(f"  -> reach of the {NAMES[cell]}: {r['reach']}")
        r = rule_r2(src, models)
        print("\n=== Rule 3 (R2, words or deeds at d = 1) ===")
        for m, (liar, loud) in r["harm"].items():
            print(f"  {tag[m]}: harm of the liar {liar:+.2f}, of the loud source {loud:+.2f}")
        if verdict:
            print(f"  pooled p (deeds) = {r['p_deeds']:.3f}, p (words) = {r['p_words']:.3f}  -> {r['verdict']}")
        print("\n=== Rule 4 (R3, does the hostile register travel?) ===")
        for d, r in rule_r3(src, models, dmax).items():
            marg = ", ".join(f"{tag[m]} {g:+.1%}" for m, g in r["gaps"].items())
            print(f"  d={d}: {marg}"
                  + (f"   Fisher p={r['p']:.3f}  {'TRAVELS' if r['travels'] else '-'}" if verdict else ""))
        r = sanity(src, models)
        print("\n=== Sanity: source_cc against the natural line at d = 1 ===")
        print("  " + ", ".join(f"{tag[m]}: {g:+.2f}" for m, g in r["gaps"].items())
              + (("   CAVEAT: the scripted source itself shifts behaviour" if r["caveat"] else "   ok")
                 if verdict else ""))

    # ---- rules 5-9: the LLM sources, model by model
    for m in models:
        need = ["baseline", "source_cd"] + list(LLM_CELLS.values())
        short_llm = [f"{c}: {n_runs(dn, m, c)}" for c in need if n_runs(dn, m, c) < RUNS]
        print(f"\n=== Rules 5-9, the LLM sources: {m} ===")
        if short_llm:
            print(f"  [not read] they need {RUNS} runs of these cells; short: " + ", ".join(short_llm))
            continue
        chk = manipulation_check(dn, m)
        print(f"  Rule 5, manipulation check: signals {chk['signals']}/{chk['msgs']} = {chk['sig_share']:.0%} "
              f"(>= 50%), broken {chk['broken']} = {chk['broken_share']:.0%} (>= 25%)"
              f"  -> {'a manipulator' if chk['passed'] else 'NO manipulator: rules 6 and 7 not read for it'}")
        if chk["passed"]:
            h = harm_vs_liar(dn, m)
            print(f"  Rule 6, agent 1 beside it {f2(h['manip'])}, beside the scripted liar {f2(h['liar'])} "
                  f"({h['gap']:+.2f})  -> {h['verdict']}")
        print("  Rule 7, reach against the natural line (harm: a drop of more than 0.10)")
        for cell in LLM_CELLS.values():
            if cell == "llm_manipulator" and not chk["passed"]:
                continue
            r = reach_vs_natural(dn, cell, m, dmax)
            marg = " ".join(f"{v:+.2f}" for v in r["diffs"].values())
            print(f"    {cell:<16} d=1-{dmax}: {marg}  -> reach {r['reach']}")
            for d in range(3, r["reach"] + 1):
                vals = ", ".join(f"{v:.2f}" for v in coop_runs(dn, cell, d, m))
                base = ", ".join(f"{v:.2f}" for v in coop_runs(dn, "baseline", d, m))
                print(f"      d={d} per run: {vals}  (natural line: {base})")
        print("  Rule 8, agent 0's points per round (per run)")
        for cell in CELLS:
            s = dn[(dn.model == m) & (dn.cell == cell) & (dn.d == 0)]
            if len(s):
                print(f"    {cell:<16} {s.points.mean():.2f}   ("
                      + ", ".join(f"{v:.2f}" for v in s.points) + ")")
        print("  Rule 9, nearest scripted cell (mean absolute difference over d = 1-"
              f"{dmax})")
        for cell in LLM_CELLS.values():
            r = nearest(dn, cell, m, dmax)
            print(f"    {cell:<16} -> {r['nearest']}   ("
                  + ", ".join(f"{c} {v:.2f}" for c, v in r["mad"].items()) + ")")

    # ---- length: the same model on two lines, at the distances both share inside the line
    for m in sorted(df.model.unique()):
        lengths = sorted(df[df.model == m].n.unique())
        if len(lengths) < 2:
            continue
        a, b = lengths[0], lengths[-1]
        dshare = min(a, b) - 2
        print(f"\n=== Length (descriptive): {m}, line of {b} against line of {a}, d = 1-{dshare} ===")
        for cell in CELLS:
            sa = df[(df.model == m) & (df.n == a) & (df.cell == cell)]
            sb = df[(df.model == m) & (df.n == b) & (df.cell == cell)]
            if sa.empty or sb.empty:
                continue
            ca = [sa[sa.d == d].coop.mean() for d in range(1, dshare + 1)]
            cb = [sb[sb.d == d].coop.mean() for d in range(1, dshare + 1)]
            print(f"  {cell:<16} {a}: " + " ".join(f2(v) for v in ca)
                  + f"   {b}: " + " ".join(f2(v) for v in cb)
                  + "   diff: " + " ".join(f"{y - x:+.2f}" for x, y in zip(ca, cb)))


if __name__ == "__main__":
    main()
