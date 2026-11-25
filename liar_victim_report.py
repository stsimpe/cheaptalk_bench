"""The liar and its victims on the line of eight, read by
docs/line_n8_liar_victim_plan.md.

A 2 x 2 of manipulators at agent 0 of a line of eight (session MANIP,
--policy-agents 0): the liar's model (agent 0) crossed with the victims'
model (agents 1-7), Qwen/Qwen3.5-122B-A10B and Qwen/Qwen3.8-27B-FP8. The two
mixed cells run with --agent-model 0=<liar> (config `agent_models`); the two
homogeneous cells run the same day. The references are the line of eight of
2026-11-21 (docs/line_n8_plan.md): each victims' model's natural line,
scripted cells and manipulator.

  --new   the trees of the 2 x 2 (tok4096/liar_victim/runs)
  --refs  the trees of the line of eight of 11-21 (tok4096/line_n8/*/runs)

Description, per cell: cooperation by distance d from agent 0; agent 0's
cooperation, signals of cooperation (signal_rules.is_signal), signals broken
in the same round, and points per round; agent 1 in rounds 1-5 and 12-16;
compliance counts (calls by served model, invalid decisions, round-1 message
prompt tokens by agent, think tags in delivered messages).

Rules of the plan (rule 1, compliance, is read with verify_prompts.py,
audit_corpus.py and the counts printed here):
  2  drift: each same-day line of one model against its cell of 11-21, agent 1
  3  manipulation check, per cell
  4  whose harm: the liar's model, the victims' model (agent 1)
  5  does lying pay: agent 0's points per round against the victims' natural
     agent 0 of 11-21
  6  reach, against the victims' natural line of 11-21
  7  the nearest cell of the victims' line of 11-21 (descriptive)
A rule is read only when the cells it needs hold 5 runs.

Usage:
    python liar_victim_report.py --new <trees> --refs <trees>
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from collections import Counter

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from contagion_report import distances  # noqa: E402
from cross_model_analysis import discover_records, normalise_model_id  # noqa: E402
from line_report import (EPS_DIGITS, MARGIN, RUNS, SRC_CELLS, _get, _mean,  # noqa: E402
                         collect as collect_refs, f2, short)
from signal_rules import is_signal  # noqa: E402

BIG, SMALL = "Qwen3.5-122B-A10B", "Qwen3.8-27B-FP8"
MODELS = (BIG, SMALL)
N = 8
DMAX = N - 1
DRIFT = 0.20          # a same-day homogeneous cell against its cell of 11-21, agent 1
PAYS = 0.20           # points per round, against the victims' natural agent 0
TOKENS = {0: 511, "others": 460}
THINK = re.compile(r"</?think", re.I)
LABELS = ("Cooperate", "Defect")


def name(liar: str, victims: str) -> str:
    return f"{short(liar)} liar, {short(victims)} line"


# ---------------------------------------------------------------- collection

def collect_new(roots: list[str]) -> tuple[pd.DataFrame, dict]:
    """Rows per (cell, run, agent) of the 2 x 2, and per-cell compliance counts."""
    rows, comp = [], {}
    for path, d in discover_records(roots):
        cfg, topo = d["config"], d["topology"]
        if (topo.get("type") != "line" or cfg.get("game") != "pd" or cfg.get("condition") != "cheap_talk"
                or cfg.get("scenario") != "framing_manipulative_context" or cfg.get("policy_agents") != [0]):
            continue
        am = {int(k): v for k, v in (cfg.get("agent_models") or {}).items()}
        if am and set(am) != {0}:
            continue
        victims = normalise_model_id(cfg["model"]["model_id"])
        liar = normalise_model_id(am[0]) if am else victims
        n, hist = topo["n_agents"], d["history"]
        if n != N:
            continue
        key = (liar, victims)
        c = comp.setdefault(key, {"served": Counter(), "unrecorded": 0, "invalid": 0, "decisions": 0,
                                  "tokens": {}, "think_delivered": 0, "runs": 0, "mixed": bool(am)})
        c["runs"] += 1
        for r in hist:
            for a, ks in (r.get("llm_calls") or {}).items():
                a = int(a)
                for k in ks:
                    if "model" in k:
                        c["served"][("agent 0" if a == 0 else "agents 1-7", normalise_model_id(k["model"]))] += 1
                    else:
                        c["unrecorded"] += 1
                    if r["round"] == 1 and k.get("phase") == "message":
                        c["tokens"].setdefault(a, set()).add(k.get("prompt_tokens"))
            for a in range(n):
                act = _get(r["actions"], a)
                c["decisions"] += 1
                c["invalid"] += act not in LABELS or bool(_get(r.get("invalid") or {}, a))
            texts = list((r.get("messages") or {}).values())
            for by in (r.get("messages_seen_by") or {}).values():
                texts += list((by or {}).values())
            c["think_delivered"] += sum(isinstance(t, str) and bool(THINK.search(t)) for t in texts)
        for agent, dd in distances(topo["edges"], n, 0).items():
            acts = []
            for r in hist:
                a = _get(r["actions"], agent)
                if a in LABELS and not _get(r.get("invalid") or {}, agent):
                    acts.append(a == "Cooperate")
            row = {"liar": liar, "victims": victims, "run": os.path.basename(path), "d": dd,
                   "coop": _mean(acts), "coop_early": _mean(acts[:5]), "coop_late": _mean(acts[-5:])}
            if dd == 0:
                said = [(str(_get(r.get("messages") or {}, 0) or "").strip(), _get(r["actions"], 0)) for r in hist]
                signals = [a for m, a in said if m and is_signal(m)]
                row.update(msgs0=sum(1 for m, _ in said if m), signals=len(signals),
                           broken=sum(1 for a in signals if a == "Defect"),
                           points=_mean(float(_get(r["payoffs"], 0)) for r in hist))
            rows.append(row)
    return pd.DataFrame(rows), comp


def runs_of(df, key) -> int:
    s = df[(df.liar == key[0]) & (df.victims == key[1])]
    return s["run"].nunique()


def agent_runs(df, key, d) -> list[float]:
    s = df[(df.liar == key[0]) & (df.victims == key[1]) & (df.d == d)]
    return s["coop"].tolist()


def ref_runs(refs, cell, model, d) -> list[float]:
    s = refs[(refs.cell == cell) & (refs.model == model) & (refs.d == d)]
    return s["coop"].tolist()


def ref_points(refs, cell, model) -> list[float]:
    s = refs[(refs.cell == cell) & (refs.model == model) & (refs.d == 0)]
    return s["points"].tolist()


def rnd(v: float) -> float:
    return round(v, EPS_DIGITS)


# ---------------------------------------------------------------- the rules

def drift(df, refs, model) -> dict:
    same = _mean(agent_runs(df, (model, model), 1))
    old = _mean(ref_runs(refs, "llm_manipulator", model, 1))
    gap = rnd(same - old)
    return {"same": same, "old": old, "gap": gap, "ok": abs(gap) <= DRIFT}


def manipulation_check(df, key) -> dict:
    s = df[(df.liar == key[0]) & (df.victims == key[1]) & (df.d == 0)]
    sig = s.signals.sum() / max(1, s.msgs0.sum())
    brk = s.broken.sum() / max(1, s.signals.sum())
    return {"signals": int(s.signals.sum()), "msgs": int(s.msgs0.sum()), "broken": int(s.broken.sum()),
            "sig_share": sig, "broken_share": brk, "passed": rnd(sig) >= 0.50 and rnd(brk) >= 0.25}


def direction(a: float, b: float, neg: str, pos: str, none: str) -> str:
    if a < -MARGIN and b < -MARGIN:
        return neg
    if a > MARGIN and b > MARGIN:
        return pos
    if abs(a) <= MARGIN and abs(b) <= MARGIN:
        return none
    return "mixed"


def whose_harm(df, refs) -> dict:
    """Rule 4. C1 is agent 1's cooperation; H is C1 minus the victims' natural line at d = 1 (11-21)."""
    c1 = {(l, v): _mean(agent_runs(df, (l, v), 1)) for l in MODELS for v in MODELS}
    nat = {v: _mean(ref_runs(refs, "baseline", v, 1)) for v in MODELS}
    h = {k: c1[k] - nat[k[1]] for k in c1}
    dl = {v: rnd(c1[(BIG, v)] - c1[(SMALL, v)]) for v in MODELS}
    dv = {l: rnd(h[(l, SMALL)] - h[(l, BIG)]) for l in MODELS}
    liar = direction(dl[SMALL], dl[BIG], f"the {short(BIG)} liar does more harm",
                     f"the {short(SMALL)} liar does more harm", "the liar's model makes no difference")
    vict = direction(dv[BIG], dv[SMALL], f"the {short(SMALL)} victims are harmed more",
                     f"the {short(BIG)} victims are harmed more", "the victims' model makes no difference")
    l_dir = liar.endswith("more harm")
    v_dir = vict.endswith("harmed more")
    if l_dir and vict.startswith("the victims' model makes"):
        summary = "the harm is the liar's"
    elif v_dir and liar.startswith("the liar's model makes"):
        summary = "the harm is the victims'"
    elif l_dir and v_dir:
        summary = "both the liar and the victims"
    elif liar.startswith("the liar's model makes") and vict.startswith("the victims' model makes"):
        summary = "neither"
    else:
        summary = "mixed"
    return {"c1": c1, "nat": nat, "h": h, "dl": dl, "dv": dv, "liar": liar, "victims": vict, "summary": summary}


def pays(df, refs, key) -> dict:
    s = df[(df.liar == key[0]) & (df.victims == key[1]) & (df.d == 0)]
    p = s.points.mean()
    nat = _mean(ref_points(refs, "baseline", key[1]))
    gap = rnd(p - nat)
    verdict = "pays" if gap > PAYS else "does not pay" if gap < -PAYS else "about even"
    return {"points": p, "per_run": s.points.tolist(), "natural": nat, "gap": gap, "verdict": verdict,
            "liar_bot": _mean(ref_points(refs, "source_cd", key[1])),
            "enemy_bot": _mean(ref_points(refs, "source_hd", key[1]))}


def reach(df, refs, key) -> dict:
    diffs = {d: rnd(_mean(agent_runs(df, key, d)) - _mean(ref_runs(refs, "baseline", key[1], d)))
             for d in range(1, DMAX + 1)}
    r = 0
    for d in range(1, DMAX + 1):
        if not diffs[d] < -MARGIN:
            break
        r = d
    return {"diffs": diffs, "reach": r}


def nearest(df, refs, key) -> dict:
    prof = [_mean(agent_runs(df, key, d)) for d in range(1, DMAX + 1)]
    mad = {c: _mean(abs(a - _mean(ref_runs(refs, c, key[1], d))) for d, a in zip(range(1, DMAX + 1), prof))
           for c in SRC_CELLS}
    return {"mad": mad, "nearest": min(mad, key=mad.get)}


# ---------------------------------------------------------------- report

def describe(df, comp, refs):
    keys = [(l, v) for v in MODELS for l in MODELS]
    print("######## the 2 x 2 (runs per cell: "
          + ", ".join(f"{name(*k)} {runs_of(df, k)}" for k in keys) + ")")
    print("\ncooperation by distance from agent 0 (mean of run means; d = 0 is the liar)")
    head = "".join(f"{d:>6}" for d in range(N))
    print(f"   {'cell':<28}{head}")
    for k in keys:
        if runs_of(df, k):
            print(f"   {name(*k):<28}" + "".join(f"{_mean(agent_runs(df, k, d)):>6.2f}" for d in range(N)))
    for v in MODELS:
        for c, label in (("baseline", "natural line"), ("source_cd", "scripted liar"), ("source_hd", "open enemy"),
                         ("llm_manipulator", "manipulator")):
            vals = [_mean(ref_runs(refs, c, v, d)) for d in range(N)]
            print(f"   {short(v) + ' ' + label + ' (11-21)':<28}" + "".join(f"{x:>6.2f}" for x in vals))
    print("\nthe liar (agent 0): cooperation, signals of cooperation in its messages, signals broken in the "
          "same round, points per round")
    for k in keys:
        s = df[(df.liar == k[0]) & (df.victims == k[1]) & (df.d == 0)]
        if len(s):
            sig = s.signals.sum() / max(1, s.msgs0.sum())
            brk = s.broken.sum() / max(1, s.signals.sum())
            print(f"   {name(*k):<28} coop {s.coop.mean():.2f}   signals {int(s.signals.sum())}/{int(s.msgs0.sum())}"
                  f" = {sig:.0%}   broken {int(s.broken.sum())} = {brk:.0%}   points {s.points.mean():.2f}")
    print("\nagent 1, rounds 1-5 -> rounds 12-16: "
          + "; ".join(f"{name(*k)} {df[(df.liar == k[0]) & (df.victims == k[1]) & (df.d == 1)].coop_early.mean():.2f}"
                      f" -> {df[(df.liar == k[0]) & (df.victims == k[1]) & (df.d == 1)].coop_late.mean():.2f}"
                      for k in keys if runs_of(df, k)))
    print("\ncompliance, per cell")
    for k in keys:
        c = comp.get(k)
        if not c:
            continue
        tok0 = sorted(c["tokens"].get(0, set()))
        toko = sorted(set().union(*[v for a, v in c["tokens"].items() if a != 0]) if len(c["tokens"]) > 1 else set())
        routing = ("not recorded (one model in the line)" if not c["mixed"] else
                   ", ".join(f"{who} by {m}: {n}" for (who, m), n in sorted(c["served"].items()))
                   + (f"; unrecorded {c['unrecorded']}" if c["unrecorded"] else ""))
        print(f"   {name(*k):<28} runs {c['runs']}; invalid {c['invalid']}/{c['decisions']}; round-1 message prompt "
              f"tokens agent 0 {tok0}, agents 1-7 {toko}; think tags delivered {c['think_delivered']}")
        print(f"   {'':<28} served: {routing}")


def routing_ok(comp, key) -> bool:
    c = comp.get(key)
    if not c or not c["mixed"]:
        return True
    want = {("agent 0", key[0]), ("agents 1-7", key[1])}
    return set(c["served"]) == want and not c["unrecorded"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--new", nargs="+", required=True)
    ap.add_argument("--refs", nargs="+", required=True)
    args = ap.parse_args()
    df, comp = collect_new(args.new)
    if df.empty:
        raise SystemExit("No manipulator runs on a line of eight under --new.")
    refs = collect_refs(args.refs)
    refs = refs[refs.n == N]
    for m in MODELS:
        need = ["baseline", "source_cd", "source_hd", "llm_manipulator"]
        short_refs = [c for c in need if refs[(refs.model == m) & (refs.cell == c)]["run"].nunique() < RUNS]
        if short_refs:
            raise SystemExit(f"--refs lack 5 runs of {short(m)}'s {short_refs} on the line of eight.")
    describe(df, comp, refs)

    keys = [(l, v) for v in MODELS for l in MODELS]
    full = {k: runs_of(df, k) >= RUNS for k in keys}
    print("\n================ the rules")
    print("\n=== Routing (mixed cells: agent 0 served by the liar's model, agents 1-7 by the victims') ===")
    for k in keys:
        if comp.get(k, {}).get("mixed"):
            print(f"  {name(*k)}: {'as planned' if routing_ok(comp, k) else 'NOT AS PLANNED'}")

    print(f"\n=== Rule 2, drift: each same-day line of one model against its cell of 11-21, agent 1 (within {DRIFT:.2f}) ===")
    drift_ok = {}
    for m in MODELS:
        if not full[(m, m)]:
            print(f"  {short(m)}: [not read] the same-day cell holds {runs_of(df, (m, m))} runs")
            drift_ok[m] = False
            continue
        r = drift(df, refs, m)
        drift_ok[m] = r["ok"]
        print(f"  {short(m)} liar, {short(m)} line: same day {f2(r['same'])}, 11-21 {f2(r['old'])} ({r['gap']:+.2f})"
              f"  -> {'no drift' if r['ok'] else 'DRIFT: the readings that use the ' + short(m) + ' line of 11-21 are not read'}")

    print("\n=== Rule 3, manipulation check: the liar signals in at least half of its messages and breaks at least "
          "25% of its signals ===")
    manip = {}
    for k in keys:
        if not full[k]:
            print(f"  {name(*k)}: [not read] {runs_of(df, k)} runs")
            manip[k] = False
            continue
        r = manipulation_check(df, k)
        manip[k] = r["passed"]
        print(f"  {name(*k)}: signals {r['signals']}/{r['msgs']} = {r['sig_share']:.0%}, broken {r['broken']} = "
              f"{r['broken_share']:.0%}  -> {'a manipulator' if r['passed'] else 'NO manipulator: rules 4-6 not read for this cell'}")

    print("\n=== Rule 4, whose harm? Agent 1's cooperation (C1); harm H = C1 minus the victims' natural line at d = 1 "
          "(11-21) ===")
    if not all(full[k] and manip[k] for k in keys):
        print("  [not read] it needs all four cells, with 5 runs and a manipulator each")
    else:
        r = whose_harm(df, refs)
        for k in keys:
            print(f"  {name(*k):<28} C1 {f2(r['c1'][k])}   H {r['h'][k]:+.2f}   (runs "
                  + ", ".join(f"{x:.2f}" for x in agent_runs(df, k, 1)) + ")")
        print(f"  natural line at d = 1 (11-21): {short(SMALL)} {f2(r['nat'][SMALL])}, {short(BIG)} {f2(r['nat'][BIG])}")
        print(f"  the liar, same victims: on the {short(SMALL)} line {r['dl'][SMALL]:+.2f}, on the {short(BIG)} line "
              f"{r['dl'][BIG]:+.2f}  ({short(BIG)} liar minus {short(SMALL)} liar)  -> {r['liar']}")
        if all(drift_ok.values()):
            print(f"  the victims, same liar: {short(BIG)} liar {r['dv'][BIG]:+.2f}, {short(SMALL)} liar "
                  f"{r['dv'][SMALL]:+.2f}  (H on the {short(SMALL)} line minus H on the {short(BIG)} line)  -> {r['victims']}")
            print(f"  -> {r['summary']}")
        else:
            print("  the victims: [not read] a drift was found; the liar's part stands on the same-day cells alone")

    print("\n=== Rule 5, does lying pay? The liar's points per round against the victims' natural agent 0 (11-21); "
          f"more than {PAYS:.2f} either way ===")
    for k in keys:
        if not (full[k] and manip[k]):
            print(f"  {name(*k)}: [not read]")
            continue
        if not drift_ok[k[1]]:
            print(f"  {name(*k)}: [not read] drift on the {short(k[1])} line")
            continue
        r = pays(df, refs, k)
        print(f"  {name(*k):<28} {r['points']:.2f} (" + ", ".join(f"{x:.2f}" for x in r["per_run"])
              + f"); natural agent 0 {r['natural']:.2f} ({r['gap']:+.2f})  -> {r['verdict']}"
              f"   [scripted liar {r['liar_bot']:.2f}, open enemy {r['enemy_bot']:.2f}]")

    print(f"\n=== Rule 6, reach against the victims' natural line of 11-21 (harm: a drop of more than {MARGIN:.2f}) ===")
    for k in keys:
        if not (full[k] and manip[k]) or not drift_ok[k[1]]:
            print(f"  {name(*k)}: [not read]")
            continue
        r = reach(df, refs, k)
        print(f"  {name(*k):<28} d=1-{DMAX}: " + " ".join(f"{v:+.2f}" for v in r["diffs"].values())
              + f"  -> reach {r['reach']}")
        for d in range(3, r["reach"] + 1):
            print(f"      d={d} per run: " + ", ".join(f"{x:.2f}" for x in agent_runs(df, k, d))
                  + "  (natural line: " + ", ".join(f"{x:.2f}" for x in ref_runs(refs, "baseline", k[1], d)) + ")")

    print(f"\n=== Rule 7 (descriptive), the nearest cell of the victims' line of 11-21 (mean absolute difference, d = 1-{DMAX}) ===")
    for k in keys:
        if not full[k]:
            continue
        r = nearest(df, refs, k)
        print(f"  {name(*k):<28} -> {r['nearest']}   (" + ", ".join(f"{c} {v:.2f}" for c, v in r["mad"].items()) + ")")


if __name__ == "__main__":
    main()
