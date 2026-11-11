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
