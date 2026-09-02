"""Harmful-vs-helpful ledger: the direct answer to the thesis's core question.

    Does cheap talk push towards harmful or helpful equilibria?

Every cell with an OPEN channel is compared against the `no_comm` anchor of its
OWN (model, topology, game). That is the only fair comparison -- anchors range
from 0.04 to 0.67 in PD, so a raw cooperation rate says nothing on its own.

A cell counts as harmful at delta < -0.05 and helpful at delta > +0.05; the band
between is reported as neutral rather than folded into either side.

Cells are grouped by WHAT FLOWS THROUGH the channel, because that -- not the
channel's existence -- is what sets the sign:

  meaningful   baseline_cheap_talk, the prosocial/neutral framings, and the
               context arms whose messages are unconstrained
  degraded     no_sense (scrambled), silence (empty), counterfactual (wrong
               sender attribution)
  adversarial  framing_competitive -- the competitive frame shaping the messages
               themselves. Note that framing_competitive_context[cheap_talk] is
               NOT adversarial content: the frame sits in the system prompt and
               the messages are ordinary, which is exactly the contrast that
               shows the harm is carried by content and not by disposition.

Usage:
    python harm_ledger.py --in-dir cross_model_output_final
"""
from __future__ import annotations

import argparse
import os

import pandas as pd

MEANINGFUL = [
    "baseline_cheap_talk",
    "framing_business",
    "framing_team",
    "framing_business_context[cheap_talk]",
    "framing_team_context[cheap_talk]",
]
DEGRADED = ["no_sense", "silence", "counterfactual"]
ADVERSARIAL = ["framing_competitive"]
# Adversarial frame, but delivered through the system prompt with ordinary
# messages -- kept separate because it is the control that identifies the route.
ADVERSARIAL_PROMPT = ["framing_competitive_context[cheap_talk]"]

KIND = {c: "meaningful" for c in MEANINGFUL}
KIND.update({c: "degraded" for c in DEGRADED})
KIND.update({c: "adversarial (messages)" for c in ADVERSARIAL})
KIND.update({c: "adversarial (prompt)" for c in ADVERSARIAL_PROMPT})

BAND = 0.05


def build(master: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (model, topology, game), sub in master.groupby(
            ["model_id", "topology", "game"]):
        anchor = sub[sub["cell"] == "no_comm"]["coop_rate_overall"].mean()
        if pd.isna(anchor):
            continue
        for cell, kind in KIND.items():
            vals = sub[sub["cell"] == cell]["coop_rate_overall"].dropna()
            if vals.empty:
                continue
            rows.append({
                "model_id": model,
                "topology": topology,
                "game": game,
                "cell": cell,
                "kind": kind,
                "anchor": anchor,
                "value": vals.mean(),
                "delta": vals.mean() - anchor,
                "n": len(vals),
            })
    return pd.DataFrame(rows)


def report(d: pd.DataFrame) -> None:
    for game in ["pd", "sh"]:
        g = d[d["game"] == game]
        if g.empty:
            continue
        up = int((g["delta"] > BAND).sum())
        down = int((g["delta"] < -BAND).sum())
        print(f"\n=== {game.upper()} -- {len(g)} open-channel cells ===")
        print(f"  helpful {up:3d}   neutral {len(g)-up-down:3d}   harmful {down:3d}")
        print(f"  {'what flows through the channel':26s} {'mean d':>7s}  harmful"
              f"   without gemma-2-2b")
        for kind in ["meaningful", "degraded",
                     "adversarial (prompt)", "adversarial (messages)"]:
            k = g[g["kind"] == kind]
            if k.empty:
                continue
            nk = k[k["model_id"] != "gemma-2-2b-it"]
            print(f"  {kind:26s} {k['delta'].mean():+7.2f}  "
                  f"{int((k['delta'] < -BAND).sum()):3d}/{len(k):<3d}"
                  f"      {int((nk['delta'] < -BAND).sum())}/{len(nk)}")
        worst = g[g["delta"] < -BAND].sort_values("delta")
        if not worst.empty:
            print(f"\n  harmful cells, worst first:")
            for _, r in worst.iterrows():
                print(f"    {r['delta']:+.2f}  {r['model_id']:22s} {r['topology']:6s} "
                      f"{r['cell']:40s} ({r['anchor']:.2f} -> {r['value']:.2f})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in-dir", default="cross_model_output_final")
    ap.add_argument("--out", default=None,
                    help="Write the per-cell ledger as CSV here.")
    args = ap.parse_args()

    path = os.path.join(args.in_dir, "cross_model_master.csv")
    master = pd.read_csv(path)
    if "cell" not in master.columns:
        raise SystemExit(
            f"{path} has no 'cell' column, so it predates the condition fix.\n"
            "Re-run cross_model_analysis.py before trusting any ledger built "
            "from it -- the context scenarios' two arms would be pooled."
        )
    d = build(master)
    report(d)
    out = args.out or os.path.join(args.in_dir, "harm_ledger.csv")
    d.to_csv(out, index=False)
    print(f"\n-> {out}")


if __name__ == "__main__":
    main()
