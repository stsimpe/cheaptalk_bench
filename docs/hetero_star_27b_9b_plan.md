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
