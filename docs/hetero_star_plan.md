# A mixed star: Qwen3.5-122B in the hub, Qwen3.8-27B in the leaves

This is the plan for an exploratory experiment on the lab server, the first
with two models in one network. It was written before any run of it, and its
rules and prediction are fixed here.

## Question

Every run so far put one model in every seat. On the star, the two lab-server
models we know best play almost opposite games:
- **Qwen/Qwen3.5-122B-A10B**
  - Talk is its only source of cooperation: 0.01 in silence.
  - In round 1, before any talk, it intends to defect in every call.
  - It believes talk, and its actions follow its beliefs.
  - It breaks many promises, most of them planned: on its star the hub broke
    25 of 68 (grid), and in the forecast cell 19 of 21 broken promises were
    planned.
- **Qwen/Qwen3.8-27B-FP8**
  - It cooperates in every seat of its star (1.00) and keeps its word: 1
    broken promise in 318.
  - It intends to cooperate before any talk, believes promises (+27 to +31
    in round 1), and does what it expects.

What happens when the 122B sits in the hub, with three 27B agents as its
leaves?
- **The hub.** Does a neighbourhood that keeps its promises change the 122B?
  It could cooperate more, since its beliefs stay high. Or it could defect
  more, since its leaves trust it.
- **The leaves.** Does a hub that lies change the 27B? Are its leaves
  exploited? Do they retaliate, or start to lie?
- **The lies.** When the hub breaks a promise, do the 27B leaves believe it,
  and does the lie pay?

The agents are never told which model a neighbour is: the prompts are those
of a homogeneous star. Any difference is made by play and talk alone.

## Design

- **The mixed star:** four agents. Agent 0, the hub with three edges, is
  served Qwen/Qwen3.5-122B-A10B; agents 1-3, the leaves, Qwen/Qwen3.8-27B-FP8.
- **The cell:** `forecast_probe` (session `PROBE`).
  - It is the baseline with cheap talk: Prisoner's Dilemma, 16 rounds with a
    hidden horizon, memory 10, temperature 0.7, cap 4096, thinking off.
  - Each agent also gives two private forecasts per round, before and after
    the messages. The game's prompts are the baseline's, byte for byte.
  - So cooperation compares with both models' grid stars, and the forecasts
    give each agent's intention and beliefs.
- **5 runs,** as in every reference below.
- **A same-day control: the 122B alone on the star,** the same cell, 5 runs,
  in a second lane beside the first.
  - The 122B's earlier stars ran on 10-30 (grid) and 11-04 (forecast cell),
    before the server's model update of 11-09.
  - The control separates the leaves' effect on the hub from any change in
    the server. The 27B's references ran after the update (11-10).
- **A smoke run first:** one run of 2 rounds of the mixed star, into
  `pharos_runs/smoke_hetero/runs`. It must pass five checks before the runs:
  - every call of agent 0 is answered by the 122B, and every call of a leaf by
    the 27B, as the server reports;
  - no `<think>` block, from either model;
  - every forecast call parses;
  - the round-1 message prompt has 464 tokens for every agent, as on both
    models' stars;
  - `verify_prompts.py` finds nothing.
- **Placement.** `pharos_runs/tok4096/hetero/runs/` holds two trees:
  - `Qwen3.8-27B-FP8_a0-Qwen3.5-122B-A10B`, the mixed star;
  - `Qwen3.5-122B-A10B`, the control.

  The two campaign zips land in `tok4096/hetero/`.
- **The code** (this commit):
  - `--agent-model AGENT=MODEL_ID` in `campaign.py` and
    `run_all_scenarios.py`, and the config field `agent_models`;
  - every agent gets its model's client. Everything else is shared:
    provider, temperature, cap, retries;
  - in a mixed run, every call records the model the server says answered
    it;
  - a mixed run gets its own tree and zip names, and the readers of the
    grid (`forecast_report.py`, `scale_report.py`, `intent_report.py`,
    `cross_model_analysis.py`) leave it out;
  - without the option, every run is as before: an offline test found the
    calls of the game byte-identical, and the existing reports print the
    same lines;
  - `hetero_report.py` computes the rules below, writes the blind sheets of
    the hand checks, and reads their labels.

## References

The two models' own stars, by role (hub = agent 0, leaves = agents 1-3).
Promises and broken promises are the detector's. The payoff is per neighbour
and per round.

| model, cell | runs | hub cooperation | leaves cooperation | hub payoff | leaves payoff | hub broken | leaves broken |
|---|---|---|---|---|---|---|---|
| 122B, grid baseline (10-30) | 5 | 0.60 | 0.50 | 2.95 | 3.47 | 25/68 | 45/162 |
| 122B, grid no_comm (10-30) | 5 | 0.01 | 0.01 | 2.02 | 2.04 | | |
| 122B, forecast cell (11-04) | 5 | 0.66 | 0.56 | 3.11 | 3.63 | 21/73 | 49/178 |
| 27B, grid baseline (11-10) | 5 | 1.00 | 1.00 | 3.99 | 4.01 | 0/80 | 1/238 |
| 27B, grid no_comm (11-10) | 5 | 0.37 | 0.38 | 2.90 | 2.76 | | |
| 27B, forecast cell (11-10) | 5 | 1.00 | 1.00 | 4.00 | 4.00 | 0/80 | 0/237 |

- **Runs are all or nothing** on the 122B's star. The hub's run means are
  0.31, 0.38, 1.00, 0.31, 1.00 (grid) and 0.56, 0.50, 0.88, 0.38, 1.00
  (forecast cell).
- **Who exploits whom on the 122B's star:**
  - in the grid's 240 hub-leaf edge-rounds, the hub defects on a cooperating
    leaf in 15, and a leaf on a cooperating hub in 40;
  - in the forecast cell, 24 and 49.

  The 27B's star has none, apart from one leaf in the grid.
- **Round 1, before the talk** (forecast cells):
  - the 122B's hub intends to cooperate in 0 of 5 calls (forecast 21.0), and
    its leaves in 0 of 15 (23.3);
  - the 27B's hub in 5 of 5 (60.0), its leaves in 14 of 15 (58.7).
- **Belief and action** (forecast cells), cooperation at a belief of 50 or
  more against below 50:
  - the 122B's hub 0.89 against 0.23, its leaves 0.86 against 0.15;
  - the 27B: 1.00, and never below 50.
- **The kind of lie** of the 122B's hub (forecast cell): 5 of its 21 broken
  promises are planned exploitation, 14 planned defence, 2 decided after
  the messages.
- **Round-1 message prompt tokens:** 464 for every agent, on both models'
  stars.

## Definitions

These are the competitive plan's (`docs/qwen38_27b_competitive_plan.md`),
by role:
- forecast, promise, kept and broken promise;
- intention before and after the talk, P;
- belief: the mean forecast of one's neighbours after the messages;
- first defection: a broken promise whose sender had seen no neighbour defect
  in any earlier round of the run;
- the four kinds of lie: planned exploitation, planned defence, decided after
  the messages expecting cooperation, and expecting defection;
- announced defection, with the 9B plan's pattern unchanged.

Three are new:
- **Role:** hub (agent 0) or leaves (agents 1-3).
- **Payoff per neighbour:** an agent's round payoff over its edges (3 for
  the hub, 1 for a leaf).
- **Hub-leaf edge-rounds:** each of the three edges in each round is one of
  four:
  - both cooperate;
  - the hub defects on a cooperating leaf;
  - a leaf defects on a cooperating hub;
  - both defect.

## Hand checks

The competitive plan's, read the same way: blind, with the same seeds, over
the mixed star's and the control's runs together.
- **Promises:**
  - every message of a defecting sender that the detector reads as a
    promise, and a random 100 of those it does not (seed 7);
  - if more than 10 of the 100 are promises by hand, every such message is
    read;
  - classes U, K, DU, M and N, with the strict reading U + K;
  - the rules take the hand's reading where a message was read, and the
    detector's elsewhere.
- **Inverted forecasts:**
  - every forecast call after the messages that gives at least 50 to a
    neighbour whose message announced defection (a random 100 if more,
    seed 13);
  - a random 100 of the other forecast calls, 50 before the messages and 50
    after them (seed 13).

  The calls found inverted leave rules 5 and 6. Those rules are given both
  with them and without them.

`hetero_report.py --dump` writes both sheets, and `--dump-rest` the second
sheet of promises.

## Reading rules

Every reading is exploratory: one composition, one cell, five runs, and runs
that may be all or nothing.

1. **Routing, compliance and the untouched game, read first, for both
   cells.** If rule 1 fails, nothing else is read.
   - **Routing:** in the mixed star, every one of the hub's calls is
     answered by Qwen/Qwen3.5-122B-A10B, and every one of the leaves' by
     Qwen/Qwen3.8-27B-FP8, as the server reports.
   - **Forecasts:** at least 90% of forecast calls are valid, before and
     after, for each role in each cell.
   - **Inversion:** at most 5 calls of the random 100 are inverted.
   - **`verify_prompts.py`** finds nothing, or every hit is in an agent's own
     words.
   - **Tokens:** the round-1 message prompt tokens equal the references, role
     by role: 464.
2. **Does the neighbourhood change the hub?** The hub's cooperation in the
   mixed star minus the hub's in the control, 80 decisions each.
   - +0.20 or more: "the leaves raise the hub's cooperation".
   - -0.20 or less: "the leaves lower the hub's cooperation".
   - Within 0.10: "the hub plays as in its own star".
   - In between: "partly".
   - Reported beside it: run means; the 122B's earlier stars (hub 0.60 and
     0.66); the control against them.
3. **Does the hub change the leaves?** The leaves' cooperation in the mixed
   star against the 27B's own star (its grid and its forecast cell, 480
   decisions).
   - A drop of 0.20 or more: "the hub pulls the leaves down".
   - Below 0.10: "the leaves play as in their own star".
   - In between: "partly".
4. **Who gains at whose expense?** The hub's payoff per neighbour minus the
   leaves'.
   - +0.5 or more: "the hub gains at the leaves' expense".
   - -0.5 or less: "the leaves gain at the hub's expense".
   - In between: "even".
   - Reported beside it: the four kinds of hub-leaf edge-round, in each cell
     and in both references.
5. **The hub's lies.** The hub's broken promises that have a valid intention
   before the talk and a belief. Read only with at least 10; otherwise "too
   few to read".
   - The share of planned exploitation:
     - 0.50 or more: "mostly planned exploitation";
     - below 0.25: "rarely";
     - in between: "partly".
   - Reported beside it:
     - P and the four kinds, in the mixed star, the control and the 122B's
       earlier forecast cell;
     - the leaves' forecast of the hub after its kept and after its broken
       promises, the share of its broken promises they believe (50 or
       more), and the AUC;
     - the round-1 shift of a leaf's forecast of the hub after the hub's
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
   - the leaves' own broken promises: do the 27B leaves start to lie?

**How the numbers are computed.**
- `hetero_report.py` prints rules 1-6 and the descriptive splits, and reads
  the hand labels with `--hand`.
- `verify_prompts.py` and `audit_corpus.py` run on both trees.
- The scripts, sheets, keys, labels and outputs are kept beside the runs, in
  `pharos_runs/tok4096/hetero/analysis/`.

## Prediction, stated before the run

- **Rule 1** passes for both cells.
- **The control** plays as the 122B's earlier stars: its hub's cooperation
  is within 0.20 of 0.63, their mean.
- **Rule 2: "the leaves raise the hub's cooperation"** (+0.20 or more).
  - The hub's actions follow its beliefs (0.89 at 50 or more).
  - Leaves that keep their promises keep those beliefs high.
- **Rule 3:** the leaves are not pulled down: a drop below 0.20.
- **Rule 4:** "even".
- **Rule 5:** the hub breaks fewer promises than in the control. If at least
  10 can be read:
  - "mostly planned exploitation": a hub that plans to defect against
    leaves it expects to cooperate is exploiting them;
  - the leaves believe at least half of them.
- **Rule 6:** the hub's actions follow its beliefs. The leaves' do too, or
  they are too few to read below 50.

## Seen before writing

- Every number of the two models' stars above, and of their other cells.
- The offline test of the code and the reports' regression on the existing
  runs.
- A fixture: the 27B's forecast runs on the star, relabelled as a mixed
  star, read by `hetero_report.py` against the 122B's forecast runs.

No run of this experiment existed when this was written.

## Limits fixed in advance

- **Scope.** One composition, one cell, five runs. The hub is one agent per
  run: 80 decisions per cell.
- **Two changes at once.** The two models differ in generation, size and
  precision. "Strong" and "weak" are shorthand.
- **Stated beliefs.** The forecasts come from separate calls, and nothing
  rewards their accuracy.
- **The detector** is not validated on these models; the hand check covers
  the messages of defecting senders.
- **The served model is what the server reports.** The smoke run checks it
  before any run.
- **Server updates:**
  - if one stops the runs, a new smoke run comes before any further run;
  - a lane cut short keeps its runs if it has at least 4 of 5; otherwise it
    is run again whole;
  - the write-up names every run made after an update.
- **The reverse composition** (a 27B hub with 122B leaves) is not part of
  this plan.

## Reproduce

From `cheaptalk_bench`. First the smoke run, then the two lanes side by
side:

```
python campaign.py --provider pharos --model Qwen/Qwen3.8-27B-FP8 --agent-model 0=Qwen/Qwen3.5-122B-A10B --session PROBE --topology star --games pd --n-runs 1 --n-rounds 2 --max-new-tokens 4096 --out-root ..\pharos_runs\smoke_hetero\runs --zip-mirror=
python campaign.py --provider pharos --model Qwen/Qwen3.8-27B-FP8 --agent-model 0=Qwen/Qwen3.5-122B-A10B --session PROBE --topology star --games pd --n-runs 5 --n-rounds 16 --max-new-tokens 4096 --out-root ..\pharos_runs\tok4096\hetero\runs --zip-mirror=
python campaign.py --provider pharos --model Qwen/Qwen3.5-122B-A10B --session PROBE --topology star --games pd --n-runs 5 --n-rounds 16 --max-new-tokens 4096 --out-root ..\pharos_runs\tok4096\hetero\runs --zip-mirror=
```

Then the checks, the sheets and the report:

```
python verify_prompts.py ..\pharos_runs\tok4096\hetero\runs\Qwen3.8-27B-FP8_a0-Qwen3.5-122B-A10B ..\pharos_runs\tok4096\hetero\runs\Qwen3.5-122B-A10B
python audit_corpus.py ..\pharos_runs\tok4096\hetero\runs\Qwen3.8-27B-FP8_a0-Qwen3.5-122B-A10B ..\pharos_runs\tok4096\hetero\runs\Qwen3.5-122B-A10B
python hetero_report.py --mixed ..\pharos_runs\tok4096\hetero\runs\Qwen3.8-27B-FP8_a0-Qwen3.5-122B-A10B --control ..\pharos_runs\tok4096\hetero\runs\Qwen3.5-122B-A10B --dump ..\pharos_runs\tok4096\hetero\analysis
python hetero_report.py --mixed ..\pharos_runs\tok4096\hetero\runs\Qwen3.8-27B-FP8_a0-Qwen3.5-122B-A10B --control ..\pharos_runs\tok4096\hetero\runs\Qwen3.5-122B-A10B --hub-home ..\pharos_runs\tok4096\grid\Qwen3.5-122B-A10B ..\pharos_runs\tok4096\probe\Qwen3.5-122B-A10B --leaves-home ..\pharos_runs\tok4096\grid\Qwen3.8-27B-FP8 ..\pharos_runs\tok4096\probe_27b\Qwen3.8-27B-FP8 --hand ..\pharos_runs\tok4096\hetero\analysis
```

**Timing.** The forecast cells of both models ran at 1.4-3.7 s per call with
three lanes (the 122B's on 11-04, the 27B's on 11-10 and 11-11). A run has
256 calls, or 6-16 minutes, so a lane of 5 runs should take 40-70 minutes.
The smoke run takes 1-2 minutes.

## Results, 2026-11-11

Read on 2026-11-11 after the 10 runs. Every reading is exploratory, as fixed
above.
- The rules come from `hetero_report.py`, as fixed in the commit that adds
  this section. Rule 5's split of the leaves' forecasts now takes the hand's
  reading of the hub's messages where it read them, as "Hand checks" says.
  Before, it took the detector's; the two versions are given below.
- The scripts, the hand sheets with their keys and labels, and the outputs
  are kept in `pharos_runs/tok4096/hetero/analysis/`.

**Runs and checks.**
- **When and on what.** The two lanes ran side by side on 2026-11-11, on
  `1ddc2ae`, which holds this plan and was pushed at 13:39.
  - The mixed star ran from 14:16 to 14:52, and the control from 14:20 to
    14:56.
  - A run took 5.7-9.2 minutes. Each lane averaged 1.69 s per call and took
    36 minutes; the plan foresaw 40-70.
  - No run stopped, and no server update came during them.
- **The smoke run** (14:04-14:05) passed the five checks:
  - routing: the hub's 8 calls were answered by the 122B and the leaves' 24
    by the 27B, as the server reports;
  - no `<think>` block in its 32 calls;
  - 16 of 16 forecast calls parse;
  - the round-1 message prompt has 464 tokens for every agent;
  - `verify_prompts.py` finds nothing in its 40 prompts.

  It ran at 1.64 s per call. All four agents cooperated in both rounds. The
  hub intended to defect before the talk (forecast 20), and to cooperate
  after the leaves' promises (95).
- **`verify_prompts.py`** rebuilt 3,200 prompts and flags one run, in three
  prompts. The words are "remaining rounds", from a leaf's own message in
  round 7 of mixed run 3 ("... for both of us in all remaining rounds"). They
  reach that leaf's own prompt later in round 7, and the hub's in rounds 7
  and 8. `horizon_hits.py` finds no other horizon wording in any agent's
  message.
- `audit_corpus.py` finds no issue and no duplicate history.
- **Calls cut at the cap: 3 of 2,560.** One is a forecast of the mixed hub
  after the messages, left invalid. Two are messages in the control, left
  empty. No decision is invalid.
- **`<think>` blocks, all from the 122B:** 1 of the mixed hub's 320 calls,
  and 5 of the control's 1,280. Every forecast among them was read from the
  restarted answer. The 122B's forecast cell of 11-04 had 9 in 1,280.
- **Configs.** Every config equals the run of the same number in the
  reference forecast cell, apart from the output folder: the control against
  the 122B's cell (11-04), the mixed star against the 27B's (11-10). The
  mixed star's also differs in `agent_models`.
- The two campaign zips and each tree's inner zips are intact and
  byte-identical to the runs on disk.

### The hand checks

- **Promises.** The 10 runs hold 132 messages of defecting senders. The
  detector reads 67 of them as promises. The other 65 are fewer than the 100
  the sample asks for, so all were read, in one blind sheet (seed 7).
  - By hand: U 35, K 32, DU 10, M 3, N 52. That makes 67 strict promises
    (U + K).
  - The detector finds 52 of them. It also reads 15 messages as promises
    that are not strict promises by hand: 12 N, 2 M and 1 DU. Most are "I
    will cooperate only if you prove ...", which puts cooperation after
    proof.
  - It misses 15, most of them "I will cooperate (this round) only if you
    do; otherwise, I will defect".
  - By cell and role: the mixed hub 4 messages (3 strict), the mixed leaves
    11 (6), the control's hub 23 (19), the control's leaves 94 (39).
  - The reading notes follow the competitive cell's second sheet. An appeal
    or a demand whose only first-person statement is a threat is DU.
- **Inverted forecasts.** 112 calls were read, blind to the set they came
  from: the 12 flagged calls, and a random 100 (50 before the messages, 50
  after them, seed 13).
  - None is inverted, and none is unclear.
  - The flagged calls give high forecasts after conditional threats ("Let us
    all cooperate this round ...; I will defect if you do not"). Their
    reasoning reads the cooperative half.
  - So rules 5 and 6 read the same with and without the plan's correction,
    and only one version is given.

### Rule 1: it passes, for both cells

- **Routing:** 1,280 of the mixed star's 1,280 calls were answered by the
  planned model, as the server reports. The hub's 320 were answered by
  Qwen/Qwen3.5-122B-A10B, the leaves' 960 by Qwen/Qwen3.8-27B-FP8.
- **Forecasts:**
  - the mixed hub: 79 of 80 valid before the messages, 79 of 80 after them;
  - the mixed leaves: 240 of 240, before and after;
  - the control's hub: 80 of 80;
  - the control's leaves: 240 of 240 before, 239 of 240 after.
- **Inverted calls:** 0 of the random 100, at most 5 allowed.
- **`verify_prompts.py`:** one run flagged, in an agent's own words (above).
- **Tokens:** the round-1 message prompt has 464 tokens in every role and
  cell, as in both models' stars.

### Cooperation by role

Run means are in brackets.

| star | hub | leaves |
|---|---|---|
| mixed | **0.95** (1.00, 1.00, 0.94, 0.88, 0.94) | 0.95 (1.00, 1.00, 0.96, 0.85, 0.96) |
| control: the 122B alone | 0.71 (0.44, 0.88, 0.88, 1.00, 0.38) | 0.61 (0.19, 0.88, 0.77, 0.98, 0.23) |
| the 122B's earlier stars (grid 10-30, forecast cell 11-04) | 0.63 | 0.53 |
| the 27B's star (grid and forecast cell, 11-10) | 1.00 | 1.00 |

Two of the five mixed runs have no defection at all in 16 rounds.

### The control: the 122B plays as before the update

- **Its hub cooperates 0.71, within 0.20 of 0.63,** as predicted. Its leaves
  cooperate 0.61, against 0.53.
- **Before the talk in round 1,** the 122B intends to defect in all 25 of its
  calls (5 mixed hubs, 5 control hubs, 15 control leaves), as in all 20 on
  11-04.
  - The mean forecasts in the control are 24.0 for the hub and 21.7 for the
    leaves. On 11-04 they were 21.0 and 23.3.
- **Its hub's lies are close to 11-04's:** P 0.79 against 0.90, and planned
  exploitation 0.26 against 0.24 (rule 5).
- So the server's update of 11-09 has not changed the 122B in this cell.
  Rule 2 reads the leaves' effect.

### Rule 2: the leaves raise the hub's cooperation

- **The hub cooperates 0.95 in the mixed star and 0.71 in the control:
  +23.7 points.** That is "the leaves raise the hub's cooperation", as
  predicted.
- **Beside it:** the 122B's earlier stars, hub 0.60 (grid) and 0.66
  (forecast cell). The control is 0.08 above their mean.
- **By run.** No mixed run's hub falls below 0.88. Two of the control's runs
  collapse (0.44 and 0.38). Of all 15 of the 122B's own stars (the 10
  earlier and the control's 5), 8 have a hub below 0.60.
  - So the difference rests on runs that collapse in the 122B's own star and
    never did in the mixed star.
  - An exact permutation test of the hub's run means, outside the plan,
    gives a one-sided p of 0.075 against the control's 5 runs. Against all
    15 of the 122B's own stars it gives 0.029.
- **The hub's belief stays high in the mixed star.** The belief is its mean
  forecast of the leaves after the messages.
  - Mixed star, by run: 97, 97, 96, 83 and 91, below 50 in 3 of 79
    decisions.
  - Control: 29, 86, 83, 95 and 43, below 50 in 24 of 80. The two low runs
    are the two that collapse.
  - This is the mechanism the prediction gave.

### Rule 3: the leaves play as in their own star

- **The leaves cooperate 0.95, against 1.00 in the 27B's own star** (479 of
  480). That is a drop of 4.4 points: "the leaves play as in their own
  star", as predicted.
- **But they defected 11 times in 240, against once in 480 at home.**
  - 9 follow a lie of the hub. In run 4, after the hub defected in round 5,
    all three leaves defect in round 6 ("I noticed your defection last
    round; I will defect this round in response"). All three defect again in
    round 7, and one in round 8 ("I am currently in a position of
    advantage"). In run 5, after the hub's round-1 lie, two leaves defect in
    round 2.
  - 2 come from one leaf of run 3, in rounds 15 and 16: "Since the game is
    finite ..., the optimal strategy is to defect in the final round". The
    horizon is hidden: no prompt says how many rounds there are.
  - Full cooperation returned: from round 3 in run 5, and from round 9 in
    run 4.
- **The leaves broke 6 strict promises,** by hand. In the 27B's own star they
  broke 1 of 475, by the detector.
  - 4 came while the leaves punished the hub, in runs 4 and 5. Each was
    planned before the talk. 3 of them are, by the plan's definitions,
    planned exploitation: the leaf expected the hub, which had just
    promised, to cooperate.
  - 2 came from run 3's leaf. It intended to cooperate before and after the
    talk, and decided in the action call.

### Rule 4: even

**Payoff per neighbour: hub 3.95, leaves 3.92. That is "even",** as
predicted.

| star | hub-leaf edge-rounds | both cooperate | the hub defects on a cooperating leaf | a leaf defects on a cooperating hub | both defect | hub payoff | leaves payoff | reading |
|---|---|---|---|---|---|---|---|---|
| mixed | 240 | 221 | 8 | 7 | 4 | 3.95 | 3.92 | even |
| control | 240 | 125 | 21 | 46 | 48 | 3.20 | 3.72 | the leaves gain at the hub's expense |
| the 122B's earlier stars | 480 | 214 | 39 | 89 | 138 | 3.03 | 3.55 | the leaves gain at the hub's expense |
| the 27B's star | 480 | 479 | 0 | 1 | 0 | 3.99 | 4.00 | even |

In the 122B's own star its leaves exploit the hub more often than it
exploits them: 46 against 21 today, 89 against 39 before. In the mixed star
both are rare.

### Rule 5: too few lies to read

- **The hub promised in 78 of its 80 decisions and broke 3 of those
  promises.** That is "too few to read" (fewer than 10). The control's hub
  broke 19.
  - So the hub lies less than in its own star, as predicted.
  - The rest of the prediction cannot be read: mostly planned exploitation,
    and believed by at least half.
- **The three lies are one of each kind:**
  - **Run 5, round 1: planned exploitation.**
    - Before the talk it intended to defect (forecast 20).
    - It wrote "Let us all cooperate this round for mutual benefit; I will
      defect if you do not". After the leaves' promises it forecast 57.
    - Its action call: "In the first round of an unknown-length repeated
      game, the rational strategy to maximize my own cumulative score is to
      defect immediately."
  - **Run 4, round 5: decided in the action call, expecting cooperation.**
    After four rounds of full cooperation, it intended to cooperate before
    and after the talk (forecast 98), and promised. Its action call: "Since
    I do not know if this is the last round, ..."
  - **Run 4, round 6: decided after the messages, expecting defection.** It
    promised again. All three leaves announced their punishment, and its
    forecast fell from 80 to 0.

| star | the hub's promises | broken | P | planned exploitation | planned defence | decided after, expecting C | decided after, expecting D | reading |
|---|---|---|---|---|---|---|---|---|
| mixed | 78/80 | 3 | 1/3 | 1 | 0 | 1 | 1 | too few to read |
| control | 73/80 | 19 | 15/19 = 0.79 | 5 (0.26) | 10 | 2 | 2 | partly |
| the 122B's forecast cell, 11-04 (detector) | | 21 | 19/21 = 0.90 | 5 (0.24) | 14 | 1 | 1 | rarely |

- **The leaves' forecasts of the hub,** with the hand's reading of the hub's
  messages where read:
  - after a kept promise, 93.2 (225 forecasts);
  - after a broken one, 77.2 (9); 7 of the 9 are 50 or more; AUC 0.80.
- **The two lies that came without warning were believed by all three
  leaves** (85-95): run 5's round 1 and run 4's round 5. The lie that came
  after the betrayal mostly was not (30, 40 and 80).
- **The detector's reading** of the hub's messages, which the report used
  before the fix, gives 6 broken, 72.5, 4 of 6 and AUC 0.74. The detector
  misses the hub's round-1 promise in run 5.
- **Round 1:** a leaf's forecast of the hub moves +40.3 after the hub's
  promise (15 pairs), from 46.7 to 87.0. In the 27B's own star it moves
  +27.3, from 58.7 to 86.0.
- **Lying did not pay the hub.**
  - Its 3 lies earned 4.67 per neighbour in their round, against 3.91 for a
    kept promise.
  - In the next round its leaves cooperated 0.11, against 0.99 after a kept
    promise.

### Rule 6: belief and action

| star | role | at a belief of 50 or more | below 50 | reading |
|---|---|---|---|---|
| mixed | hub | 73/76 = 0.96 | 2/3 | too few to read |
| mixed | leaves | 228/235 = 0.97 | 1/5 | too few to read |
| control | hub | 49/56 = 0.88 | 8/24 = 0.33 | its actions follow its beliefs |
| control | leaves | 140/156 = 0.90 | 6/83 = 0.07 | its actions follow its beliefs |

- The prediction for the hub can be read only in the control, where it
  holds. In the mixed star the hub's belief fell below 50 in 3 decisions.
- The leaves' side below 50 is too small to read, which the prediction
  allowed.
- Beside it, the 122B's forecast cell of 11-04: hub 0.89 against 0.23,
  leaves 0.86 against 0.15.

### Rule 7 (descriptive)

**Round 1, before and after the talk.**

| star | role | intends C before (forecast) | after | plays C |
|---|---|---|---|---|
| mixed | hub | 0/5 (17.0) | 3/5 | 4/5 |
| mixed | leaves | 13/15 (46.7) | 14/15 | 15/15 |
| control | hub | 0/5 (24.0) | 4/5 | 5/5 |
| control | leaves | 0/15 (21.7) | 12/15 | 11/15 |

The 27B leaves' call before the talk has the same prompt as in the 27B's
own forecast cell. There, 14 of 15 intended to cooperate, with a forecast of
58.7.

**The first defection of each mixed run.**
- Runs 1 and 2: none.
- Run 3: a leaf, in round 15. It intended to cooperate before and after the
  talk (the guessed end, under rule 3).
- Run 4: the hub, in round 5. It intended to cooperate before and after the
  talk.
- Run 5: the hub, in round 1, planned.

**Does lying pay?** For each decision: the sender's payoff per neighbour in
the round, and the share of its neighbours that cooperate, that round and
the next.

| star | role | the sender | decisions | payoff per neighbour | neighbours cooperating, that round | next round |
|---|---|---|---|---|---|---|
| mixed | hub | broke a promise | 3 | 4.67 | 0.67 | 0.11 |
| mixed | hub | kept a promise | 75 | 3.91 | 0.97 | 0.99 |
| mixed | hub | defected without a promise | 1 | 4.67 | 0.67 | - |
| mixed | hub | cooperated without a promise | 1 | 4.00 | 1.00 | 1.00 |
| mixed | leaves | broke a promise | 6 | 5.33 | 0.83 | 0.80 |
| mixed | leaves | kept a promise | 228 | 3.89 | 0.96 | 0.96 |
| mixed | leaves | defected without a promise | 5 | 3.60 | 0.40 | 1.00 |
| mixed | leaves | cooperated without a promise | 1 | 4.00 | 1.00 | 1.00 |
| control | hub | broke a promise | 19 | 3.40 | 0.35 | 0.16 |
| control | hub | kept a promise | 54 | 3.24 | 0.75 | 0.78 |
| control | hub | defected without a promise | 4 | 2.33 | 0.08 | 0.25 |
| control | hub | cooperated without a promise | 3 | 2.33 | 0.44 | 0.44 |
| control | leaves | broke a promise | 39 | 4.56 | 0.64 | 0.45 |
| control | leaves | kept a promise | 143 | 3.62 | 0.87 | 0.84 |
| control | leaves | defected without a promise | 55 | 3.53 | 0.38 | 0.50 |
| control | leaves | cooperated without a promise | 3 | 1.00 | 0.00 | 0.67 |

- In the mixed star a lie earns more than a kept promise within its round.
- The hub's lies are punished at once: 0.11 in the next round.
- After a leaf's lie, the hub cooperated in 4 of the 5 next rounds; the
  sixth came in the last round.
- These are 9 decisions in all, and descriptive.

**Do the 27B leaves start to lie?** Only after the hub has lied, and at an
end that one leaf guessed (rule 3).

### The prediction, read

| | predicted | found | |
|---|---|---|---|
| rule 1 | passes for both cells | passes | held |
| the control | hub within 0.20 of 0.63 | 0.71 | held |
| rule 2 | the leaves raise the hub's cooperation | +23.7 | held |
| rule 3 | a drop below 0.20 | 4.4: as in their own star | held |
| rule 4 | even | 3.95 against 3.92 | held |
| rule 5 | fewer broken promises than the control | 3 against 19 | held |
| rule 5, with 10 or more | mostly planned exploitation; believed by at least half | 3: too few to read | not read |
| rule 6 | the hub follows its beliefs; the leaves too, or too few below 50 | the hub follows in the control, too few in the mixed star; the leaves too few | held where it can be read |

### In words

- **A neighbourhood that keeps its word keeps the 122B cooperating.** In its
  own star its runs collapse; in the mixed star none did. The hub cooperated
  0.95, against 0.71 the same day. Its belief in its leaves stayed high, and
  its actions follow its beliefs.
- **Its habits stay.** It still intends to defect before the first talk,
  every time. And it still lies: 3 times in 78 promises, once by plan in
  round 1.
- **The 27B leaves believe, and retaliate.** They believed the hub's two
  unwarned lies, and defected in the very next round. Lying did not pay the
  hub.
- **The 27B leaves lie only after the hub has lied, or at an end they
  guess.** Four of their six broken promises came while they punished the
  hub. Two came from one leaf that took round 15 for the last.
- **Neither side exploits the other:** 3.95 against 3.92 per neighbour. In
  the 122B's own star the leaves gain at the hub's expense.
- **Limits.**
  - One composition, five runs, and a difference carried by runs that
    collapse in the 122B's own star.
  - The two models differ in generation, size and precision.
