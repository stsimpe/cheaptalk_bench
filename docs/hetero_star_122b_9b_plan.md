# A third mixed star: Qwen3.5-122B in the hub, Qwen3.5-9B in the leaves

This is the plan for the third exploratory experiment with two models in one
network, on the lab server. It was first written at 02:09 on 2026-11-12, before
its smoke run (02:12). Its same-day control lane was added at 02:20, after its
mixed lane had started (02:18) and before any run of it had ended. Both lanes
ended by 03:11; the plan was committed after that, before any of their runs was
read. Its rules and prediction are fixed here. It follows
`docs/hetero_star_plan.md` (the 122B in the hub, the 27B in the leaves) and
`docs/hetero_star_27b_9b_plan.md` (the 27B in the hub, the 9B in the leaves),
and takes their definitions, hand checks and code.

## Question

The 122B hub has now been seen with two neighbourhoods, both on 2026-11-11,
after the server's model update:
- with three 27B leaves that keep their word, it cooperated 0.95;
- with three 122B leaves, in its own star, 0.71, with two of five runs
  collapsing.

This plan gives it a third neighbourhood: three 9B leaves, which defect and
mostly say so (80% of their messages announce defection in the 9B's forecast
cell).
- **The hub.** The 122B believes talk and acts on its beliefs. After an
  announced defection its forecast of the sender is 13.9 (its star of 11-11),
  and below a belief of 50 it cooperates 0.33. Does it follow its leaves into
  defection?
- **The leaves.** The 9B's actions do not follow its beliefs. Does a hub that
  promises, and sometimes lies, change them at all?
- **The lies.** The 122B lies in its own star (19 broken promises in 80
  decisions on 11-11, by hand), mostly as planned defence. Does it lie to
  leaves that announce defection, and do they believe it?

The agents are never told which model a neighbour is.

## Design

- **The mixed star:** agent 0, the hub, is served Qwen/Qwen3.5-122B-A10B;
  agents 1-3, the leaves, Qwen/Qwen3.5-9B. The cell is `forecast_probe`
  (session `PROBE`), as in the first two mixed stars. 5 runs.
- **A same-day control: the 122B alone on the star,** the same cell, 5 runs,
  in a lane beside the mixed star's
  (`tok4096/hetero_122b_9b/runs/Qwen3.5-122B-A10B`). It is the hub's
  reference for rule 2, as in the first mixed star. Its star of 11-11 (the
  first mixed star's control) is reported beside it.
- **The leaves' reference:** the 9B alone on the star, the same day, the
  second mixed star's control (`tok4096/hetero_27b_9b/runs/Qwen3.5-9B`, 240
  leaf decisions). If it ends with fewer than 4 of its 5 runs, the 9B runs
  alone again beside these lanes, and rule 3 reads against that run.
- **A smoke run first:** one run of 2 rounds of the mixed star, into
  `pharos_runs/smoke_hetero_122b_9b/runs`, with the first plan's five checks
  (routing to the 122B and the 9B; no `<think>` block; every forecast call
  parses; 464 round-1 message tokens for every agent; `verify_prompts.py`
  finds nothing).
- **Placement.** `pharos_runs/tok4096/hetero_122b_9b/runs/` holds two trees:
  `Qwen3.5-9B_a0-Qwen3.5-122B-A10B`, the mixed star, and `Qwen3.5-122B-A10B`,
  the control. The campaign zips land in `tok4096/hetero_122b_9b/`.
- **The code:** none beyond the second plan's. `hetero_report.py` reads the
  9B's star of 11-12 as `--control` (the leaves' model), so rule 3 reads the
  leaves against it, either way, and the 122B's same-day star as
  `--hub-home`, so rule 2 reads the hub against it. Rule 5 reads the hub's
  lies, the default of `--lies`.

## References

The stars of the two models, by role (hub = agent 0, leaves = agents 1-3).
Promises and broken promises are the detector's; announced defections follow
the 9B plan's pattern. The payoff is per neighbour and per round.

| model, cell | runs | hub cooperation | leaves cooperation | hub payoff | leaves payoff | hub broken | leaves broken | leaves' messages announcing defection |
|---|---|---|---|---|---|---|---|---|
| 122B, grid baseline (10-30) | 5 | 0.60 | 0.50 | 2.95 | 3.47 | 25/68 | 45/162 | 72/240 |
| 122B, grid no_comm (10-30) | 5 | 0.01 | 0.01 | 2.02 | 2.04 | | | |
| 122B, forecast cell (11-04) | 5 | 0.66 | 0.56 | 3.11 | 3.63 | 21/73 | 49/178 | 56/240 |
| **122B, forecast cell (11-11, after the update)** | 5 | **0.71** | 0.61 | 3.20 | 3.72 | 20/74 | 40/183 | 56/240 |
| 9B, grid baseline (11-06) | 5 | 0.00 | 0.02 | 2.08 | 1.98 | 16/16 | 42/45 | 185/239 |
| 9B, grid no_comm (11-06) | 5 | 0.07 | 0.13 | 2.37 | 2.10 | | | |
| 9B, forecast cell (11-09) | 5 | 0.03 | 0.05 | 2.18 | 2.04 | 16/17 | 33/39 | 192/239 |
| **9B, forecast cell (11-12, after the update)** | 5 | running | running | | | | | |
| **122B, forecast cell (11-12, this plan's control)** | 5 | to be run | to be run | | | | | |

- **The 122B's star of 11-11:**
  - its hub's run means are 0.44, 0.88, 0.88, 1.00 and 0.38;
  - before the talk in round 1, its hub intends to defect in 5 of 5 calls
    (forecast 24.0);
  - its hub cooperates 0.88 at a belief of 50 or more (56 decisions), and
    0.33 below (24);
  - its hub's forecast of a neighbour is 83.9 after the neighbour's promise
    (a round-1 shift of +66.0), and 13.9 after an announced defection;
  - of its hub's 19 broken promises (by hand, in the first mixed star's
    write-up), 5 are planned exploitation (0.26), 10 planned defence, and 2
    and 2 decided after the messages;
  - in its 240 hub-leaf edge-rounds, the hub defects on a cooperating leaf in
    21 and a leaf on a cooperating hub in 46.
- **The 9B** (forecast cell, 11-09): its leaves intend to defect before the
  talk in 15 of 15 calls (forecast 24.0), and cooperate 0.19 at a belief of
  50 or more against 0.03 below. Its leaves' forecast of a neighbour is 31.0
  after a promise.
- **The 122B hub with 27B leaves** (11-11): 0.95, with 3 broken promises.
- **Round-1 message prompt tokens:** 464 for every agent, on both stars.

## Hand checks

Those of `docs/hetero_star_plan.md`: blind, with the same seeds, over the
mixed star's runs and the control's (the 9B's star of 11-12) together. The
second plan's hand check reads that control too; each plan keeps its own
labels. The inverted calls found leave rules 5 and 6, which are given both
with them and without them.

## Reading rules

Every reading is exploratory: one composition, one cell, five runs.

1. **Routing, compliance and the untouched game,** as in the first plan,
   read first. The hub's calls must be answered by Qwen/Qwen3.5-122B-A10B and
   the leaves' by Qwen/Qwen3.5-9B. If rule 1 fails, nothing else is read.
2. **Does the neighbourhood change the hub?** The hub's cooperation in the
   mixed star minus the 122B's hub in its same-day star, the control (80
   decisions each).
   - +0.20 or more: "the leaves raise the hub's cooperation".
   - -0.20 or less: "the leaves lower the hub's cooperation".
   - Within 0.10: "the hub plays as in its own star".
   - In between: "partly".
   - Reported beside it: run means; the 122B's star of 11-11 (0.71) and its
     earlier stars (0.60 and 0.66); the 122B hub with 27B leaves (0.95).
3. **Does the hub change the leaves?** The leaves' cooperation in the mixed
   star minus the 9B's leaves in its star of 11-12 (240 decisions each).
   - +0.20 or more: "the hub raises the leaves' cooperation".
   - -0.20 or less: "the hub lowers the leaves' cooperation".
   - Within 0.10: "the leaves play as in their own star".
   - In between: "partly".
   - Reported beside it: the 9B's earlier stars, and its star of 11-12
     against them.
4. **Who gains at whose expense?** As in the first plan: the hub's payoff per
   neighbour minus the leaves', +0.5 or more "the hub gains at the leaves'
   expense", -0.5 or less "the leaves gain at the hub's expense", else
   "even". Reported beside it: the four kinds of hub-leaf edge-round.
5. **The hub's lies,** as in the first plan. The hub's broken promises that
   have a valid intention before the talk and a belief; read only with at
   least 10, otherwise "too few to read".
   - The share of planned exploitation: 0.50 or more "mostly planned
     exploitation", below 0.25 "rarely", in between "partly".
   - Reported beside it: P and the four kinds in the mixed star and in the
     122B's same-day star; the leaves' forecast of the hub after its kept and
     broken promises, the share of broken promises they believe (50 or
     more), and the AUC; the round-1 shift of a leaf's forecast of the hub
     after the hub's promise.
   - The report's "control" row is the 9B's star (the leaves' reference): its
     hub is a 9B, not part of the rule. The 122B's same-day star is its "hub
     home" row.
6. **Belief and action, by role,** as in the first plan: cooperation at a
   belief of 50 or more against below 50, each side with at least 20
   decisions. A difference of 0.50 or more: "its actions follow its
   beliefs"; below 0.20: "its actions ignore its beliefs"; in between:
   "partly".
7. **Descriptive, not rules:**
   - round 1 before and after the talk, by role;
   - the first defection of each run;
   - does lying pay? By role, as in the first plan;
   - the leaves' broken promises: do the 9B leaves lie to a 122B hub?
   - the 122B hub in its three neighbourhoods side by side: 27B leaves, 122B
     leaves and 9B leaves.

**How the numbers are computed.**
- `hetero_report.py` (default `--lies hub`) prints rules 1-6 and the
  descriptive splits, and reads the hand labels with `--hand`.
- `verify_prompts.py` and `audit_corpus.py` run on both trees.
- The scripts, sheets, keys, labels and outputs are kept beside the runs, in
  `pharos_runs/tok4096/hetero_122b_9b/analysis/`.

## Prediction, stated before the run

- **Rule 1** passes. The risk is the 9B's inversion, as in the second plan.
- **The control** plays as the 122B's star of 11-11: its hub within 0.20 of
  0.71.
- **Rule 2: "the leaves lower the hub's cooperation"** (-0.20 or less against
  the same-day star).
  - The 9B's leaves announce defection in most messages, from round 1.
  - The 122B believes an announced defection (13.9) and mostly acts on what
    it expects.
- **Rule 3: "the leaves play as in their own star".** The 9B's actions do not
  follow its beliefs.
- **Rule 4: "even".** The edges settle on mutual defection.
- **Rule 5:** readable, and "rarely planned exploitation". The hub keeps
  promising while it expects its leaves to defect: its lies are planned
  defence. The leaves believe fewer than half of them.
- **Rule 6:** the leaves' actions ignore their beliefs. The hub's follow its
  beliefs, or its side at 50 or more is too few to read.

## Seen before writing

- Every number of the two models' stars above, and of their other cells.
- The results of the first mixed star, and the second mixed star's plan, its
  smoke run, and a first start of its two lanes (2026-11-12, 02:01), which
  stopped before any run ended. None of the second mixed star's runs had
  ended.
- This plan's own smoke run (02:12), and the start of its mixed lane (02:18),
  before its control lane was added.

No run of this experiment existed when this was first written, apart from
its smoke run. When the control lane was added, no run of the mixed lane had
ended.

## Limits fixed in advance

- **Scope.** One composition, one cell, five runs. The hub is one agent per
  run: 80 decisions.
- **One generation, two sizes.** Both models are Qwen3.5. They differ in
  total size and in architecture: a mixture of experts with 10B active
  parameters, against 9B dense.
- **The leaves' reference is shared.** It is the second mixed star's
  control, run the same day; each plan reads it with its own hand labels.
- **Stated beliefs, the detector, and the 9B's inversions:** as in the second
  plan.
- **Server updates:** as in the first plan.
- **Other compositions** (a 9B hub with 122B leaves) are not part of this
  plan.

## Reproduce

From `cheaptalk_bench`. First the smoke run, then the two lanes side by
side:

```
python campaign.py --provider pharos --model Qwen/Qwen3.5-9B --agent-model 0=Qwen/Qwen3.5-122B-A10B --session PROBE --topology star --games pd --n-runs 1 --n-rounds 2 --max-new-tokens 4096 --out-root ..\pharos_runs\smoke_hetero_122b_9b\runs --zip-mirror=
python campaign.py --provider pharos --model Qwen/Qwen3.5-9B --agent-model 0=Qwen/Qwen3.5-122B-A10B --session PROBE --topology star --games pd --n-runs 5 --n-rounds 16 --max-new-tokens 4096 --out-root ..\pharos_runs\tok4096\hetero_122b_9b\runs --zip-mirror=
python campaign.py --provider pharos --model Qwen/Qwen3.5-122B-A10B --session PROBE --topology star --games pd --n-runs 5 --n-rounds 16 --max-new-tokens 4096 --out-root ..\pharos_runs\tok4096\hetero_122b_9b\runs --zip-mirror=
```

Then the checks, the sheets and the report:

```
python verify_prompts.py ..\pharos_runs\tok4096\hetero_122b_9b\runs\Qwen3.5-9B_a0-Qwen3.5-122B-A10B ..\pharos_runs\tok4096\hetero_122b_9b\runs\Qwen3.5-122B-A10B
python audit_corpus.py ..\pharos_runs\tok4096\hetero_122b_9b\runs\Qwen3.5-9B_a0-Qwen3.5-122B-A10B ..\pharos_runs\tok4096\hetero_122b_9b\runs\Qwen3.5-122B-A10B
python hetero_report.py --mixed ..\pharos_runs\tok4096\hetero_122b_9b\runs\Qwen3.5-9B_a0-Qwen3.5-122B-A10B --control ..\pharos_runs\tok4096\hetero_27b_9b\runs\Qwen3.5-9B --dump ..\pharos_runs\tok4096\hetero_122b_9b\analysis
python hetero_report.py --mixed ..\pharos_runs\tok4096\hetero_122b_9b\runs\Qwen3.5-9B_a0-Qwen3.5-122B-A10B --control ..\pharos_runs\tok4096\hetero_27b_9b\runs\Qwen3.5-9B --hub-home ..\pharos_runs\tok4096\hetero_122b_9b\runs\Qwen3.5-122B-A10B --leaves-home ..\pharos_runs\tok4096\grid\Qwen3.5-9B ..\pharos_runs\tok4096\probe_9b\Qwen3.5-9B --hand ..\pharos_runs\tok4096\hetero_122b_9b\analysis
```

**Timing.** The first mixed star ran at 1.7 s per call with two lanes, and
the second's smoke run at 3.0 s. A run has 256 calls, so a lane of 5 runs
should take 40-120 minutes; less once the second mixed star's two lanes have
ended. The smoke run takes 1-3 minutes.
