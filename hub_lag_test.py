"""Does the star's hub lead its leaves? A lagged test with a permutation null.

The thesis first read hub - leaf ~ 0 and a hub/leaf correlation of 0.97 as
refuting hub leadership. Neither can: a hub that the leaves follow produces
exactly equal rates and a high correlation. What can is timing -- does one
side's previous action predict the other's next one, beyond its own habit?

For every hub-leaf edge of a star run and every round t >= 2, two dyadic
logistic regressions (PD, valid decisions only):

    leaf_t ~ leaf_{t-1} + hub_{t-1}      beta_hub  = hub -> leaf influence
    hub_t  ~ hub_{t-1}  + leaf_{t-1}     beta_leaf = leaf -> hub influence

Controlling for the agent's own previous action is what separates influence
from inertia. The statistic is beta_hub - beta_leaf.

Null: within each run the partner's series is circularly shifted by a random
lag (2..n-2 rounds). That keeps each series' own autocorrelation and the
cell's composition but breaks the timing between the two agents; both betas
are refitted on every shuffle. A small ridge keeps the fit finite when a cell
never switches.

Caveat stated up front: a leaf's only partner is the hub, so "leaf follows
hub" is also plain reciprocity (tit-for-tat); the hub has three partners and
each leaf is one third of its input. A positive difference therefore shows
asymmetric responsiveness, not steering.

Usage:
    python hub_lag_test.py --roots <star run folders> [--cells silence no_sense no_comm]
"""
from __future__ import annotations

import argparse
import os

import numpy as np
import pandas as pd
from scipy.optimize import minimize

from analysis import scenario_of
from cross_model_analysis import discover_records, normalise_model_id

RIDGE = 0.1
N_PERM = 2000


def logit_beta(X: np.ndarray, y: np.ndarray) -> np.ndarray:
    """Ridge-penalised logistic regression (intercept unpenalised)."""
    X1 = np.column_stack([np.ones(len(y)), X])

    def nll(b):
        z = X1 @ b
        return np.sum(np.logaddexp(0, z) - y * z) + RIDGE * np.sum(b[1:] ** 2)

    def grad(b):
        p = 1 / (1 + np.exp(-(X1 @ b)))
        g = X1.T @ (p - y)
        g[1:] += 2 * RIDGE * b[1:]
        return g

    return minimize(nll, np.zeros(X1.shape[1]), jac=grad, method="BFGS").x


def series(record: dict) -> np.ndarray | None:
    """Rounds x agents, 1 = cooperate, 0 = defect, nan = invalid."""
    rows = []
    for x in record["history"]:
        a = x["actions"]
        rows.append([1.0 if a[str(i)] == "Cooperate" else 0.0 if a[str(i)] == "Defect"
                     else np.nan for i in range(len(a))])
    return np.array(rows)


def design(runs: list[np.ndarray], shifts: list[int] | None = None):
    """Stack the two dyadic regressions. shifts[k] lags the partner in run k."""
    Xl, yl, Xh, yh = [], [], [], []
    for k, S in enumerate(runs):
        T = S.shape[0]
        hub = S[:, 0]
        for leaf in range(1, S.shape[1]):
            lf = S[:, leaf]
            hub_p = np.roll(hub, shifts[k]) if shifts else hub   # partner for leaf
            lf_p = np.roll(lf, shifts[k]) if shifts else lf      # partner for hub
            for t in range(1, T):
                if not np.isnan([lf[t], lf[t - 1], hub_p[t - 1]]).any():
                    Xl.append([lf[t - 1], hub_p[t - 1]]); yl.append(lf[t])
                if not np.isnan([hub[t], hub[t - 1], lf_p[t - 1]]).any():
                    Xh.append([hub[t - 1], lf_p[t - 1]]); yh.append(hub[t])
    return (np.array(Xl), np.array(yl)), (np.array(Xh), np.array(yh))


def betas(runs, shifts=None):
    (Xl, yl), (Xh, yh) = design(runs, shifts)
    return logit_beta(Xl, yl)[2], logit_beta(Xh, yh)[2]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--roots", nargs="+", required=True)
    ap.add_argument("--cells", nargs="+", default=["silence", "no_sense", "no_comm"])
    ap.add_argument("--game", default="pd")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out-dir", default="cross_model_output_final")
    args = ap.parse_args()
    rng = np.random.default_rng(args.seed)

    by_model: dict[str, list[np.ndarray]] = {}
    for _, rec in discover_records(args.roots):
        cfg = rec["config"]
        if (rec["topology"].get("type", "star") != "star" or cfg["game"] != args.game
                or scenario_of(rec) not in args.cells):
            continue
        by_model.setdefault(normalise_model_id(cfg["model"]["model_id"]), []).append(series(rec))

    print(f"star, {args.game.upper()}, cells {args.cells}; null: {N_PERM} circular shifts\n")
    print(f"{'model':24s}{'runs':>5s}{'b hub->leaf':>13s}{'b leaf->hub':>13s}"
          f"{'difference':>12s}{'p (diff)':>10s}{'p hub->leaf':>13s}")
    rows = []
    for model, runs in sorted(by_model.items()):
        b_h, b_l = betas(runs)
        T = runs[0].shape[0]
        null = np.array([betas(runs, [int(rng.integers(2, T - 1)) for _ in runs])
                         for _ in range(N_PERM)])
        d_obs, d_null = b_h - b_l, null[:, 0] - null[:, 1]
        p_diff = (1 + np.sum(np.abs(d_null) >= abs(d_obs))) / (N_PERM + 1)
        p_hub = (1 + np.sum(null[:, 0] >= b_h)) / (N_PERM + 1)
        print(f"{model:24s}{len(runs):5d}{b_h:13.2f}{b_l:13.2f}{d_obs:12.2f}"
              f"{p_diff:10.3f}{p_hub:13.3f}")
        rows.append({"model_id": model, "runs": len(runs), "beta_hub_to_leaf": b_h,
                     "beta_leaf_to_hub": b_l, "difference": d_obs,
                     "p_difference": p_diff, "p_hub_to_leaf": p_hub})
    out = os.path.join(args.out_dir, "hub_lag_test.csv")
    pd.DataFrame(rows).to_csv(out, index=False)
    print(f"\n-> {out}")


if __name__ == "__main__":
    main()
