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

## Results, 2026-11-12

Read on 2026-11-12 after the 10 runs, by `hetero_report.py` as committed in
`74406fc` (the default `--lies hub`). Every reading is exploratory, as fixed
above. The scripts, the hand sheets with their keys and labels, and the
outputs are kept in `pharos_runs/tok4096/hetero_122b_9b/analysis/`.

**Runs and checks.**
- **When and on what.** The two lanes ran on 2026-11-12, beside the second
  mixed star's two lanes, on `8fa4fa3` (`74406fc` added the plans and changed
  only the report). The mixed star ran from 02:18 to 03:11, the control (the
  122B alone) from 02:21 to 02:58.
  - A run took 7.3-13.8 minutes in the mixed star, 5.3-9.4 in the control.
    The lanes averaged 2.49 and 1.70 s per call and took 53 and 36 minutes;
    the plan foresaw 40-120.
  - No run stopped. The server reported the planned model on every call of
    the mixed star.
- **The smoke run** (02:12-02:13) passed the five checks:
  - routing: the hub's 8 calls were answered by the 122B and the leaves' 24
    by the 9B, as the server reports;
  - no `<think>` block in its 32 calls;
  - 16 of 16 forecast calls parse;
  - the round-1 message prompt has 464 tokens for every agent;
  - `verify_prompts.py` finds nothing in its 40 prompts.

  It ran at 2.06 s per call. All four agents defected in both rounds. In
  round 1 the hub intended to defect before the talk (forecast 20) and
  promised; it gave 80 to the leaf that promised back, and defected.
- **`verify_prompts.py`** rebuilt 3,200 prompts of the mixed star and the
  control and finds nothing. `horizon_hits.py` finds no horizon wording in
  any agent's message. `audit_corpus.py` finds no issue and no duplicate
  history.
- **Calls cut at the cap: 1 of 2,560,** a 9B leaf's message in the mixed
  star, kept.
- **`<think>` blocks, all from the 122B:**
  - 4 of the mixed hub's 320 calls: three messages, one of them left empty;
    one forecast, read from the restarted answer;
  - 5 of the control's 1,280, each leaving a valid record;
  - the 122B's star of 11-11 had 5, its forecast cell of 11-04 had 9.
- **One decision is invalid,** a leaf's in the mixed star.
- **Configs.** The mixed star's equal the 9B's forecast runs of 11-09 of the
  same number, apart from the output folder and `agent_models`. The
  control's equal the 122B's of 11-04, apart from the output folder.
- The two campaign zips and each tree's inner zips are intact and
  byte-identical to the runs on disk.

### The hand checks

- **Promises.** The mixed star and the 9B's star of 11-12 (the leaves'
  reference, the second mixed star's control) hold 615 messages of
  defecting senders. The sheet held the 155 that the detector reads as
  promises and a random 100 of the 460 others (seed 7). They were read
  blind.
  - Only 5 of the 100 were strict promises by hand, so no second sheet was
    needed.
  - By hand: U 71, K 70, N 114. That makes 141 strict promises.
  - Of the detector's 155, 136 are strict promises by hand. The 19 N
    announce or justify a defection, most of them by the neighbour's broken
    promises ("Your promises are empty; ...").
  - By cell and role: the mixed hub 47 messages (42 strict), the mixed
    leaves 93 (45), the 9B star's hub 29 (22), its leaves 86 (32).
- **The shared reference.** 68 messages of the 9B's star were read in both
  mixed stars' sheets, and all 68 got the same label. This sheet's random
  sample also found two strict promises there that the detector misses and
  the second sheet's did not. So this write-up counts one more broken
  promise for that star's hub (22 against 21) and one more for its leaves
  (32 against 31).
- **Inverted forecasts.** 160 calls were read, blind to the set they came
  from: the 60 flagged calls, and a random 100 (50 before the messages, 50
  after them, seed 13).
  - 43 of the 60 flagged calls are inverted. All but one are the 9B's.
  - The one is the 122B hub's, in run 4, round 6. It gives 100 to a leaf
    that has just announced defection, while its reasoning says that leaf
    will defect.
  - 3 of the random 100 are inverted: the two the second sheet found, in
    the 9B's star before the messages, and a leaf's call after the messages
    in the mixed star.
  - 4 calls did not parse, all in the 9B's star.
  - 54 calls were read in both sheets, and all got the same label.
  - Rules 5 and 6 are read without the 46 inverted calls (B), and given with
    them (A).

### Rule 1: it passes

- **Routing:** 1,280 of the mixed star's 1,280 calls were answered by the
  planned model: the hub's 320 by Qwen/Qwen3.5-122B-A10B, the leaves' 960 by
  Qwen/Qwen3.5-9B.
- **Forecasts valid,** before and after the messages:
  - the mixed hub: 80 and 80 of 80; its leaves: 237 and 236 of 239;
  - the control's hub: 80 and 80 of 80; its leaves: 240 and 240 of 240;
  - the 9B's star: as in the second mixed star.
- **Inverted calls:** 3 of the random 100, at most 5 allowed.
- **`verify_prompts.py`:** nothing.
- **Tokens:** the round-1 message prompt has 464 tokens in every role and
  cell.

### Cooperation by role

Run means are in brackets.

| star | hub | leaves |
|---|---|---|
| mixed: the 122B hub, 9B leaves | **0.04** (0.00, 0.00, 0.19, 0.00, 0.00) | 0.04 (0.06, 0.04, 0.00, 0.00, 0.10) |
| control: the 122B alone, 11-12 | 0.68 (0.88, 1.00, 0.81, 0.19, 0.50) | 0.60 (0.85, 1.00, 0.77, 0.12, 0.23) |
| the 122B alone, 11-11 (the first mixed star's control) | 0.71 (0.44, 0.88, 0.88, 1.00, 0.38) | 0.61 |
| the 122B's earlier stars (grid 10-30, forecast cell 11-04) | 0.63 | 0.53 |
| the 9B alone, 11-12 (the leaves' reference) | 0.01 | 0.04 (0.02, 0.06, 0.00, 0.00, 0.10) |
| the 9B's earlier stars (grid 11-06, forecast cell 11-09) | 0.01 | 0.04 |

In four of the five mixed runs the hub never cooperated.

### The control: the 122B plays as on 11-11

- **Its hub cooperates 0.68, within 0.20 of 0.71,** as predicted. Its leaves
  cooperate 0.60, against 0.61. One run collapses (run 4: hub 0.19, leaves
  0.12); two did on 11-11.
- **Before the talk in round 1,** the 122B intends to defect in 24 of its 25
  calls: the 5 mixed hubs, the 5 control hubs, and 14 of the 15 control
  leaves. On 11-11 it was 25 of 25.
  - The mean forecasts in the control are 14.0 for the hub and 27.7 for the
    leaves; 24.0 and 21.7 on 11-11.
- **Its hub's actions follow its beliefs:** it cooperates 0.91 at a belief of
  50 or more (55 decisions) and 0.16 below (25). On 11-11: 0.88 and 0.33.
- **Its hub's lies,** by the detector (the hand check does not read this
  star): 19 broken promises, P 19/19, planned exploitation 3 (0.16),
  "rarely". On 11-11, by hand: 19, P 0.79, 5 (0.26), "partly".
- **The edges.** Its leaves defect on a cooperating hub in 38 edge-rounds,
  the hub on a cooperating leaf in 19; on 11-11, 46 and 21. The payoff per
  neighbour is 3.19 for the hub and 3.59 for the leaves: "even", by 0.10.
  On 11-11 it read "the leaves gain at the hub's expense" (3.20 and 3.72).

### Rule 2: the leaves lower the hub's cooperation

- **The 122B hub cooperates 0.04, against 0.68 in its same-day star: -63.8
  points.** That is "the leaves lower the hub's cooperation", as predicted.
- **By run,** the hub's means are 0.00, 0.00, 0.19, 0.00 and 0.00.
  - Across all 20 of the 122B's own stars, only one run's hub is as low as
    0.19 (the control's run 4), and none is below it.
  - An exact permutation test of the run means, outside the plan, gives a
    one-sided p of 2/252 against the same-day star, and 2/53130 against all
    20.
- **The hub in its four stars,** by the detector's promises:

| the 122B hub's leaves | hub cooperation | promises | broken | payoff per neighbour |
|---|---|---|---|---|
| three 27B (11-11) | 0.95 | 77/80 | 2 | 3.95 |
| three 122B (11-11) | 0.71 | 74/80 | 20 | 3.20 |
| three 122B (11-12) | 0.68 | 72/80 | 19 | 3.19 |
| three 9B (11-12) | 0.04 | 41/80 | 39 | 2.12 |

- **It believes the announcements.**
  - Its forecast of a leaf that has just announced defection is 2.0 (167
    forecasts).
  - Its belief by run is 13, 8, 10, 12 and 5, below 50 in 76 of its 80
    decisions. In its same-day star: 89, 96, 80, 25 and 54, below 50 in 25.
- **Round 1.** Before the talk it intends to defect in 5 of 5 runs (forecast
  20.0), as the 122B does in its own star. After the talk it still intends
  to in 5 of 5, and defects in 5 of 5. In its same-day star, all 5 hubs
  intend to cooperate after the talk, and 3 do.
- **It cooperated 3 times, all in run 3** (rounds 5, 8 and 11). Each time all
  three leaves defected. Twice it had promised ("I commit to Cooperate this
  round to break the deadlock and restore mutual gains; please
  reciprocate."); once it had announced defection.

### Rule 3: the leaves play as in their own star

- The leaves cooperate 0.04, against 0.04 in the 9B's star of 11-12: +0.4
  points. That is "the leaves play as in their own star", as predicted.
- Beside it: the 9B's earlier stars, leaves 0.04; its star of 11-12 against
  them, +0.0 points.

### Rule 4: even

**Payoff per neighbour: hub 2.12, leaves 2.11. That is "even",** as
predicted.

| star | hub-leaf edge-rounds | both cooperate | the hub defects on a cooperating leaf | a leaf defects on a cooperating hub | both defect | hub payoff | leaves payoff | reading |
|---|---|---|---|---|---|---|---|---|
| mixed | 239 | 0 | 10 | 9 | 220 | 2.12 | 2.11 | even |
| control: the 122B alone, 11-12 | 240 | 124 | 19 | 38 | 59 | 3.19 | 3.59 | even |
| the 9B alone, 11-12 | 239 | 0 | 9 | 3 | 227 | 2.13 | 2.01 | even |
| the 9B's earlier stars | 478 | 1 | 17 | 5 | 455 | 2.13 | 2.01 | even |

No edge-round of the mixed star has both agents cooperating.

### Rule 5: the hub's lies

| star | the hub's promises | broken | P | planned exploitation | planned defence | decided after, expecting C | decided after, expecting D | reading |
|---|---|---|---|---|---|---|---|---|
| mixed | 44/80 | 42 | 42/42 | 2 (0.05) | 40 | 0 | 0 | **rarely planned exploitation** |
| control: the 122B alone, 11-12 (detector) | 72/80 | 19 | 19/19 | 3 (0.16) | 16 | 0 | 0 | rarely |
| the 122B alone, 11-11 (hand) | 73/80 | 19 | 15/19 | 5 (0.26) | 10 | 2 | 2 | partly |

- **Readable, and "rarely planned exploitation", as predicted.** A and B are
  the same: the hub's inverted call is not in a broken promise.
  - The hub promised in 44 of its 80 decisions and broke 42 of those
    promises, each planned before the talk.
  - 40 are planned defence: it expected its leaves to defect.
- **The leaves believe fewer than half, as predicted.**
  - Their forecast of the hub after a broken promise is 30.6 (123
    forecasts). 29 of the 123 are 50 or more (0.24); AUC 0.65.
  - After the hub's 2 kept promises (6 forecasts) it is 39.2. Without the
    inverted calls: 0.23, AUC 0.66.
- **Round 1:** a leaf's forecast of the hub moves +30.7 after the hub's
  promise (14 pairs), from 12.9 to 43.6.
- **When:** 5 in round 1, 9 in rounds 2-5, 28 in rounds 6-16.
- **Lying did not pay the hub:** 2.11 per neighbour when it broke a promise,
  against 2.23 when it defected without one.
- The report's "control" row is the 9B's star, whose hub is a 9B. As the
  plan says, it is not part of the rule.

### Rule 6: belief and action

| star | role | at a belief of 50 or more (B) | below 50 (B) | reading (B) | reading (A) |
|---|---|---|---|---|---|
| mixed | hub | 1/3 | 2/76 | too few to read | too few to read (1/4 against 2/76) |
| mixed | leaves | 1/38 = 0.03 | 8/180 = 0.04 | its actions ignore its beliefs | ignore (2/56 against 8/180) |
| the 9B alone, 11-12 | hub | 1/7 | 0/60 | too few to read | ignore (1/20 against 0/60) |
| the 9B alone, 11-12 | leaves | 4/11 | 4/209 | too few to read | ignore (4/23 against 4/211) |

- As predicted: the leaves' actions ignore their beliefs. The hub's side at
  50 or more is too few to read (4 decisions; 3 without its inverted call).
- Beside it, the 122B alone the same day (all calls, outside the report):
  hub 0.91 against 0.16, leaves 0.92 (147) against 0.09 (93).

### Rule 7 (descriptive)

**Round 1, before and after the talk.**

| star | role | intends C before (forecast) | after | plays C |
|---|---|---|---|---|
| mixed | hub | 0/5 (20.0) | 0/5 | 0/5 |
| mixed | leaves | 0/15 (12.9) | 4/15 | 1/15 |
| the 122B alone, 11-12 | hub | 0/5 (14.0) | 5/5 | 3/5 |
| the 122B alone, 11-12 | leaves | 1/15 (27.7) | 13/15 | 12/15 |
| the 9B alone, 11-12 | hub | 0/5 (12.0) | 0/5 | 0/5 |
| the 9B alone, 11-12 | leaves | 0/15 (10.7) | 2/15 | 1/15 |

Four leaves of the mixed star intended to cooperate once they had read the
hub's promise, and all four defected. The one leaf that cooperated in round
1 had intended to defect.

**The first defection of each mixed run** came in round 1, from the hub and
at least two leaves.
- In every run the hub intended to defect before the talk, promised, and
  defected. In run 2 it wrote "I promise to Cooperate this round and hope
  you do the same for mutual benefit."
- In every run at least one leaf announced defection in round 1, and the
  hub's forecasts after the messages were 50 or below.

**Do the 9B leaves lie to a 122B hub? Yes, and about half of their lies
are now planned exploitation.** These are read by `hetero_report.py --lies
leaves`:

| star | the leaves' promises | broken | P | planned exploitation | planned defence | decided after, expecting C | decided after, expecting D |
|---|---|---|---|---|---|---|---|
| mixed, B | 51/239 | 41 | 38/38 | 18 (0.47) | 20 | 0 | 0 |
| mixed, A | 51/239 | 45 | 42/42 | 22 (0.52) | 20 | 0 | 0 |
| the 9B alone, 11-12, B | 36/239 | 27 | 26/27 | 1 (0.04) | 25 | 0 | 1 |
| the 9B alone, 11-12, A | 36/239 | 32 | 31/32 | 6 (0.19) | 25 | 0 | 1 |
| the 9B's forecast cell, 11-09 (detector) | 39 | 33 | 30/33 | 5 (0.15) | 25 | 1 | 2 |

- **With a 122B hub, about half of a 9B leaf's broken promises are made
  while it expects the hub to cooperate:** 18 of 38, against 1 of 27 in its
  own star the same day. By the second plan's rule 5 that is "partly" (A:
  22 of 42, "mostly"); its own star and the second mixed star read
  "rarely".
- **Its actions did not change** (rule 6). The hub's promises raise the
  leaves' forecasts (+30.7 in round 1), and the leaves defect at any
  forecast. What changes is what they expect when they defect.
- **The hub cannot tell these lies from kept promises.** Its forecast of a
  leaf after a broken promise is 41.2 (45), and after a kept one 28.3 (6):
  AUC 0.40. It gave 50 or more after 17 of the 45 (0.38). Without the
  inverted calls: 15 of 43, AUC 0.42.
- **In their round,** a leaf's broken promise earned 2.44 per neighbour,
  against 2.09 for a defection without one. The hub cooperated in 0.11 of
  those rounds, against 0.02.

**Does lying pay?** For each decision of the mixed star: the sender's payoff
per neighbour in the round, and the share of its neighbours that cooperate,
that round and the next. The 9B star's rows are in the second mixed star's
write-up; here its hub has 22 broken promises and its leaves 32.

| role | the sender | decisions | payoff per neighbour | neighbours cooperating, that round | next round |
|---|---|---|---|---|---|
| hub | broke a promise | 42 | 2.11 | 0.03 | 0.05 |
| hub | kept a promise | 2 | 1.00 | 0.00 | 0.00 |
| hub | defected without a promise | 35 | 2.23 | 0.06 | 0.03 |
| hub | cooperated without a promise | 1 | 1.00 | 0.00 | 0.00 |
| leaves | broke a promise | 45 | 2.44 | 0.11 | 0.07 |
| leaves | kept a promise | 6 | 1.00 | 0.00 | 0.00 |
| leaves | defected without a promise | 184 | 2.09 | 0.02 | 0.04 |
| leaves | cooperated without a promise | 4 | 1.00 | 0.00 | 0.00 |

Every kept promise, the hub's 2 and the leaves' 6, was met by defection on
every edge.

### The prediction, read

| | predicted | found | |
|---|---|---|---|
| rule 1 | passes | passes | held |
| the control | hub within 0.20 of 0.71 | 0.68 | held |
| rule 2 | the leaves lower the hub's cooperation | -63.8 | held |
| rule 3 | the leaves play as in their own star | +0.4 | held |
| rule 4 | even | 2.12 against 2.11 | held |
| rule 5 | readable; rarely planned exploitation | 42 lies; 2 of 42 (0.05) | held |
| rule 5, belief | the leaves believe fewer than half | 0.24 | held |
| rule 6 | the leaves ignore their beliefs; the hub follows, or too few | ignore; too few | held |

### In words

- **A neighbourhood that defects and says so turns the 122B into a
  defector.**
  - It cooperated 0.04, against 0.68 in its own star the same day and 0.95
    with 27B leaves. In four of five runs it never cooperated.
  - The same hub, in three neighbourhoods: 0.95 with leaves that keep their
    word, 0.68-0.71 with its own kind, 0.04 with leaves that defect and say
    so.
- **It keeps promising, and its lies are defence.** It promised in 44 of 80
  decisions and broke 42 of those promises. Each was planned before the
  talk, and almost all came while it expected its leaves to defect. Its
  leaves believed a quarter of them, and lying did not pay it. The 27B hub,
  beside the same kind of leaves, mostly stopped promising (19 of 80).
- **The 9B leaves do not move,** with a 122B hub as with a 9B one: they
  cooperate 0.04 in both, and their actions ignore their beliefs.
- **But their lies change kind.** Beside a hub that promises, about half of
  their broken promises come while they expect the hub to cooperate (18 of
  38). In their own star it is 1 of 27. They defect either way; the hub's
  promises change what they expect.
- **Nobody gains:** no edge-round has both cooperating, and the payoffs are
  even.
- **Limits.**
  - One composition, five runs.
  - The two models are one generation but differ in size and architecture.
  - The leaves' reference is shared with the second mixed star. Each read it
    with its own labels, and the two agree on every message and call read
    in both.
