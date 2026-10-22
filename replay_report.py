"""Round-1 replay: which part of a hostile message does the harm (docs/replay_plan.md).

Reads the calls of replay.py and applies the plan's rules, per model:

  link         the replay reproduces the corpus: recorded round-1 cooperation
               against W0 (writers), R0 (readers) and W2 (silence), Fisher
               two-sided, p >= 0.05 in all three
  harm         a route is decomposed only where it harms in round 1:
               W2 - W0 (writers) or W2 - R0 (readers) >= 0.15, p < 0.05
  writer       on the contexts whose own message holds an action word:
               recovery = (W1 - W0) / (W2 - W0)
                 copying  recovery >= 0.5 and W1 > W0 (p < 0.05)
                 stance   recovery <= 0.25 and W2 > W1 (p < 0.05)
                 mixed    otherwise
  attribution  S1 - W0, two-sided: |difference| > 0.10 and p < 0.05
  reader       the same on the contexts whose received messages hold an
               action word: recovery = (R1 - R0) / (W2 - R0), word / intent / mixed
  dose         hub readers, 0 to 3 hostile of 3 (D0, D1, D2, R0): Mantel's
               stratified trend test (strata = contexts), decreasing, p < 0.05,
               and D0 - R0 > 0.10

The unit is the context (one agent's round-1 decision in one original run)
and its share of cooperative calls. Within-context contrasts use an exact
sign-flip test over contexts; contrasts with the silence reference, which is
measured on other contexts, a two-sample permutation test. Holm across the
five models within each test. A variant with more than 15% invalid calls is
not read.

Usage:
    python replay_report.py --results replay_out/*.jsonl [--csv replay_summary.csv]
"""
from __future__ import annotations

import argparse
import glob
import json
import math
import os
import sys

import numpy as np
import pandas as pd
from scipy.stats import fisher_exact, norm

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from contagion_report import holm  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
HARM, COPY, STANCE, ATTR, DOSE, MAX_INVALID, ALPHA = 0.15, 0.5, 0.25, 0.10, 0.10, 0.15, 0.05


# --- tests -------------------------------------------------------------------

def flip_p(d, alternative: str) -> float:
    """Sign-flip permutation test of the sum of within-context differences:
    exact up to 16 non-zero differences, else 200,000 random flips."""
    d = np.asarray([x for x in d if abs(x) > 1e-12], float)
    if not len(d):
        return 1.0
    obs = d.sum()
    if len(d) <= 16:
        signs = ((np.arange(2 ** len(d))[:, None] >> np.arange(len(d))) & 1) * 2 - 1
        null, extra = signs @ d, 0
    else:
        signs = np.random.default_rng(0).choice([-1, 1], size=(200_000, len(d)))
        null, extra = signs @ d, 1
    hit = {"greater": null >= obs - 1e-9, "less": null <= obs + 1e-9,
           "two-sided": np.abs(null) >= abs(obs) - 1e-9}[alternative]
    return float((hit.sum() + extra) / (len(null) + extra))


def perm2_p(a, b, alternative: str = "greater", n: int = 100_000) -> float:
    """Two-sample permutation test of mean(a) - mean(b) over contexts."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    if not len(a) or not len(b):
        return 1.0
    pooled, na = np.concatenate([a, b]), len(a)
    obs = a.mean() - b.mean()
    idx = np.argsort(np.random.default_rng(0).random((n, len(pooled))), axis=1)
    null = pooled[idx[:, :na]].mean(1) - pooled[idx[:, na:]].mean(1)
    hit = null >= obs - 1e-9 if alternative == "greater" else null <= obs + 1e-9
    return float((hit.sum() + 1) / (n + 1))


def mantel_trend(strata: list[list[tuple[int, int]]]) -> tuple[float, float]:
    """Mantel's (1963) extension test for a trend in a proportion across scores,
    stratified. Each stratum is a list of (score, cooperated) calls. Returns
    z and the one-sided p for a decreasing trend."""
    t = v = 0.0
    for calls in strata:
        x = np.array([s for s, _ in calls], float)
        y = np.array([c for _, c in calls], float)
        n, k = len(y), y.sum()
        if n < 2 or k in (0, n):
            continue            # a stratum without both outcomes carries no information
        t += float((x * (y - k / n)).sum())
        v += k * (n - k) / (n ** 2 * (n - 1)) * (n * float((x ** 2).sum()) - float(x.sum()) ** 2)
    if v <= 0:
        return 0.0, 1.0
    z = t / math.sqrt(v)
    return z, float(norm.cdf(z))


# --- data --------------------------------------------------------------------

def load(paths: list[str]) -> pd.DataFrame:
    rows = []
    for p in paths:
        with open(p, encoding="utf-8") as f:
            rows += [json.loads(line) for line in f if line.strip()]
    if not rows:
        raise SystemExit("No replay calls under --results.")
    df = pd.DataFrame(rows)
    df["coop"] = (df["action"] == "Cooperate").astype(float)
    df["ctx"] = df["run"] + "|" + df["agent"].astype(str)
    return df


def shares(df: pd.DataFrame, kind: str, variant: str, only: set | None = None) -> pd.Series:
    """Per context: the share of its valid calls that cooperate."""
    sub = df[(df["kind"] == kind) & (df["variant"] == variant) & df["valid"]]
    if only is not None:
        sub = sub[sub["ctx"].isin(only)]
    return sub.groupby("ctx")["coop"].mean()


def invalid(df: pd.DataFrame, kind: str, variant: str) -> float:
    sub = df[(df["kind"] == kind) & (df["variant"] == variant)]
    return float(1 - sub["valid"].mean()) if len(sub) else float("nan")


def recorded(contexts: list[dict], model: str, kind: str) -> tuple[int, int]:
    acts = [c["recorded"] for c in contexts if c["model"] == model and c["kind"] == kind]
    acts = [a for a in acts if a in ("Cooperate", "Defect")]
    return sum(a == "Cooperate" for a in acts), len(acts)


def paired(a: pd.Series, b: pd.Series) -> np.ndarray:
    both = a.index.intersection(b.index)
    return (a[both] - b[both]).to_numpy()


def has_word(text: str) -> bool:
    from replay import ACTION_WORD
    return bool(ACTION_WORD.search(str(text)))


# --- one model ---------------------------------------------------------------

def model_block(df: pd.DataFrame, contexts: list[dict], model: str) -> dict:
    d = df[df["model"] == model]
    r = {"model": model}
    inv = {(k, v): invalid(d, k, v) for k, v in
           [("writer", v) for v in ("W0", "W1", "W2", "S1")] +
           [("reader", v) for v in ("R0", "R1", "D0", "D1", "D2")]}
    r["invalid"] = inv
    bad = {v for (k, v), x in inv.items() if x > MAX_INVALID}
    r["bad"] = bad
    s = {v: shares(d, "writer", v) for v in ("W0", "W1", "W2", "S1")}
    s.update({v: shares(d, "reader", v) for v in ("R0", "R1")})
    r["rate"] = {v: float(x.mean()) for v, x in s.items()}

    # Link: the unchanged contexts against the corpus.
    link = {}
    for kind, v in (("writer", "W0"), ("reader", "R0"), ("silence", "W2")):
        kc, nc = recorded(contexts, model, kind)
        calls = d[(d["kind"] == ("reader" if kind == "reader" else "writer"))
                  & (d["variant"] == v) & d["valid"]]
        kr, nr = int(calls["coop"].sum()), len(calls)
        p = fisher_exact([[kc, nc - kc], [kr, nr - kr]])[1] if nc and nr else float("nan")
        link[kind] = {"recorded": kc / nc if nc else float("nan"), "n_recorded": nc,
                      "replay": kr / nr if nr else float("nan"), "p": p}
    r["link"] = link
    r["link_ok"] = all(x["p"] >= ALPHA for x in link.values())

    # Writers: harm, then copying or stance on the contexts with an action word.
    r["harm_w"] = r["rate"]["W2"] - r["rate"]["W0"]
    r["p_harm_w"] = flip_p(paired(s["W2"], s["W0"]), "greater")
    worded = {f"{c['run']}|{c['agent']}" for c in contexts
              if c["model"] == model and c["kind"] == "writer" and has_word(c["own"])}
    w = {v: shares(d, "writer", v, worded) for v in ("W0", "W1", "W2")}
    r["n_worded_w"] = len(worded)
    gap = w["W2"].mean() - w["W0"].mean()
    r["gap_w"] = gap
    r["recovery_w"] = (w["W1"].mean() - w["W0"].mean()) / gap if gap > 1e-9 else float("nan")
    r["p_copy_w"] = flip_p(paired(w["W1"], w["W0"]), "greater")
    # Descriptive: the harm where there is a word to copy and where there is none.
    rest = set(s["W0"].index) - worded
    r["harm_w_worded"] = float(w["W2"].mean() - w["W0"].mean()) if worded else float("nan")
    r["harm_w_unworded"] = (float(shares(d, "writer", "W2", rest).mean()
                                  - shares(d, "writer", "W0", rest).mean()) if rest else float("nan"))
    r["p_stance_w"] = flip_p(paired(w["W2"], w["W1"]), "greater")

    # Attribution: the same text as one's own or as a neighbour's.
    r["attr"] = r["rate"]["S1"] - r["rate"]["W0"]
    r["p_attr"] = flip_p(paired(s["S1"], s["W0"]), "two-sided")

    # Readers: harm against silence, then word or intent.
    r["harm_r"] = r["rate"]["W2"] - r["rate"]["R0"]
    r["p_harm_r"] = perm2_p(s["W2"], s["R0"], "greater")
    worded_r = {f"{c['run']}|{c['agent']}" for c in contexts
                if c["model"] == model and c["kind"] == "reader"
                and any(has_word(m) for _, m in c["received"])}
    rr = {v: shares(d, "reader", v, worded_r) for v in ("R0", "R1")}
    r["n_worded_r"] = len(worded_r)
    gap_r = s["W2"].mean() - rr["R0"].mean()
    r["gap_r"] = gap_r
    r["recovery_r"] = (rr["R1"].mean() - rr["R0"].mean()) / gap_r if gap_r > 1e-9 else float("nan")
    r["p_word_r"] = flip_p(paired(rr["R1"], rr["R0"]), "greater")
    r["p_intent_r"] = perm2_p(s["W2"], rr["R1"], "greater")

    # Dose, hub readers: score = hostile messages of 3.
    hub = d[(d["kind"] == "reader") & d["hub"] & d["valid"]]
    dose = {"D0": 0, "D1": 1, "D2": 2, "R0": 3}
    hub = hub[hub["variant"].isin(dose)]
    strata = [[(dose[v], int(c)) for v, c in zip(g["variant"], g["coop"])]
              for _, g in hub.groupby("ctx")]
    r["dose_rate"] = {dose[v]: float(hub[hub["variant"] == v].groupby("ctx")["coop"].mean().mean())
                      for v in dose}
    r["dose_z"], r["p_dose"] = mantel_trend(strata)
    r["n_hub"] = hub["ctx"].nunique()
    return r


def verdicts(blocks: list[dict]):
    """Holm within each test across the models, then the plan's thresholds."""
    for key in ("p_harm_w", "p_copy_w", "p_stance_w", "p_attr", "p_harm_r",
                "p_word_r", "p_intent_r", "p_dose"):
        for b, adj in zip(blocks, holm([b[key] for b in blocks])):
            b[key + "_holm"] = adj
    for b in blocks:
        bad = b["bad"]
        b["v_writer"] = (
            "not read (invalid)" if bad & {"W0", "W1", "W2"} else
            "no round-1 harm" if not (b["harm_w"] >= HARM and b["p_harm_w_holm"] < ALPHA) else
            "harm with no action word to copy" if not b["n_worded_w"] else
            "copying" if b["recovery_w"] >= COPY and b["p_copy_w_holm"] < ALPHA else
            "stance" if b["recovery_w"] <= STANCE and b["p_stance_w_holm"] < ALPHA else
            "mixed")
        b["v_attr"] = (
            "not read (invalid)" if bad & {"W0", "S1"} else
            "own words weigh more" if b["attr"] > ATTR and b["p_attr_holm"] < ALPHA else
            "a neighbour's words weigh more" if b["attr"] < -ATTR and b["p_attr_holm"] < ALPHA else
            "not shown")
        b["v_reader"] = (
            "not read (invalid)" if bad & {"R0", "R1", "W2"} else
            "no round-1 harm" if not (b["harm_r"] >= HARM and b["p_harm_r_holm"] < ALPHA) else
            "harm with no action word to read" if not b["n_worded_r"] else
            "word" if b["recovery_r"] >= COPY and b["p_word_r_holm"] < ALPHA else
            "intent" if b["recovery_r"] <= STANCE and b["p_intent_r_holm"] < ALPHA else
            "mixed")
        drop = b["dose_rate"][0] - b["dose_rate"][3]
        b["v_dose"] = (
            "not read (invalid)" if bad & {"R0", "D0", "D1", "D2"} else
            "dose-dependent" if b["p_dose_holm"] < ALPHA and drop > DOSE else "not shown")


def show(b: dict):
    rt = b["rate"]
    print(f"\n=== {b['model']} ===")
    flag = "" if b["link_ok"] else "   <- the replay differs from the corpus"
    print("link" + flag)
    for k, x in b["link"].items():
        print(f"  {k:8s} recorded {x['recorded']:.2f} (n={x['n_recorded']})  replay {x['replay']:.2f}"
              f"  Fisher p = {x['p']:.3f}")
    print("cooperation by variant:  " + "  ".join(f"{v} {rt[v]:.2f}" for v in rt))
    if b["bad"]:
        print(f"  >15% invalid calls: {sorted(b['bad'])}")
    print(f"writers  harm W2-W0 {b['harm_w']:+.2f} (p {b['p_harm_w_holm']:.3f});"
          f" {b['n_worded_w']} worded contexts, gap {b['gap_w']:+.2f}, recovery {b['recovery_w']:.2f}"
          f" (W1>W0 p {b['p_copy_w_holm']:.3f}, W2>W1 p {b['p_stance_w_holm']:.3f})"
          f"  -> {b['v_writer']}")
    print(f"         harm W2-W0 with an action word {b['harm_w_worded']:+.2f}, "
          f"without {b['harm_w_unworded']:+.2f} (descriptive)")
    print(f"         S1-W0 {b['attr']:+.2f} (p {b['p_attr_holm']:.3f})  -> {b['v_attr']}")
    print(f"readers  harm W2-R0 {b['harm_r']:+.2f} (p {b['p_harm_r_holm']:.3f});"
          f" {b['n_worded_r']} worded contexts, gap {b['gap_r']:+.2f}, recovery {b['recovery_r']:.2f}"
          f" (R1>R0 p {b['p_word_r_holm']:.3f}, W2>R1 p {b['p_intent_r_holm']:.3f})"
          f"  -> {b['v_reader']}")
    dr = b["dose_rate"]
    print(f"dose     hub, hostile of 3: " + "  ".join(f"{k}: {dr[k]:.2f}" for k in sorted(dr))
          + f"  (z {b['dose_z']:+.2f}, p {b['p_dose_holm']:.3f}, {b['n_hub']} hubs)  -> {b['v_dose']}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", nargs="+", required=True, help="replay.py output (.jsonl).")
    ap.add_argument("--contexts", default=os.path.join(HERE, "replay", "contexts.json"))
    ap.add_argument("--csv", default=None)
    args = ap.parse_args()
    paths = sorted({p for pat in args.results for p in glob.glob(pat)} or set(args.results))
    df = load(paths)
    with open(args.contexts, encoding="utf-8") as f:
        contexts = json.load(f)["contexts"]
    blocks = [model_block(df, contexts, m) for m in sorted(df["model"].unique())]
    verdicts(blocks)
    for b in blocks:
        show(b)
    ok = [b for b in blocks if b["link_ok"]]
    print(f"\n=== Summary: {len(ok)} of {len(blocks)} models where the replay reproduces the corpus ===")
    for key, label in (("v_writer", "writers"), ("v_attr", "attribution"),
                       ("v_reader", "readers"), ("v_dose", "dose")):
        counts = pd.Series([b[key] for b in ok]).value_counts()
        print(f"  {label:12s} " + ", ".join(f"{v}: {n}" for v, n in counts.items()))
    if len(blocks) < 5:
        print(f"  ({len(blocks)} of 5 models: Holm ran over these only; re-read with all five)")
    if args.csv:
        flat = []
        for b in blocks:
            row = {k: v for k, v in b.items() if not isinstance(v, (dict, set))}
            row.update({f"rate_{k}": v for k, v in b["rate"].items()})
            row.update({f"dose_{k}": v for k, v in b["dose_rate"].items()})
            row.update({f"link_{k}_p": x["p"] for k, x in b["link"].items()})
            flat.append(row)
        pd.DataFrame(flat).to_csv(args.csv, index=False)
        print(f"-> {args.csv}")


if __name__ == "__main__":
    main()
