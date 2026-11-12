# A second mixed star: Qwen3.8-27B in the hub, Qwen3.5-9B in the leaves

This is the plan for the second exploratory experiment with two models in one
network, on the lab server. It was written before any run of it, and its rules
and prediction are fixed here. Its smoke run ran at 01:53 on 2026-11-12. A
first start of its two lanes (02:01) stopped before any run had ended, when the
terminal running them was closed; the lanes then ran again from the beginning,
02:17-03:17. The plan was committed after they had ended, before any of their
runs was read. Its text is as written at 01:42, before all of them, with these
sentences added. It follows `docs/hetero_star_plan.md` (the 122B in the hub,
the 27B in the leaves; results of 2026-11-11), with another pair of models.

## Question

In the first mixed star, three leaves that kept their word kept the 122B hub
cooperating: 0.95, against 0.71 in its own star the same day. This plan asks
the converse. What does a neighbourhood that defects do to a hub that keeps
its word?
- **Qwen/Qwen3.8-27B-FP8, the hub:**
  - it cooperates in every seat of its own star (1.00), and keeps its word: no
    broken promise in its 160 hub decisions;
  - it intends to cooperate before any talk (5 of 5 hubs, forecast 60), and
    believes promises (+29.3 in round 1);
  - it does what it expects: it cooperates 0.99 at a belief of 50 or more and
    0.08 below (its forecast cells). An announced defection drops its
    forecast to 11.7 (its competitive cell);
  - as the leaves of the first mixed star, it retaliated at once: after the
    122B hub's lies its leaves cooperated 0.11 in the next round.
- **Qwen/Qwen3.5-9B, the leaves:**
  - it defects in its own star: leaves 0.02 (grid) and 0.05 (forecast cell);
  - before any talk it intends to defect, in every call;
  - when it defects it mostly says so: 80% of its leaves' messages announce
    defection (forecast cell). It breaks 33 of its 39 promises;
  - its actions do not follow its beliefs: it cooperates 0.19 at a belief of
    50 or more and 0.03 below.

What happens when the 27B sits in the hub and three 9B agents are its leaves?
- **The hub.** Does a neighbourhood that defects, and says so, drag the 27B
  into defection? Or does it keep cooperating, and get exploited?
- **The leaves.** Does a hub that cooperates and promises raise the 9B's
  cooperation, or do its actions stay deaf to what it expects?
- **The lies.** When a 9B leaf promises and defects, does the 27B believe it?

The agents are never told which model a neighbour is: the prompts are those
of a homogeneous star. Any difference is made by play and talk alone.

## Design

- **The mixed star:** four agents. Agent 0, the hub with three edges, is
  served Qwen/Qwen3.8-27B-FP8; agents 1-3, the leaves, Qwen/Qwen3.5-9B.
- **The cell:** `forecast_probe` (session `PROBE`), as in the first mixed
  star.
  - It is the baseline with cheap talk: Prisoner's Dilemma, 16 rounds with a
    hidden horizon, memory 10, temperature 0.7, cap 4096, thinking off.
  - Each agent also gives two private forecasts per round, before and after
    the messages. The game's prompts are the baseline's, byte for byte.
- **5 runs.**
- **A same-day control: the 9B alone on the star,** the same cell, 5 runs, in
  a second lane beside the first.
  - The 9B's earlier stars ran on 11-06 (grid) and 11-09 (forecast cell),
    before the server's model update of 11-09. The update cut its last
    forecast run. The 27B's stars ran after it (11-10).
  - So the control is the model whose references predate the update, as in
    the first mixed star. There it was the hub's model (the 122B); here it is
    the leaves'.
  - The control separates the hub's effect on the leaves from any change in
    the served 9B.
- **A smoke run first:** one run of 2 rounds of the mixed star, into
  `pharos_runs/smoke_hetero_27b_9b/runs`. It is also the 9B's first run since
  the update. It must pass the first plan's five checks before the runs:
  - every call of agent 0 is answered by the 27B, and every call of a leaf by
    the 9B, as the server reports;
  - no `<think>` block, from either model;
  - every forecast call parses;
  - the round-1 message prompt has 464 tokens for every agent, as on both
    models' stars;
  - `verify_prompts.py` finds nothing.
- **Placement.** `pharos_runs/tok4096/hetero_27b_9b/runs/` holds two trees:
  - `Qwen3.5-9B_a0-Qwen3.8-27B-FP8`, the mixed star;
  - `Qwen3.5-9B`, the control.

  The two campaign zips land in `tok4096/hetero_27b_9b/`. The control's,
  `Qwen3.5-9B_star_sessionPROBE_pd.zip`, has the same name as the 9B's
  forecast zip of 11-09 in `tok4096/`.
- **The code** (this commit) generalises `hetero_report.py`:
  - the control may be either model alone. When it is the leaves' model, rule
    2 reads the mixed hub against the hub's model at home, and rule 3 the
    mixed leaves against the control, either way;
  - `--lies leaves` reads rule 5 for the leaves' broken promises, with the
    hub's forecast of each leaf after that leaf's promise;
  - on the first mixed star it prints the same lines as before, with and
    without the hand labels, and `--dump` writes the same sheets.

## References

The two models' own stars, by role (hub = agent 0, leaves = agents 1-3).
Promises and broken promises are the detector's; announced defections follow
the 9B plan's pattern. The payoff is per neighbour and per round.

| model, cell | runs | hub cooperation | leaves cooperation | hub payoff | leaves payoff | hub broken | leaves broken | leaves' messages announcing defection |
|---|---|---|---|---|---|---|---|---|
| 27B, grid baseline (11-10) | 5 | 1.00 | 1.00 | 3.99 | 4.01 | 0/80 | 1/238 | 1/240 |
| 27B, grid no_comm (11-10) | 5 | 0.37 | 0.38 | 2.90 | 2.76 | | | |
| 27B, forecast cell (11-10) | 5 | 1.00 | 1.00 | 4.00 | 4.00 | 0/80 | 0/237 | 0/240 |
| 9B, grid baseline (11-06) | 5 | 0.00 | 0.02 | 2.08 | 1.98 | 16/16 | 42/45 | 185/239 |
| 9B, grid no_comm (11-06) | 5 | 0.07 | 0.13 | 2.37 | 2.10 | | | |
| 9B, forecast cell (11-09) | 5 | 0.03 | 0.05 | 2.18 | 2.04 | 16/17 | 33/39 | 192/239 |

- **Runs.** In the 27B's star every run's hub is at 1.00. In the 9B's star no
  run's hub is above 0.06, and no run's leaves above 0.10.
- **Round 1, before the talk** (forecast cells):
  - the 27B's hub intends to cooperate in 5 of 5 calls (forecast 60.0);
  - the 9B's leaves in 0 of 15 (24.0), and its hub in 0 of 5 (6.0).
- **The 9B leaves' round-1 messages** announce defection in 13 of 15
  (forecast cell) and 9 of 15 (grid). They promise in 2 and 6.
- **Belief and action** (forecast cells), cooperation at a belief of 50 or
  more against below 50:
  - the 27B: 1.00, and never below 50 (its two forecast cells: 0.99 against
    0.08);
  - the 9B's leaves: 0.19 (37 decisions) against 0.03 (199); its hub: 0.00
    (14) against 0.03 (61).
- **Forecasts of a neighbour** (forecast cells):
  - the 27B after a promise: 95.9, a round-1 shift of +29.3. After an
    announced defection: none in its star; 11.7 in its competitive cell;
  - the 9B's leaves after a promise: 31.0. After an announced defection:
    14.0, raw (the 9B often writes the probability of defection for a
    neighbour that announced it).
- **The kind of lie** of the 9B's leaves (forecast cell): of 33 broken
  promises, 5 are planned exploitation (0.15), 25 planned defence, 1 decided
  after expecting cooperation and 2 expecting defection.
- **The edges.** In the 9B's forecast cell, of 239 hub-leaf edge-rounds, the
  hub defects on a cooperating leaf in 12 and a leaf on a cooperating hub in
  5; 221 are both defect. In the 27B's, 240 of 240 are both cooperate.
- **Round-1 message prompt tokens:** 464 for every agent, on both stars.

## Definitions

Those of `docs/hetero_star_plan.md`, which are the competitive plan's, by
role. One is new:
- **The hub's forecast of a leaf:** the hub's forecast call gives one number
  per leaf. Rule 5 reads the number for a leaf after that leaf's message.

## Hand checks

Those of `docs/hetero_star_plan.md`: blind, with the same seeds, over the
mixed star's and the control's runs together.
- **Promises:**
  - every message of a defecting sender that the detector reads as a
    promise, and a random 100 of those it does not (seed 7);
  - if more than 10 of the 100 are promises by hand, every such message is
    read (`--dump-rest`);
  - classes U, K, DU, M and N, with the strict reading U + K;
  - the rules take the hand's reading where a message was read, and the
    detector's elsewhere.
- **Inverted forecasts:**
  - every forecast call after the messages that gives at least 50 to a
    neighbour whose message announced defection (a random 100 if more, seed
    13);
  - a random 100 of the other forecast calls, 50 before the messages and 50
    after them (seed 13).

  The 9B often inverts the first kind: in its forecast cell, 83 of the 100
  flagged calls read were inverted, and 3 of the random 100. The calls found
  inverted leave rules 5 and 6. Those rules are given both with them and
  without them.

## Reading rules

Every reading is exploratory: one composition, one cell, five runs.

1. **Routing, compliance and the untouched game, read first, for both
   cells.** If rule 1 fails, nothing else is read.
   - **Routing:** in the mixed star, every one of the hub's calls is
     answered by Qwen/Qwen3.8-27B-FP8, and every one of the leaves' by
     Qwen/Qwen3.5-9B, as the server reports.
   - **Forecasts:** at least 90% of forecast calls are valid, before and
     after, for each role in each cell.
   - **Inversion:** at most 5 calls of the random 100 are inverted.
   - **`verify_prompts.py`** finds nothing, or every hit is in an agent's own
     words.
   - **Tokens:** the round-1 message prompt tokens equal the references, role
     by role: 464.
2. **Does the neighbourhood change the hub?** The hub's cooperation in the
   mixed star minus the 27B's hub in its own star (its grid and its forecast
   cell, 160 decisions, both after the update).
   - +0.20 or more: "the leaves raise the hub's cooperation".
   - -0.20 or less: "the leaves lower the hub's cooperation".
   - Within 0.10: "the hub plays as in its own star".
   - In between: "partly".
   - Reported beside it: run means; the control's hub.
3. **Does the hub change the leaves?** The leaves' cooperation in the mixed
   star minus the control's leaves, 240 decisions each.
   - +0.20 or more: "the hub raises the leaves' cooperation".
   - -0.20 or less: "the hub lowers the leaves' cooperation".
   - Within 0.10: "the leaves play as in their own star".
   - In between: "partly".
   - Reported beside it: the 9B's earlier stars, and the control against
     them.
4. **Who gains at whose expense?** The hub's payoff per neighbour minus the
   leaves'.
   - +0.5 or more: "the hub gains at the leaves' expense".
   - -0.5 or less: "the leaves gain at the hub's expense".
   - In between: "even".
   - Reported beside it: the four kinds of hub-leaf edge-round, in each cell
     and in both references.
5. **The leaves' lies.** The leaves' broken promises that have a valid
   intention before the talk and a belief. Read only with at least 10;
   otherwise "too few to read".
   - The share of planned exploitation:
     - 0.50 or more: "mostly planned exploitation";
     - below 0.25: "rarely";
     - in between: "partly".
   - Reported beside it:
     - P and the four kinds, in the mixed star, the control and the 9B's
       earlier forecast cell;
     - the hub's forecast of a leaf after that leaf's kept and broken
       promises, the share of broken promises the hub believes (50 or more),
       and the AUC;
     - the round-1 shift of the hub's forecast of a leaf after that leaf's
       promise.
6. **Belief and action, by role.** Cooperation at a belief of 50 or more,
   against below 50, for each role in each cell, each side with at least 20
   decisions; otherwise "too few to read".
   - A difference of 0.50 or more: "its actions follow its beliefs".
   - Below 0.20: "its actions ignore its beliefs".
   - In between: "partly".
7. **Descriptive, not rules:**
   - round 1 before and after the talk, by role;
   - the first defection of each mixed run: who, when, planned or not;
   - **does lying pay?** By role, the sender's payoff per neighbour when it
     broke a promise, kept one, or defected without one, and its neighbours'
     cooperation in that round and the next;
   - the hub's own broken promises: does the 27B hub start to lie?

**How the numbers are computed.**
- `hetero_report.py` with `--lies leaves` prints rules 1-6 and the
  descriptive splits, and reads the hand labels with `--hand`.
- `verify_prompts.py` and `audit_corpus.py` run on both trees.
- The scripts, sheets, keys, labels and outputs are kept beside the runs, in
  `pharos_runs/tok4096/hetero_27b_9b/analysis/`.

## Prediction, stated before the run

- **Rule 1** passes for both cells. The risk is the 9B's inversion: in its
  own cell 3 of the random 100 were inverted, against at most 5 allowed.
- **The control** plays as the 9B's earlier stars: its leaves cooperate below
  0.20, and every round-1 call before the talk intends to defect.
- **Rule 2: "the leaves lower the hub's cooperation"** (-0.20 or less).
  - The 9B's leaves announce defection in most messages, from round 1.
  - The 27B believes an announced defection, and does what it expects.
- **Rule 3: "the leaves play as in their own star".** The 9B's actions do not
  follow its beliefs, so a hub that promises cannot raise its cooperation.
- **Rule 4: "even".** The hub stops cooperating within a round or two, and
  the edges settle on mutual defection.
- **Rule 5:** readable, and "rarely planned exploitation", as in the 9B's own
  cell (0.15): once the hub defects, the leaves' lies cover defections they
  expect to be returned. In round 1 the hub believes a leaf's promise, with a
  shift of +20 or more.
- **Rule 6:** the leaves' actions ignore their beliefs. The hub's actions
  follow its beliefs, or its side at 50 or more is too few to read.

## Seen before writing

- Every number of the two models' stars above, and of their other cells.
- The results of the first mixed star (`docs/hetero_star_plan.md`).
- The test of the code:
  - the first mixed star's report and sheets are unchanged;
  - a fixture, the 9B's forecast runs on the star relabelled as a mixed star
    with the 27B in the hub, read by `hetero_report.py --lies leaves` against
    the 9B's own runs as the control. Its rule 5 lines agree with a count made
    apart.

No run of this experiment existed when this was written.

## Limits fixed in advance

- **Scope.** One composition, one cell, five runs. The hub is one agent per
  run: 80 decisions.
- **Two changes at once.** The two models differ in generation, size and
  precision. "Strong" and "weak" would be shorthand.
- **Stated beliefs.** The forecasts come from separate calls, and nothing
  rewards their accuracy.
- **The detector** is not validated on these models; the hand check covers the
  messages of defecting senders, in part by sample.
- **The 9B's inversions.** The check reads the reasoning of the flagged calls.
  The readings that use forecasts are given with and without the calls found
  inverted.
- **The served model is what the server reports.** The smoke run checks it
  before any run.
- **Server updates:**
  - if one stops the runs, a new smoke run comes before any further run;
  - a lane cut short keeps its runs if it has at least 4 of 5; otherwise it
    is run again whole;
  - the write-up names every run made after an update.
- **Other compositions** (a 9B hub with 27B leaves, or the 122B with the 9B)
  are not part of this plan.

## Reproduce

From `cheaptalk_bench`. First the smoke run, then the two lanes side by
side:

```
python campaign.py --provider pharos --model Qwen/Qwen3.5-9B --agent-model 0=Qwen/Qwen3.8-27B-FP8 --session PROBE --topology star --games pd --n-runs 1 --n-rounds 2 --max-new-tokens 4096 --out-root ..\pharos_runs\smoke_hetero_27b_9b\runs --zip-mirror=
python campaign.py --provider pharos --model Qwen/Qwen3.5-9B --agent-model 0=Qwen/Qwen3.8-27B-FP8 --session PROBE --topology star --games pd --n-runs 5 --n-rounds 16 --max-new-tokens 4096 --out-root ..\pharos_runs\tok4096\hetero_27b_9b\runs --zip-mirror=
python campaign.py --provider pharos --model Qwen/Qwen3.5-9B --session PROBE --topology star --games pd --n-runs 5 --n-rounds 16 --max-new-tokens 4096 --out-root ..\pharos_runs\tok4096\hetero_27b_9b\runs --zip-mirror=
```

Then the checks, the sheets and the report:

```
python verify_prompts.py ..\pharos_runs\tok4096\hetero_27b_9b\runs\Qwen3.5-9B_a0-Qwen3.8-27B-FP8 ..\pharos_runs\tok4096\hetero_27b_9b\runs\Qwen3.5-9B
python audit_corpus.py ..\pharos_runs\tok4096\hetero_27b_9b\runs\Qwen3.5-9B_a0-Qwen3.8-27B-FP8 ..\pharos_runs\tok4096\hetero_27b_9b\runs\Qwen3.5-9B
python hetero_report.py --mixed ..\pharos_runs\tok4096\hetero_27b_9b\runs\Qwen3.5-9B_a0-Qwen3.8-27B-FP8 --control ..\pharos_runs\tok4096\hetero_27b_9b\runs\Qwen3.5-9B --dump ..\pharos_runs\tok4096\hetero_27b_9b\analysis
python hetero_report.py --mixed ..\pharos_runs\tok4096\hetero_27b_9b\runs\Qwen3.5-9B_a0-Qwen3.8-27B-FP8 --control ..\pharos_runs\tok4096\hetero_27b_9b\runs\Qwen3.5-9B --hub-home ..\pharos_runs\tok4096\grid\Qwen3.8-27B-FP8 ..\pharos_runs\tok4096\probe_27b\Qwen3.8-27B-FP8 --leaves-home ..\pharos_runs\tok4096\grid\Qwen3.5-9B ..\pharos_runs\tok4096\probe_9b\Qwen3.5-9B --hand ..\pharos_runs\tok4096\hetero_27b_9b\analysis --lies leaves
```

**Timing.** The 9B's forecast cells ran at 1.5-8.2 s per call with three
lanes (11-09; the first two runs of each lane were the slow ones), the 27B's
at 1.5-2.5 s (11-10), and the first mixed star at 1.7 s with two lanes. A run
has 256 calls, or 7-35 minutes, so a lane of 5 runs should take 40-120
minutes. The smoke run takes 1-3 minutes.

## Results, 2026-11-12

Read on 2026-11-12 after the 10 runs, by `hetero_report.py` as committed in
`74406fc`, with `--lies leaves`. Every reading is exploratory, as fixed above.
The scripts, the hand sheets with their keys and labels, and the outputs are
kept in `pharos_runs/tok4096/hetero_27b_9b/analysis/`.

**Runs and checks.**
- **When and on what.** The two lanes ran side by side on 2026-11-12, on
  `8fa4fa3` (`74406fc` added the plans and changed only the report): the
  mixed star from 02:17 to 03:17, the control from 02:17 to 03:11. The third
  mixed star's two lanes ran beside them.
  - A run took 4.4-16.9 minutes. The lanes averaged 2.78 and 2.53 s per call
    and took 59 and 54 minutes; the plan foresaw 40-120.
  - A first start of the two lanes (02:01) stopped before any run ended, when
    the terminal running them was closed. No run stopped after that. The
    server reported the planned model on every call of the mixed star.
- **The smoke run** (01:53-01:55) passed the five checks:
  - routing: the hub's 8 calls were answered by the 27B and the leaves' 24 by
    the 9B, as the server reports;
  - no `<think>` block in its 32 calls;
  - 16 of 16 forecast calls parse;
  - the round-1 message prompt has 464 tokens for every agent;
  - `verify_prompts.py` finds nothing in its 40 prompts.

  It ran at 3.0 s per call. In round 1 the hub intended to cooperate before
  the talk (forecast 60) and promised. Two leaves announced defection, and
  it defected; the leaf that had promised cooperated. All four defected in
  round 2.
- **`verify_prompts.py`** rebuilt 3,200 prompts and finds nothing.
  `horizon_hits.py` finds no horizon wording in any agent's message.
  `audit_corpus.py` finds no issue and no duplicate history.
- **Calls cut at the cap: 5 of 2,560,** all from the 9B. Each left an invalid
  forecast or an empty message. One decision is invalid, in the control.
- One message of the 27B hub did not parse and was left empty (run 2, round
  14).
- **One `<think>` block,** in a 9B leaf's action call; its action was read.
- **Configs.** Every config equals the 9B's forecast run of 11-09 of the same
  number, apart from the output folder. The mixed star's also differs in
  `agent_models`.
- The two campaign zips and each tree's inner zips are intact and
  byte-identical to the runs on disk.

### The hand checks

- **Promises.** The 10 runs hold 621 messages of defecting senders. The sheet
  held the 112 that the detector reads as promises and a random 100 of the 509
  others (seed 7). They were read blind.
  - Only 3 of the 100 were strict promises by hand, so no second sheet was
    needed.
  - By hand: U 50, K 51, DU 3, N 108. That makes 101 strict promises (U + K).
  - Of the detector's 112, 98 are strict promises by hand and 14 are N.
- **Inverted forecasts.** 157 calls were read, blind to the set they came
  from: the 57 flagged calls, and a random 100 (50 before the messages, 50
  after them, seed 13).
  - 45 of the 57 flagged calls are inverted, all of them the 9B's. It gives
    95-100 to a neighbour that has just announced defection while its
    reasoning says that neighbour will defect, as in its own forecast cell
    (83 of 100).
  - 2 of the random 100 are inverted, both before the messages, in the
    control. 2 calls did not parse, both in the control.
  - Rules 5 and 6 are read without the 47 inverted calls (B), and given with
    them (A).

### Rule 1: it passes, for both cells

- **Routing:** 1,280 of the mixed star's 1,280 calls were answered by the
  planned model: the hub's 320 by Qwen/Qwen3.8-27B-FP8, the leaves' 960 by
  Qwen/Qwen3.5-9B.
- **Forecasts valid,** before and after the messages:
  - the mixed hub: 80 and 80 of 80; its leaves: 239 and 235 of 240;
  - the control's hub: 78 and 80 of 80; its leaves: 238 and 234 of 239;
  - at least 0.97 everywhere.
- **Inverted calls:** 2 of the random 100, at most 5 allowed.
- **`verify_prompts.py`:** nothing.
- **Tokens:** the round-1 message prompt has 464 tokens in every role and
  cell.

### Cooperation by role

Run means are in brackets.

| star | hub | leaves |
|---|---|---|
| mixed: the 27B hub, 9B leaves | **0.05** (0.12, 0.00, 0.12, 0.00, 0.00) | 0.02 (0.00, 0.00, 0.06, 0.02, 0.00) |
| control: the 9B alone | 0.01 (0.00, 0.06, 0.00, 0.00, 0.00) | 0.04 (0.02, 0.06, 0.00, 0.00, 0.10) |
| the 27B's star (grid and forecast cell, 11-10) | 1.00 | 1.00 |
| the 9B's earlier stars (grid 11-06, forecast cell 11-09) | 0.01 | 0.04 |

### The control: the 9B plays as before the update

Its leaves cooperate 0.04, below 0.20, and every round-1 call before the talk
intends to defect (20 of 20), as predicted. Its earlier stars gave its leaves
0.04.

### Rule 2: the leaves lower the hub's cooperation

- **The 27B hub cooperates 0.05, against 1.00 in its own star: -95.0
  points.** That is "the leaves lower the hub's cooperation", as predicted.
- **By run,** the hub's means are 0.12, 0.00, 0.12, 0.00 and 0.00. In its own
  star all ten are 1.00. An exact permutation test of the run means, outside
  the plan, gives a one-sided p of 1/3003.
- **It believes the announcements.**
  - Its forecast of a leaf that has just announced defection is 3.9 (195
    forecasts). In round 1 such a message drops it by 51.2 points, to 11.2.
  - Its belief by run is 17, 3, 18, 7 and 4, below 50 in 75 of its 80
    decisions. In its own forecast cell it is 96 in every run, never below
    50.
- **Round 1.** Before the talk the hub intends to cooperate in 5 of 5 runs
  (forecast 60.0), as in its own star. After reading its leaves it intends to
  in 1 of 5, and plays Cooperate in 1 of 5.

### Rule 3: the leaves play as in their own star

The leaves cooperate 0.02, against 0.04 in the control: -2.1 points. That is
"the leaves play as in their own star", as predicted.

### Rule 4: even

**Payoff per neighbour: hub 2.01, leaves 2.18. That is "even",** as
predicted.

| star | hub-leaf edge-rounds | both cooperate | the hub defects on a cooperating leaf | a leaf defects on a cooperating hub | both defect | hub payoff | leaves payoff | reading |
|---|---|---|---|---|---|---|---|---|
| mixed | 240 | 1 | 3 | 11 | 225 | 2.01 | 2.18 | even |
| control | 239 | 0 | 9 | 3 | 227 | 2.13 | 2.01 | even |
| the 27B's star | 480 | 479 | 0 | 1 | 0 | 3.99 | 4.00 | even |
| the 9B's earlier stars | 478 | 1 | 17 | 5 | 455 | 2.13 | 2.01 | even |

The leaves defected on a cooperating hub in 11 edge-rounds, the hub on a
cooperating leaf in 3. Both defected in 225 of the 240.

### Rule 5: the leaves' lies

| variant | the leaves' promises | broken | read (an intention and a belief) | P | planned exploitation | planned defence | decided after, expecting C | decided after, expecting D | reading |
|---|---|---|---|---|---|---|---|---|---|
| **B, without the inverted calls** | 35/240 | 28 | 27 | 27/27 | 5 (0.19) | 22 | 0 | 0 | **rarely planned exploitation** |
| A, all calls | 35/240 | 32 | 31 | 30/31 | 8 (0.26) | 22 | 1 | 0 | partly |

- **B, the reading the plan fixes, gives "rarely planned exploitation", as
  predicted.** A gives "partly", by 0.01. A counts four more lies, three of
  them planned exploitation, and their forecasts are inverted.
- **Beside it:** the control's leaves, 1 of 27 (B) and 5 of 31 (A); the 9B's
  earlier forecast cell, 5 of 33.
- **The hub's forecast of a leaf after that leaf's promise:**
  - 66.7 after a kept promise (3 forecasts), 41.6 after a broken one (32);
  - 12 of the 32 are 50 or more (0.38); AUC 0.70.
- **Round 1:** the hub's forecast of a leaf moves +31.7 after that leaf's
  promise, from 50.0 to 81.7. That is +20 or more, as predicted, but in 3
  pairs only.

### Rule 6: belief and action

| star | role | at a belief of 50 or more (B) | below 50 (B) | reading (B) | reading (A) |
|---|---|---|---|---|---|
| mixed | hub | 3/5 | 1/75 | too few to read | too few to read |
| mixed | leaves | 1/23 = 0.04 | 2/192 = 0.01 | its actions ignore its beliefs | ignore (1/43 against 2/192) |
| control | hub | 1/7 | 0/60 | too few to read | ignore (1/20 against 0/60) |
| control | leaves | 4/11 | 4/209 | too few to read | ignore (4/23 against 4/211) |

As predicted: the leaves' actions ignore their beliefs, and the hub's side at
50 or more is too few to read (5 decisions).

### Rule 7 (descriptive)

**Round 1, before and after the talk.**

| star | role | intends C before (forecast) | after | plays C |
|---|---|---|---|---|
| mixed | hub | 5/5 (60.0) | 1/5 | 1/5 |
| mixed | leaves | 0/15 (28.0) | 1/15 | 1/15 |
| control | hub | 0/5 (12.0) | 0/5 | 0/5 |
| control | leaves | 0/15 (10.7) | 2/15 | 1/15 |

**The first defection of each mixed run** came in round 1.
- Run 1: the three leaves, each planned before the talk; one of them had
  promised. The hub cooperated.
- Runs 2-5: the hub, with its leaves (two of them in run 3). Each time the
  hub had intended to cooperate before the talk and promised, and defected
  once it had read its leaves. In run 2 it wrote "Let's all cooperate for
  maximum mutual benefit. I'll cooperate if you do."
- The one leaf that intended to cooperate after the talk in round 1 defected.
  The one that cooperated had left no valid forecast after the talk.

**Does the 27B hub start to lie? Yes.**
- In its own star it promised in all 160 of its decisions and broke none.
- Here it promised in 19 of 80 and broke 17: 4 in round 1, decided after the
  messages and expecting defection; then 12 planned defence and 1 planned
  exploitation.
- Its leaves gave it 50 or more after 13 of these 47 broken-promise
  forecasts (0.28).

**Does lying pay?** For each decision: the sender's payoff per neighbour in
the round, and the share of its neighbours that cooperate, that round and the
next.

| star | role | the sender | decisions | payoff per neighbour | neighbours cooperating, that round | next round |
|---|---|---|---|---|---|---|
| mixed | hub | broke a promise | 17 | 2.24 | 0.06 | 0.02 |
| mixed | hub | kept a promise | 2 | 1.50 | 0.17 | 0.00 |
| mixed | hub | defected without a promise | 59 | 2.00 | 0.00 | 0.01 |
| mixed | hub | cooperated without a promise | 2 | 1.00 | 0.00 | 0.17 |
| mixed | leaves | broke a promise | 32 | 2.62 | 0.16 | 0.07 |
| mixed | leaves | kept a promise | 3 | 2.00 | 0.33 | 0.33 |
| mixed | leaves | defected without a promise | 204 | 2.12 | 0.03 | 0.03 |
| mixed | leaves | cooperated without a promise | 1 | 1.00 | 0.00 | 0.00 |
| control | hub | broke a promise | 21 | 2.29 | 0.08 | 0.06 |
| control | hub | defected without a promise | 58 | 2.09 | 0.02 | 0.03 |
| control | hub | cooperated without a promise | 1 | 1.00 | 0.00 | 0.00 |
| control | leaves | broke a promise | 31 | 2.26 | 0.06 | 0.00 |
| control | leaves | kept a promise | 4 | 1.00 | 0.00 | 0.00 |
| control | leaves | defected without a promise | 199 | 2.02 | 0.01 | 0.02 |
| control | leaves | cooperated without a promise | 5 | 1.00 | 0.00 | 0.00 |

In every role and cell a broken promise earns a little more in its round
than a defection without one (2.24-2.62 against 2.00-2.12). In the next
round the neighbours' cooperation stays at 0.07 or below.

### The prediction, read

| | predicted | found | |
|---|---|---|---|
| rule 1 | passes for both cells | passes | held |
| the control | leaves below 0.20; every round-1 call before the talk defects | 0.04; 20 of 20 | held |
| rule 2 | the leaves lower the hub's cooperation | -95.0 | held |
| rule 3 | the leaves play as in their own star | -2.1 | held |
| rule 4 | even | 2.01 against 2.18 | held |
| rule 5 | readable; rarely planned exploitation | 27 lies; 0.19 (B); A gives 0.26, partly | held (B) |
| rule 5, round 1 | the hub's shift +20 or more | +31.7, in 3 pairs | held |
| rule 6 | the leaves ignore their beliefs; the hub follows, or too few | ignore; too few | held |

### In words

- **A neighbourhood that defects and says so drags the 27B down at once.** It
  believes the announcements (a forecast of 3.9 after one), and below a
  belief of 50 it cooperated in 1 of 75 decisions. Its cooperation falls from
  1.00 to 0.05, from the first round.
- **The 9B leaves do not move.** They cooperate 0.02, against 0.04 beside a
  9B hub, and their actions ignore their beliefs.
- **The 27B starts to lie.** It never broke a promise in its own star. Here it
  broke 17: first promises made before it read its leaves, then planned
  defence.
- **Nobody gains:** both defect on 225 of the 240 edges, and the payoffs are
  even.
- **Limits.**
  - One composition and five runs.
  - The two models differ in generation, size and precision.
  - The control is shared with the third mixed star, which read it with its
    own labels. The two agree on every message and call read in both.
