"""Four agents or eight: the reading rules of docs/grid_n8_plan.md.

Reads plain grid trees (sessions A, B and C of run_all_scenarios.py) with four
and with eight agents, and the plan's drift control, and prints per model:

  rule 1    at eight: runs per topology and cell, invalid decisions per
            topology, and the round-1 message prompt tokens of
            baseline_cheap_talk per topology, the same for every model
  drift     the control's two cells (four agents, the ring, PD
            baseline_cheap_talk and no_comm, run in the eight-agent period)
            against the same cells of the four-agent grid
  the grid  at eight beside four, per cell, game and topology
  rule 2    size at a fixed degree: the ring at eight against the ring at four
  rule 3    degree at a fixed size: the clique at eight against the ring at
            eight, beside the same contrast at four
  rule 4    the star at eight against the ring at eight, beside the same
            contrast at four; descriptive: the leaves alone
  rule 5    the hub of seven: on the star, the hub against the mean of its
            leaves, cell by cell, at eight beside four; descriptive: their
            correlation over runs
  rule 6    the markers M1, M2, M3 and S1 at eight against four

A contrast compares two sets of cells one by one over the 28 grid cells (14
cells x 2 games): higher or lower by at least 0.05, tied otherwise, with a
two-sided exact sign test on the cells that are not tied, per model and
pooled over the models. Its verdict is "higher" or "lower" at p < 0.05, and
"not detected" otherwise. A cell's value is the mean of its run means over
valid decisions, as in scale_report.py.

Only plain grid runs count (scale_report.py's filter). A model whose rule 1
fails is not read; rules 2 and 6, which compare two periods, are not read for
a model whose drift control moved.

Usage:
    python size_report.py --four <trees of four> --eight <trees of eight>
                          [--drift <the control's trees>]
"""
from __future__ import annotations

import argparse
import glob
import json
import math
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from games import GAMES  # noqa: E402
from intent_report import plain_grid  # noqa: E402
from scale_report import CELLS, MAX_INVALID, cell_name  # noqa: E402

TOPOS = ("star", "cycle", "clique")
GAME_ORDER = ("pd", "sh")
RUNS_PER_CELL = 5
TIE = 0.05        # a contrast's cells closer than this are tied
ALPHA = 0.05      # the sign test, two-sided
HOLD = 0.20       # rule 6 and the drift control: a move below this holds
COUPLED = 0.90    # rule 5: a hub-leaf correlation at or above this is "coupled"
DRIFT_CELLS = ("baseline_cheap_talk", "no_comm")      # PD, the ring, four agents
MARKERS = (  # name, game, cells, topologies, gap (second cell minus first)
    ("M1 talk", "pd", ("baseline_cheap_talk",), TOPOS, False),
    ("M2 no channel", "pd", ("no_comm", "silence", "no_sense"), TOPOS, False),
    ("M3 frame gap", "pd", ("framing_team", "framing_team_context[cheap_talk]"), ("star", "clique"), True),
    ("S1 empty channel", "sh", ("silence", "no_sense"), ("star", "clique"), False),
)


class Grid:
    """Plain grid runs of one size: runs[(model, game, topology, cell)] is a
    list of {"coop", and on the star "hub" and "leaves"}, with rule 1's
    counts per (model, topology)."""

    def __init__(self, roots: list[str], n_agents: int):
        self.n = n_agents
        self.runs = defaultdict(list)
        self.decisions, self.invalid = defaultdict(int), defaultdict(int)
        self.tokens = defaultdict(set)
        self.wrong_size = defaultdict(int)
        seen = set()
        for root in roots:
            for f in sorted(glob.glob(os.path.join(root, "**", "*_run*.json"), recursive=True)):
                path = os.path.abspath(f)
                if f"{os.sep}zips{os.sep}" in path or path in seen:
                    continue
                seen.add(path)
                try:
                    with open(f, encoding="utf-8") as fh:
                        d = json.load(fh)
                    cfg = dict(d["config"])
                except (json.JSONDecodeError, KeyError, UnicodeDecodeError):
                    continue
                cfg["topology"] = cfg.get("topology") or "star"
                if not plain_grid(cfg) or cell_name(cfg) not in CELLS:
                    continue
                if cfg.get("n_agents", 4) != n_agents:
                    self.wrong_size[(root, cfg.get("n_agents", 4))] += 1
                    continue
                self._add(d, cfg)

    def _add(self, d: dict, cfg: dict) -> None:
        game = GAMES[cfg["game"]]
        model = cfg["model"]["model_id"].split("/")[-1]
        topo, hist = cfg["topology"], d["history"]

        def rate(acts):
            valid = [a for a in acts if a in game.action_labels]
            return sum(a == game.cooperative_action for a in valid) / len(valid) if valid else None

        every = [a for r in hist for a in r["actions"].values()]
        self.decisions[(model, topo)] += len(every)
        self.invalid[(model, topo)] += sum(a not in game.action_labels for a in every)
        if cell_name(cfg) == "baseline_cheap_talk" and cfg["game"] == "pd" and hist:
            for calls in hist[0].get("llm_calls", {}).values():
                self.tokens[(model, topo)].update(
                    c["prompt_tokens"] for c in calls
                    if c.get("phase") == "message" and c.get("prompt_tokens") is not None)
        coop = rate(every)
        if coop is None:
            return
        rec = {"coop": coop}
        if topo == "star":
            hub = str(d.get("topology", {}).get("hub_id", 0))
            rec["hub"] = rate([r["actions"][hub] for r in hist if hub in r["actions"]])
            rec["leaves"] = rate([a for r in hist for k, a in r["actions"].items() if k != hub])
        self.runs[(model, cfg["game"], topo, cell_name(cfg))].append(rec)

    def models(self) -> list[str]:
        return sorted({k[0] for k in self.runs})

    def cell(self, model: str, game: str, topo: str, c: str, part: str = "coop") -> float:
        vals = [r[part] for r in self.runs.get((model, game, topo, c), []) if r.get(part) is not None]
        return sum(vals) / len(vals) if vals else float("nan")

    def cells(self, model: str, topo: str, part: str = "coop") -> dict:
        """{(game, cell): value} over the 28 grid cells that have runs."""
        out = {}
        for g in GAME_ORDER:
            for c in CELLS:
                v = self.cell(model, g, topo, c, part)
                if v == v:
                    out[(g, c)] = v
        return out


def sign_p(up: int, down: int) -> float:
    n = up + down
    if n == 0:
        return 1.0
    k = min(up, down)
    return min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n)


def contrast(a: dict, b: dict) -> tuple[int, int, int, int]:
    """Cells of a against the same cells of b: higher, lower, tied, missing."""
    up = down = tie = 0
    for k in a.keys() & b.keys():
        d = a[k] - b[k]
        if d >= TIE:
            up += 1
        elif d <= -TIE:
            down += 1
        else:
            tie += 1
    return up, down, tie, len(a.keys() ^ b.keys())


def verdict(up: int, down: int) -> str:
    p = sign_p(up, down)
    if p < ALPHA:
        return "higher" if up > down else "lower"
    return "not detected"


def show(label: str, up: int, down: int, tie: int, missing: int = 0, read: bool = True) -> None:
    extra = f", {missing} cell(s) missing on one side" if missing else ""
    v = verdict(up, down) if read else "not read"
    print(f"   {label:34} higher {up:2d}, lower {down:2d}, tied {tie:2d}{extra}; "
          f"sign p = {sign_p(up, down):.3f} -> {v}")


def pearson(xs: list[float], ys: list[float]) -> float:
    n = len(xs)
    if n < 3:
        return float("nan")
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    if not sxx or not syy:
        return float("nan")
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / math.sqrt(sxx * syy)


def marker(grid: Grid, model: str, game: str, cells: tuple, topos: tuple, gap: bool) -> float:
    vals = []
    for t in topos:
        cv = [grid.cell(model, game, t, c) for c in cells]
        if any(x != x for x in cv):
            return float("nan")
        vals.append(cv[1] - cv[0] if gap else sum(cv) / len(cv))
    return sum(vals) / len(vals)


def f2(x: float) -> str:
    return " -  " if x != x else f"{x:.2f}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--four", nargs="+", required=True, help="the four-agent grid trees")
    ap.add_argument("--eight", nargs="+", required=True, help="the eight-agent grid trees")
    ap.add_argument("--drift", nargs="*", default=[], help="the drift control's trees (four agents)")
    args = ap.parse_args()
    four, eight = Grid(args.four, 4), Grid(args.eight, 8)
    control = Grid(args.drift, 4) if args.drift else None
    for g, name in ((four, "--four"), (eight, "--eight")) + (((control, "--drift"),) if control else ()):
        for (root, n), k in sorted(g.wrong_size.items()):
            print(f"note: {k} plain grid run(s) with {n} agents under {name} {root} are left out")
    models = [m for m in eight.models() if m in four.models()]
    if not models:
        raise SystemExit("no model has plain grid runs at both four and eight agents")

    # ------------------------------------------------------------- rule 1
    print(f"######## rule 1 at eight agents: {RUNS_PER_CELL} runs in each of the {len(CELLS) * 2} cells "
          f"per topology, at most {MAX_INVALID:.0%} invalid decisions per topology, and the same "
          f"round-1 message prompt tokens (PD baseline_cheap_talk) for every model")
    passed = {}
    for m in models:
        ok = True
        print(f"  {m}")
        for t in TOPOS:
            counts = [len(eight.runs.get((m, g, t, c), [])) for g in GAME_ORDER for c in CELLS]
            n, bad = eight.decisions[(m, t)], eight.invalid[(m, t)]
            full = all(k == RUNS_PER_CELL for k in counts)
            ok &= full and bool(n) and bad <= MAX_INVALID * n and bool(eight.tokens[(m, t)])
            print(f"     {t:6}: {sum(counts)} runs, cells with {RUNS_PER_CELL}: "
                  f"{sum(k == RUNS_PER_CELL for k in counts)}/{len(counts)}; invalid {bad}/{n} = "
                  f"{bad / n if n else float('nan'):.3f}; tokens {sorted(eight.tokens[(m, t)])}")
        passed[m] = ok
    for t in TOPOS:
        sets = {m: frozenset(eight.tokens[(m, t)]) for m in models}
        same = len(set(sets.values())) == 1
        print(f"   tokens on the {t:6}: " + ("the same for every model" if same else "NOT THE SAME"))
        if not same:
            passed = {m: False for m in passed}
    for m in models:
        print(f"   {m}: " + ("passes these checks; rule 1 also needs verify_prompts.py and "
                             "audit_corpus.py --n-agents 8, which this script does not run"
                             if passed[m] else "FAILS: nothing else is read for this model"))
    readable = [m for m in models if passed[m]]

    # ------------------------------------------------------------- drift
    print("\n######## the drift control: four agents, the ring, PD, run in the eight-agent period, "
          f"against the four-agent grid (holds below {HOLD:.2f})")
    no_drift = {}
    for m in models:
        if control is None or not any(k[0] == m for k in control.runs):
            print(f"   {m}: no control runs; rules 2 and 6 not read")
            no_drift[m] = False
            continue
        ok = True
        for c in DRIFT_CELLS:
            x, y = control.cell(m, "pd", "cycle", c), four.cell(m, "pd", "cycle", c)
            k = len(control.runs.get((m, "pd", "cycle", c), []))
            within = x == x and y == y and abs(x - y) < HOLD
            ok &= within and k == RUNS_PER_CELL
            print(f"   {m:20} {c:20} control {f2(x)} ({k} runs) against grid {f2(y)} -> "
                  f"{'within' if within else 'MOVED'}")
        no_drift[m] = ok
        print(f"   {m:20} -> " + ("no drift detected" if ok else "drift: rules 2 and 6 not read"))

    # ------------------------------------------------------------- the grid
    for m in models:
        print(f"\n######## {m}: the grid at four | eight agents")
        print(f"{'cell':40}" + "".join(f"{g.upper()} {t:13}" for g in GAME_ORDER for t in TOPOS))
        for c in CELLS:
            row = []
            for g in GAME_ORDER:
                for t in TOPOS:
                    row.append(f"{f2(four.cell(m, g, t, c))}|{f2(eight.cell(m, g, t, c))}")
            print(f"{c:40}" + "".join(f"{x:17}" for x in row))

    # ------------------------------------------------------------- rules 2-4
    def rule(title, pairs, read_ok):
        print(f"\n######## {title}")
        for label, left, right, ref in pairs:
            tot = [0, 0, 0]
            reft = [0, 0, 0]
            print(f"  {label}")
            for m in models:
                ok = m in readable and read_ok(m)
                up, down, tie, miss = contrast(left(m), right(m))
                show(m, up, down, tie, miss, ok)
                if ok:
                    tot[0] += up; tot[1] += down; tot[2] += tie
                if ref:
                    ru, rd, rt, rm = contrast(ref[0](m), ref[1](m))
                    show(f"{m} at four", ru, rd, rt, rm)
                    reft[0] += ru; reft[1] += rd; reft[2] += rt
            k = sum(1 for m in models if m in readable and read_ok(m))
            show(f"pooled over {k} model{'s' if k != 1 else ''}", *tot)
            if ref:
                show(f"pooled at four, {len(models)} model{'s' if len(models) != 1 else ''}", *reft)

    rule("rule 2, size at a fixed degree: the ring at eight against the ring at four",
         [("ring 8 vs ring 4", lambda m: eight.cells(m, "cycle"), lambda m: four.cells(m, "cycle"), None)],
         lambda m: no_drift.get(m, False))
    rule("rule 3, degree at a fixed size: the clique against the ring at eight (degree 7 against 2), "
         "and at four (3 against 2)",
         [("clique 8 vs ring 8", lambda m: eight.cells(m, "clique"), lambda m: eight.cells(m, "cycle"),
           (lambda m: four.cells(m, "clique"), lambda m: four.cells(m, "cycle")))],
         lambda m: True)
    rule("rule 4, the star at eight against the ring at eight, and at four",
         [("star 8 vs ring 8", lambda m: eight.cells(m, "star"), lambda m: eight.cells(m, "cycle"),
           (lambda m: four.cells(m, "star"), lambda m: four.cells(m, "cycle")))],
         lambda m: True)
    print("  descriptive, not rules: the leaves alone")
    for m in models:
        for label, a, b in (("leaves 8 vs ring 8", eight.cells(m, "star", "leaves"), eight.cells(m, "cycle")),
                            ("leaves 8 vs leaves 4", eight.cells(m, "star", "leaves"), four.cells(m, "star", "leaves")),
                            ("hub 8 vs hub 4", eight.cells(m, "star", "hub"), four.cells(m, "star", "hub"))):
            up, down, tie, miss = contrast(a, b)
            print(f"   {m:20} {label:22} higher {up:2d}, lower {down:2d}, tied {tie:2d}; "
                  f"sign p = {sign_p(up, down):.3f}")

    # ------------------------------------------------------------- rule 5
    rule("rule 5, the hub of seven: on the star, the hub against the mean of its leaves, cell by cell, "
         "at eight and at four",
         [("hub 8 vs leaves 8", lambda m: eight.cells(m, "star", "hub"), lambda m: eight.cells(m, "star", "leaves"),
           (lambda m: four.cells(m, "star", "hub"), lambda m: four.cells(m, "star", "leaves")))],
         lambda m: True)
    print(f"  descriptive: the correlation over star runs between the hub and the mean of its leaves "
          f"(coupled at r >= {COUPLED:.2f}), and the hub minus its leaves, per model")
    for m in models:
        for size, grid in ((4, four), (8, eight)):
            hubs, leaves = [], []
            for (mm, g, t, c), rs in grid.runs.items():
                if mm == m and t == "star":
                    for r in rs:
                        if r.get("hub") is not None and r.get("leaves") is not None:
                            hubs.append(r["hub"])
                            leaves.append(r["leaves"])
            r = pearson(hubs, leaves)
            gap = sum(h - lf for h, lf in zip(hubs, leaves)) / len(hubs) if hubs else float("nan")
            word = "" if r != r else (" -> coupled" if r >= COUPLED else " -> looser")
            print(f"   {m:20} at {size}: {len(hubs)} runs, r = {f2(r)}{word}, hub minus leaves {gap:+.2f}")

    # ------------------------------------------------------------- rule 6
    print(f"\n######## rule 6, the markers at four and eight (holds below {HOLD:.2f})")
    print(f"{'model':22}" + "".join(f"{name:27}" for name, *_ in MARKERS))
    for m in models:
        row = []
        for name, game, cells, topos, gap in MARKERS:
            a, b = marker(four, m, game, cells, topos, gap), marker(eight, m, game, cells, topos, gap)
            if m not in readable or not no_drift.get(m, False):
                word = "not read"
            elif a != a or b != b:
                word = "missing"
            else:
                word = "holds" if abs(b - a) < HOLD else ("moves up" if b > a else "moves down")
            row.append(f"{f2(a)} -> {f2(b)} {word}")
        print(f"{m:22}" + "".join(f"{x:27}" for x in row))
    for name, game, cells, topos, gap in MARKERS:
        what = f"{cells[1]} - {cells[0]}" if gap else ", ".join(cells)
        print(f"   {name}: {game.upper()} {what}; over {', '.join(topos)}")


if __name__ == "__main__":
    main()
