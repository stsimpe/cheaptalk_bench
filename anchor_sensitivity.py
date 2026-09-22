"""Worst-case sensitivity of the harm ledger to invalid decisions.

Invalid decisions (unparseable or out-of-vocabulary actions) are excluded from
every cooperation rate. That is harmless only if they are missing at random,
and they are not: the no_comm anchors carry most of them (baseline PD: Qwen3-4B
5.6% star / 10.9% ring, Llama 4.4% / 9.4%) while baseline cheap talk has 0%.
Since every ledger delta is measured against such an anchor, the anchor's
missingness can move the verdict.

This recomputes the ledger under the imputation least favourable to cheap
talk: every invalid decision in the anchor counted as Cooperate (raising the
anchor), every invalid decision in the open-channel arm counted as Defect
(lowering the arm). A cell that stays helpful under that bound does not owe its
verdict to missingness.

Usage:
    python anchor_sensitivity.py --in-dir cross_model_output_final
"""
from __future__ import annotations

import argparse
import os

import pandas as pd

from harm_ledger import BAND, KIND


def rates(sub: pd.DataFrame) -> pd.DataFrame:
    """Per-run cooperation under the three readings of an invalid decision."""
    c = sub["coop_rate_overall"]
    r = sub["invalid_rate"].fillna(0.0)
    return pd.DataFrame({
        "measured": c,
        "invalid_as_coop": c * (1 - r) + r,
        "invalid_as_defect": c * (1 - r),
    })


def build(master: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (model, topology, game), sub in master.groupby(["model_id", "topology", "game"]):
        a = sub[sub["cell"] == "no_comm"]
        if a["coop_rate_overall"].dropna().empty:
            continue
        ar = rates(a).mean()
        for cell, kind in KIND.items():
            o = sub[sub["cell"] == cell]
            if o["coop_rate_overall"].dropna().empty:
                continue
            orr = rates(o).mean()
            rows.append({
                "model_id": model, "topology": topology, "game": game,
                "cell": cell, "kind": kind,
                "anchor_invalid": a["invalid_rate"].mean(),
                "arm_invalid": o["invalid_rate"].mean(),
                "delta": orr["measured"] - ar["measured"],
                "delta_worst": orr["invalid_as_defect"] - ar["invalid_as_coop"],
            })
    return pd.DataFrame(rows)


def report(d: pd.DataFrame) -> None:
    for game in ["pd", "sh"]:
        g = d[d["game"] == game]
        if g.empty:
            continue
        print(f"\n=== {game.upper()} -- {len(g)} open-channel cells, band +-{BAND} ===")
        print(f"  {'kind':26s} {'harmful (measured)':>19s} {'harmful (worst case)':>21s}"
              f" {'mean d':>7s} {'worst d':>8s}")
        for kind in ["meaningful", "degraded", "adversarial (prompt)",
                     "adversarial (messages)"]:
            k = g[g["kind"] == kind]
            if k.empty:
                continue
            print(f"  {kind:26s} {int((k['delta'] < -BAND).sum()):>12d}/{len(k):<6d}"
                  f" {int((k['delta_worst'] < -BAND).sum()):>14d}/{len(k):<6d}"
                  f" {k['delta'].mean():+7.2f} {k['delta_worst'].mean():+8.2f}")
        flipped = g[(g["delta"] >= -BAND) & (g["delta_worst"] < -BAND)]
        if not flipped.empty:
            print("\n  cells harmful only under the worst case:")
            for _, r in flipped.sort_values("delta_worst").iterrows():
                print(f"    {r['model_id']:22s} {r['topology']:6s} {r['cell']:38s} "
                      f"d {r['delta']:+.2f} -> {r['delta_worst']:+.2f}  "
                      f"(invalid: anchor {r['anchor_invalid']:.1%}, arm {r['arm_invalid']:.1%})")
        else:
            print("\n  no cell changes verdict under the worst case.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in-dir", default="cross_model_output_final")
    args = ap.parse_args()
    master = pd.read_csv(os.path.join(args.in_dir, "cross_model_master.csv"))
    d = build(master)
    report(d)
    out = os.path.join(args.in_dir, "anchor_sensitivity.csv")
    d.to_csv(out, index=False)
    print(f"\n-> {out}")


if __name__ == "__main__":
    main()
