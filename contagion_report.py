"""Words or deeds: the contagion experiment, read by its pre-registered rules.

Reads the line runs of session SRC (docs/contagion_plan.md) and reports, for
every model, cell and distance from the scripted source: cooperation, the
share of messages written in the competitive register (F1 lexicon), and the
round of first defection. Then applies the plan's rules as written:

  R1  reach: harm at distance d against source_cc, > 0.10 in both models and
      pooled one-sided Mann-Whitney p < 0.05, Holm over the five distances;
      the reach counts outward from d = 1 and stops at the first failure
  R2  words or deeds at d = 1: source_cd against source_hc, a 0.10 margin in
      both models and a pooled Mann-Whitney p < 0.05
  R3  the hostile register travels to d: F1 share in source_hc above
      source_cc by >= 10 points in both models, pooled Fisher p < 0.05
  sanity  source_cc against baseline at d = 1

Usage:
    python contagion_report.py --roots <result trees> [--csv contagion.csv]
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from collections import deque

import pandas as pd
from scipy.stats import fisher_exact, mannwhitneyu

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cross_model_analysis import discover_records, normalise_model_id  # noqa: E402
from message_policies import MESSAGE_FILTERS  # noqa: E402

CELLS = ["baseline", "source_cc", "source_hc", "source_cd", "source_hd"]
SOURCE_CELLS = ["source_hc", "source_cd", "source_hd"]
NAMES = {"source_cc": "control (coop words, coop deeds)",
         "source_hc": "loud (hostile words, coop deeds)",
         "source_cd": "liar (coop words, defect deeds)",
         "source_hd": "open enemy (hostile words, defect deeds)",
         "baseline": "natural line (LLM agent 0)"}
F1 = MESSAGE_FILTERS["F1_competitive"]
MARGIN = 0.10
ALPHA = 0.05


# ---------------------------------------------------------------- collection

def distances(edges: list, n: int, src: int) -> dict[int, int]:
    adj = {i: set() for i in range(n)}
    for u, v in edges:
        adj[u].add(v)
        adj[v].add(u)
    dist, q = {src: 0}, deque([src])
    while q:
        u = q.popleft()
        for v in adj[u]:
            if v not in dist:
                dist[v] = dist[u] + 1
                q.append(v)
    return dist


def hostile(msg: str) -> bool:
    return bool(F1 & set(re.findall(r"[a-z']+", str(msg).lower())))


def _get(d: dict, agent: int):
    """Run records key agents by string after a JSON round trip."""
    return d.get(str(agent), d.get(agent))


def _mean(xs):
    return sum(xs) / len(xs) if len(xs) else float("nan")


def collect(roots: list[str]) -> pd.DataFrame:
    rows = []
    for path, d in discover_records(roots):
        cfg = d["config"]
        cell = cfg.get("scenario", "")
        if cell not in CELLS or d["topology"].get("type") != "line":
            continue
        if cfg.get("game") != "pd" or cfg.get("condition") != "cheap_talk":
            continue
        model = normalise_model_id(cfg.get("model", {}).get("model_id", "?"))
        topo = d["topology"]
        src = cfg.get("source_agent")
        src = 0 if src is None else src  # the natural line: compare by position
        for agent, dd in distances(topo["edges"], topo["n_agents"], src).items():
            if dd == 0:
                continue
            acts, writes, first_def = [], [], None
            for r in d["history"]:
                a = _get(r["actions"], agent)
                if a in ("Cooperate", "Defect") and not _get(r.get("invalid") or {}, agent):
                    acts.append(a == "Cooperate")
                    if a == "Defect" and first_def is None:
                        first_def = r["round"]
                msg = _get(r.get("messages") or {}, agent)
                if msg:
                    writes.append(hostile(msg))
            if not acts:
                continue
            rows.append({
                "model": model, "cell": cell, "run": os.path.basename(path), "d": dd,
                "coop": _mean(acts), "coop_early": _mean(acts[:5]),
                "coop_late": _mean(acts[-5:]), "end_coop": _mean(acts[-5:]) >= 0.5,
                "n_msgs": len(writes), "f1_hits": sum(writes), "first_defect": first_def,
            })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- the rules

def runs(df, cell, d, model=None) -> list[float]:
    s = df[(df.cell == cell) & (df.d == d)]
    if model is not None:
        s = s[s.model == model]
    return s["coop"].tolist()


def holm(ps: list[float]) -> list[float]:
    order = sorted(range(len(ps)), key=lambda i: ps[i])
    adj, running = [0.0] * len(ps), 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (len(ps) - rank) * ps[i]))
        adj[i] = running
    return adj


def _mw_less(a, b) -> float:
    return mannwhitneyu(a, b, alternative="less").pvalue if a and b else 1.0


def rule_r1(df, cell, models, dmax) -> dict:
    """Harm at each distance against source_cc, and the reach it implies."""
    both = len(models) >= 2
    diffs = {d: {m: _mean(runs(df, cell, d, m)) - _mean(runs(df, "source_cc", d, m))
                 for m in models} for d in range(1, dmax + 1)}
    padj = holm([_mw_less(runs(df, cell, d), runs(df, "source_cc", d))
                 for d in range(1, dmax + 1)])
    passed = {d: both and all(v < -MARGIN for v in diffs[d].values()) and padj[d - 1] < ALPHA
              for d in diffs}
    reach = 0
    for d in range(1, dmax + 1):
        if not passed[d]:
            break
        reach = d
    return {"diffs": diffs, "p_holm": dict(zip(diffs, padj)), "passed": passed, "reach": reach}


def rule_r2(df, models) -> dict:
    """At d = 1: does the liar (deeds) harm more than the loud source (words)?"""
    both = len(models) >= 2
    harm = {m: (_mean(runs(df, "source_cd", 1, m)) - _mean(runs(df, "source_cc", 1, m)),
                _mean(runs(df, "source_hc", 1, m)) - _mean(runs(df, "source_cc", 1, m)))
            for m in models}
    cd, hc = runs(df, "source_cd", 1), runs(df, "source_hc", 1)
    p_deeds, p_words = _mw_less(cd, hc), _mw_less(hc, cd)
    if both and all(l < h - MARGIN for l, h in harm.values()) and p_deeds < ALPHA:
        verdict = "deeds dominate"
    elif both and all(h < l - MARGIN for l, h in harm.values()) and p_words < ALPHA:
        verdict = "words dominate"
    else:
        verdict = "comparable"
    return {"harm": harm, "p_deeds": p_deeds, "p_words": p_words, "verdict": verdict}


def rule_r3(df, models, dmax) -> dict:
    """Does the agent at distance d write in the competitive register more
    when the source's words are hostile (deeds held at cooperation)?"""
    both = len(models) >= 2
    out = {}
    for d in range(1, dmax + 1):
        share, hits, tot = {}, {}, {}
        for c in ("source_hc", "source_cc"):
            s = df[(df.cell == c) & (df.d == d)]
            hits[c], tot[c] = int(s.f1_hits.sum()), int(s.n_msgs.sum())
            share[c] = {m: s[s.model == m].f1_hits.sum() / max(1, s[s.model == m].n_msgs.sum())
                        for m in models}
        p = fisher_exact([[hits["source_hc"], tot["source_hc"] - hits["source_hc"]],
                          [hits["source_cc"], tot["source_cc"] - hits["source_cc"]]],
                         alternative="greater")[1]
        gaps = {m: share["source_hc"][m] - share["source_cc"][m] for m in models}
        out[d] = {"gaps": gaps, "p": p,
                  "travels": both and all(g >= 0.10 for g in gaps.values()) and p < ALPHA}
    return out


def sanity(df, models) -> dict:
    gaps = {m: _mean(runs(df, "source_cc", 1, m)) - _mean(runs(df, "baseline", 1, m))
            for m in models}
    return {"gaps": gaps,
            "caveat": len(models) >= 2 and all(abs(g) > MARGIN for g in gaps.values())}


# ---------------------------------------------------------------- report

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--roots", nargs="+", required=True)
    ap.add_argument("--csv", default=None)
    args = ap.parse_args()
    df = collect(args.roots)
    if df.empty:
        raise SystemExit("No line runs of session SRC under --roots.")
    if "source_cc" not in set(df.cell):
        raise SystemExit("source_cc is missing: every rule is read against it.")
    models = sorted(df.model.unique())
    dmax = int(df.d.max())
    short = {m: m.split("-")[0] for m in models}

    summ = (df.groupby(["model", "cell", "d"])
              .agg(runs=("coop", "size"), coop=("coop", "mean"),
                   end_coop=("end_coop", "mean"), f1_hits=("f1_hits", "sum"),
                   msgs=("n_msgs", "sum"), first_defect=("first_defect", "median"))
              .reset_index())
    summ["f1_share"] = summ["f1_hits"] / summ["msgs"].where(summ["msgs"] > 0)
    print("=== Cooperation by distance from the source (mean of run means) ===")
    for m in models:
        for col, title in (("coop", "cooperation"), ("f1_share", "F1 share of written messages")):
            t = summ[summ.model == m].pivot(index="cell", columns="d", values=col)
            print(f"\n{m}, {title}")
            print(t.reindex([c for c in CELLS if c in t.index]).round(2).to_string())
    if args.csv:
        summ.to_csv(args.csv, index=False)
        print(f"\n-> {args.csv}")
    if len(models) < 2:
        print("\n[note] Every rule needs both models; with one, only the margins are shown.")
    # The rules are read on the complete design: five runs per cell and model.
    # A session that holds one block of runs (3 of 5, or 2 of 5) shows the
    # description above and stops here, so no verdict is read early.
    runs = df.groupby(["model", "cell"])["run"].nunique()
    short_cells = [f"{m.split('-')[0]} {c}: {n}" for (m, c), n in runs.items() if n < 5]
    if short_cells or len(runs) < len(models) * len(CELLS):
        print(f"\n[not read] the rules need 5 runs of every cell in both models; "
              f"short: {', '.join(short_cells) or 'cells missing'}")
        return

    print("\n=== R1  reach: harm against source_cc, > 0.10 in both models, Holm p < 0.05 ===")
    for cell in [c for c in SOURCE_CELLS if c in set(df.cell)]:
        r = rule_r1(df, cell, models, dmax)
        for d in r["diffs"]:
            marg = ", ".join(f"{short[m]} {v:+.2f}" for m, v in r["diffs"][d].items())
            print(f"  {cell}  d={d}: {marg}   Holm p={r['p_holm'][d]:.3f}"
                  f"  {'PASS' if r['passed'][d] else '-'}")
        print(f"  -> reach of the {NAMES[cell]}: {r['reach']}")

    if {"source_cd", "source_hc"} <= set(df.cell):
        r = rule_r2(df, models)
        print("\n=== R2  words or deeds at d = 1 ===")
        for m, (l, h) in r["harm"].items():
            print(f"  {m}: harm of the liar {l:+.2f}, of the loud source {h:+.2f}")
        print(f"  pooled p (deeds) = {r['p_deeds']:.3f}, p (words) = {r['p_words']:.3f}"
              f"  -> {r['verdict']}")

    if {"source_hc", "source_cc"} <= set(df.cell):
        print("\n=== R3  does the hostile register travel? ===")
        for d, r in rule_r3(df, models, dmax).items():
            marg = ", ".join(f"{short[m]} {g:+.1%}" for m, g in r["gaps"].items())
            print(f"  d={d}: {marg}   Fisher p={r['p']:.3f}  {'TRAVELS' if r['travels'] else '-'}")

    if "baseline" in set(df.cell):
        r = sanity(df, models)
        print("\n=== Sanity: source_cc against the natural line at d = 1 ===")
        print("  " + ", ".join(f"{m}: {g:+.2f}" for m, g in r["gaps"].items())
              + ("   CAVEAT: the scripted source itself shifts behaviour" if r["caveat"] else "   ok"))

    s = df[(df.cell == "source_cd") & (df.d == 1)]
    if len(s):
        print("\n=== Liar cell, agent 1: rounds 1-5 against rounds 12-16 (descriptive) ===")
        for m in models:
            sm = s[s.model == m]
            if len(sm):
                print(f"  {m}: {sm.coop_early.mean():.2f} -> {sm.coop_late.mean():.2f}")


if __name__ == "__main__":
    main()
