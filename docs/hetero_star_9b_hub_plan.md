# Two mixed stars with a 9B hub: Qwen3.8-27B or Qwen3.5-122B in the leaves

This is the plan for the fifth and sixth exploratory experiments with two
models in one network, on the lab server. It was written on 2026-11-12,
before any run of them, and its rules and prediction are fixed here. It takes
the definitions, hand checks and code of `docs/hetero_star_plan.md`, and is
read beside the second and third mixed stars
(`docs/hetero_star_27b_9b_plan.md`, `docs/hetero_star_122b_9b_plan.md`),
where the 9B sat in the leaves.

## Question

In the second and third mixed stars, three 9B leaves, which defect and say
so, turned a 27B hub and a 122B hub into defectors from the first round. Each
of those hubs had three neighbours. This plan puts the 9B in the hub, so that
each leaf has a single neighbour, and that neighbour defects and mostly says
so.
- **Qwen/Qwen3.5-9B, the hub:**
  - in its own stars it cooperates 0.00-0.03 in the hub, and its round-1
    message announces defection in 10 of 15 runs (it promises in 5);
  - before any talk it intends to defect, in every call;
  - it breaks almost every promise it makes (54 of 55 in its three stars);
  - its actions do not follow its beliefs: as the hub it cooperates 0.00-0.05
    on either side of a belief of 50.
- **Qwen/Qwen3.8-27B-FP8, the leaves of one star:** it cooperates in every
  seat of its own star (1.00) and keeps its word. It believes an announced
  defection (a forecast of 3.9 as the hub of the second mixed star) and does
  what it expects (0.99 against 0.08).
- **Qwen/Qwen3.5-122B-A10B, the leaves of the other:** its leaves cooperate
  0.60 in its own star after the update, and act on their beliefs (0.91
  against 0.08). As the hub of the third mixed star it believed the 9B's
  announced defections (2.0) and broke 42 promises, almost all as planned
  defence.

The questions:
- **The hub.** Does a neighbourhood that cooperates, or that cooperates and
  lies, change the 9B at all?
- **The leaves.** Does a hub that defects and says so pull its leaves down,
  when it is their only neighbour?
- **The lies.** Do the leaves lie to it? Does the 27B, which lied beside 9B
  leaves as a hub, lie as a leaf too, and what kind of lie is it?

The agents are never told which model a neighbour is: the prompts are those
of a homogeneous star. Any difference is made by play and talk alone.

## Design

- **Two mixed stars,** four agents each. Agent 0, the hub, is served
  Qwen/Qwen3.5-9B in both.
  - **Star A:** agents 1-3, the leaves, are served Qwen/Qwen3.8-27B-FP8.
  - **Star B:** agents 1-3 are served Qwen/Qwen3.5-122B-A10B.
- **The cell:** `forecast_probe` (session `PROBE`), as in the earlier mixed
  stars: Prisoner's Dilemma, 16 rounds with a hidden horizon, memory 10,
  temperature 0.7, cap 4096, thinking off, two private forecasts per round.
- **5 runs per star.**
- **One same-day control for both: the 9B alone on the star,** the same cell,
  5 runs, in a third lane beside the two. It is the hub's model, as the
  122B was in the first mixed star, so it is the hub's reference for rule 2.
- **The leaves' references** are their models' own stars after the server's
  update:
  - for star A, the 27B's grid and forecast cell (11-10, 480 leaf
    decisions);
  - for star B, the 122B's two forecast cells after the update (11-11 and
    11-12, 480 leaf decisions).
- **Two smoke runs first,** one run of 2 rounds of each mixed star, into
  `pharos_runs/smoke_hetero_9b_hub/runs`. Each must pass the first plan's five
  checks before the runs:
  - every call of agent 0 is answered by the 9B, and every call of a leaf by
    the leaves' model, as the server reports;
  - no `<think>` block, from any model. If a smoke run shows one, it is made
    once more; if the second shows one too, the runs wait for the author's
    decision;
  - every forecast call parses;
  - the round-1 message prompt has 464 tokens for every agent, as on the
    three models' stars;
  - `verify_prompts.py` finds nothing.
- **Placement.** `pharos_runs/tok4096/hetero_9b_hub/runs/` holds three trees:
  - `Qwen3.8-27B-FP8_a0-Qwen3.5-9B`, star A;
  - `Qwen3.5-122B-A10B_a0-Qwen3.5-9B`, star B;
  - `Qwen3.5-9B`, the control.

  The three campaign zips land in `tok4096/hetero_9b_hub/`. The control's,
  `Qwen3.5-9B_star_sessionPROBE_pd.zip`, has the same name as the 9B's
  forecast-cell zips in `tok4096/` (11-09) and `tok4096/hetero_27b_9b/`
  (11-12).
- **The code:** none. `hetero_report.py` (as generalised in `74406fc`) reads
  both stars as they are:
  - the control is the hub's model, so rule 2 reads the hub against the
    control, and rule 3 the leaves against their own stars, as a drop;
  - `--lies leaves` reads rule 5 for the leaves' broken promises.

  No earlier plan paired a hub control with `--lies leaves`. A fixture checks
  the pairing before any run (see "Seen before writing").

## References

The three models' own stars, by role (hub = agent 0, leaves = agents 1-3).
Promises and broken promises are the detector's; announced defections follow
the 9B plan's pattern. The payoff is per neighbour and per round.

| model, cell | runs | hub cooperation | leaves cooperation | hub payoff | leaves payoff | hub broken | leaves broken | hub's messages announcing defection |
|---|---|---|---|---|---|---|---|---|
| 9B, grid baseline (11-06) | 5 | 0.00 | 0.02 | 2.08 | 1.98 | 16/16 | 42/45 | 61/80 |
| 9B, grid no_comm (11-06) | 5 | 0.07 | 0.13 | 2.37 | 2.10 | | | |
| 9B, forecast cell (11-09) | 5 | 0.03 | 0.05 | 2.18 | 2.04 | 16/17 | 33/39 | 58/80 |
| **9B, forecast cell (11-12, after the update)** | 5 | 0.01 | 0.04 | 2.13 | 2.01 | 22/22 | 38/42 | 54/80 |
| 27B, grid baseline (11-10) | 5 | 1.00 | 1.00 | 3.99 | 4.01 | 0/80 | 1/238 | 0/80 |
| 27B, forecast cell (11-10) | 5 | 1.00 | 1.00 | 4.00 | 4.00 | 0/80 | 0/237 | 0/80 |
| **122B, forecast cells (11-11 and 11-12, after the update)** | 10 | 0.69 | 0.60 | 3.20 | 3.65 | 39/146 | 87/368 | 11/160 |
| the second mixed star: 27B hub, 9B leaves (11-12) | 5 | 0.05 | 0.02 | 2.01 | 2.18 | 19/21 | 33/36 | 55/80 |
| the third mixed star: 122B hub, 9B leaves (11-12) | 5 | 0.04 | 0.04 | 2.12 | 2.11 | 39/41 | 56/62 | 36/80 |

- **Runs.** No run's hub in the 9B's three stars is above 0.06. In the 27B's
  stars every run's hub is at 1.00, and its leaves at 0.98 or more. In the
  122B's two stars after the update the leaves' run means go from 0.12 to
  1.00.
- **Round 1 of the 9B's hub** (its three stars, 15 runs): its message
  announces defection in 10 and promises in 5. Before the talk it intends
  to defect in 10 of 10 forecast calls (forecasts 6.0 and 12.0), and it
  plays Defect in every run of its forecast cells.
- **Belief and action** (forecast cells), cooperation at a belief of 50 or
  more against below 50:
  - the 9B's hub: 0.00 (14 decisions) against 0.03 (61) on 11-09, and 0.05
    (20) against 0.00 (60) on 11-12;
  - the 27B: 1.00, and never below 50 (its two forecast cells: 0.99 against
    0.08);
  - the 122B's leaves after the update: 0.91 (303) against 0.08 (176).
- **Forecasts of a neighbour after an announced defection:** the 27B as the
  hub of the second mixed star, 3.9 (196 forecasts); the 122B as the hub of
  the third, 2.0 (167).
- **The kind of lie beside the 9B:**
  - the 27B hub of the second mixed star broke 17 promises (hand where
    read): 4 in round 1, decided after the messages and expecting
    defection, 12 planned defence, 1 planned exploitation;
  - the 122B hub of the third broke 42: 40 planned defence, 2 planned
    exploitation;
  - the 9B's own hub, in its forecast cells, by the detector: 13 and 20
    broken promises with an intention and a belief, of which 4 and 6 planned
    exploitation.
- **The edges.** In the 9B's stars nearly every hub-leaf edge-round is both
  defect: 234 of 239, 221 of 239 and 227 of 239.
- **Round-1 message prompt tokens:** 464 for every agent, on all three stars.

## Hand checks

Those of `docs/hetero_star_plan.md`: blind, with the same seeds. There are
two sheets, one per mixed star, each over that star's runs and the
control's, as in the second and third mixed stars; each star keeps its own
labels.
- **Promises:**
  - every message of a defecting sender that the detector reads as a
    promise, and a random 100 of those it does not (seed 7);
  - if more than 10 of the 100 are strict promises by hand, every such
    message is read (`--dump-rest`);
  - classes U, K, DU, M and N, with the strict reading U + K;
  - the rules take the hand's reading where a message was read, and the
    detector's elsewhere.
- **Inverted forecasts:**
  - every forecast call after the messages that gives at least 50 to a
    neighbour whose message announced defection (a random 100 if more, seed
    13);
  - a random 100 of the other forecast calls, 50 before the messages and 50
    after them (seed 13).

  The 9B inverts most flagged calls (45 of 57, and 43 of 60, in the last two
  sheets). The calls found inverted leave rules 5 and 6, which are given
  both with them and without them.

## Reading rules

Every reading is exploratory: one composition per star, one cell, five runs.
Each rule is read for star A and for star B.

1. **Routing, compliance and the untouched game, read first, for each star
   and the control.** If rule 1 fails for a star, nothing else is read for
   it.
   - **Routing:** every one of the hub's calls is answered by
     Qwen/Qwen3.5-9B, and every one of the leaves' by the leaves' model, as
     the server reports.
   - **Forecasts:** at least 90% of forecast calls are valid, before and
     after, for each role in each cell.
   - **Inversion:** at most 5 calls of the random 100 are inverted.
   - **`verify_prompts.py`** finds nothing, or every hit is in an agent's own
     words.
   - **Tokens:** the round-1 message prompt tokens equal the references, role
     by role: 464.
2. **Does the neighbourhood change the hub?** The hub's cooperation in the
   mixed star minus the control's hub (80 decisions each).
   - +0.20 or more: "the leaves raise the hub's cooperation".
   - -0.20 or less: "the leaves lower the hub's cooperation".
   - Within 0.10: "the hub plays as in its own star".
   - In between: "partly".
   - Reported beside it: run means; the 9B's earlier stars.
3. **Does the hub pull the leaves down?** The drop from the leaves'
   cooperation in their own stars (the references above, 480 decisions) to
   the mixed star's (240).
   - 0.20 or more: "the hub pulls the leaves down".
   - Below 0.10: "the leaves play as in their own star".
   - In between: "partly".
   - Reported beside it: run means; the control's leaves.
4. **Who gains at whose expense?** The hub's payoff per neighbour minus the
   leaves'.
   - +0.5 or more: "the hub gains at the leaves' expense".
   - -0.5 or less: "the leaves gain at the hub's expense".
   - In between: "even".
   - Reported beside it: the four kinds of hub-leaf edge-round, in each cell
     and in the references.
5. **The leaves' lies.** The leaves' broken promises that have a valid
   intention before the talk and a belief. Read only with at least 10;
   otherwise "too few to read".
   - The share of planned exploitation:
     - 0.50 or more: "mostly planned exploitation";
     - below 0.25: "rarely";
     - in between: "partly".
   - Reported beside it:
     - P and the four kinds, in the mixed star, the control and the leaves'
       own stars;
     - the hub's forecast of a leaf after that leaf's kept and broken
       promises, the share of broken promises it believes (50 or more), and
       the AUC. The 9B's forecasts are read with and without its inverted
       calls;
     - the round-1 shift of the hub's forecast of a leaf after that leaf's
       promise.
6. **Belief and action, by role.** Cooperation at a belief of 50 or more,
   against below 50, for each role in each cell, each side with at least 20
   decisions; otherwise "too few to read".
   - A difference of 0.50 or more: "its actions follow its beliefs".
   - Below 0.20: "its actions ignore its beliefs".
   - In between: "partly".
7. **Descriptive, not rules:**
   - round 1 before and after the talk, by role, and the leaves' answer to
     the hub's round-1 message: a promise or an announced defection;
   - the first defection of each mixed run: who, when, planned or not;
   - **does lying pay?** By role, the sender's payoff per neighbour when it
     broke a promise, kept one, or defected without one, and its neighbours'
     cooperation in that round and the next;
   - the hub's own broken promises (`--lies hub`);
   - **the hub by its neighbourhood:** the hub's cooperation in every star run
     with these three models so far, by the hub's model and the leaves'.

**How the numbers are computed.**
- `hetero_report.py` with `--lies leaves` prints rules 1-6 and the
  descriptive splits for each star, and reads that star's hand labels with
  `--hand`. With `--lies hub` it gives the hub's own broken promises.
- The leaves' answer to the hub's round-1 message and the table of hubs by
  neighbourhood are counted apart from the report, by a read-only script
  kept with the outputs.
- `verify_prompts.py` and `audit_corpus.py` run on the three trees.
- The scripts, sheets, keys, labels and outputs are kept beside the runs, in
  `pharos_runs/tok4096/hetero_9b_hub/analysis_27b/` (star A) and
  `pharos_runs/tok4096/hetero_9b_hub/analysis_122b/` (star B).

## Prediction, stated before the run

- **Rule 1** passes for both stars and the control. The risk is the 9B's
  inversions, now in the hub: in its last two cells 2 and 3 of the random
  100 were inverted, against at most 5 allowed.
- **The control** plays as the 9B's earlier stars: its hub and its leaves
  cooperate below 0.20, and every round-1 call before the talk intends to
  defect.
- **Rule 2, both stars: "the hub plays as in its own star".** The 9B's
  actions do not follow its beliefs, so leaves that cooperate or promise
  cannot raise its cooperation.
- **Rule 3, both stars: "the hub pulls the leaves down"** (a drop of 0.20 or
  more, from 1.00 and from 0.60).
  - Each leaf's only neighbour defects in almost every round and mostly
    says so. Both leaf models believe an announced defection and act on
    what they expect.
  - Where the 9B promises in round 1 (5 of its 15 runs), its leaves may
    cooperate once and be exploited; the edges still settle on mutual
    defection within a few rounds.
- **Rule 4, both stars: "even".** The edges settle on mutual defection.
  The hub's gain from round-1 exploitation is too small for +0.5.
- **Rule 5, both stars:** readable, and "rarely planned exploitation".
  - A leaf's belief is its forecast of the hub, which an announced defection
    drops. So a leaf that promises and defects mostly expects the hub to
    defect: planned defence, or a promise made before it read the hub's
    message.
  - Beside 9B leaves, the 27B hub's lies were 1 of 17 planned exploitation,
    and the 122B hub's 2 of 42.
  - The risk, for star A: the 27B leaves stop promising once the hub has
    defected, and the lies are too few to read.
- **Rule 6:**
  - the hub's actions ignore its beliefs, or its side at 50 or more is too
    few to read;
  - in both stars, the leaves' actions follow their beliefs, or their side
    at 50 or more is too few to read.

## Seen before writing

- Every number of the three models' stars above, and of their other cells.
- The results of the first three mixed stars, and the plan of the fourth
  (`docs/hetero_star_27b_122b_plan.md`), written the same day. Its two lanes
  had started at 16:40, before this plan was written; none of their runs
  was read.
- The test of the code: two fixtures, the 9B's star of 11-12 relabelled as a
  mixed star with 27B leaves, and with 122B leaves. Each was read by
  `hetero_report.py` against the 9B's forecast cell of 11-09 as the control,
  with these leaves' references as `--leaves-home`.
  - The control is read as the hub's model. Rules 2 and 3 come out as a
    count made apart gives them, and routing and tokens pass.
  - With `--lies leaves`, the leaves' kinds of lie and the hub's forecasts
    of each leaf agree with a count made apart; so do the hub's kinds with
    `--lies hub`.
  - `--dump` takes both cells into the sheets.

No run of these experiments existed when this was written.

## Limits fixed in advance

- **Scope.** One composition per star, one cell, five runs. The hub is one
  agent per run: 80 decisions.
- **Two changes at once.** The 9B differs from the 27B in generation, size
  and precision, and from the 122B in size and architecture.
- **The leaves' references are older than the control.** The 27B's stars are
  of 11-10 and the 122B's of 11-11 and 11-12, all after the update; only the
  9B runs alone the same day.
- **Stated beliefs.** The forecasts come from separate calls, and nothing
  rewards their accuracy. The hub's forecasts are the 9B's, which it often
  inverts; they are read with and without the calls found inverted.
- **The detector** is not validated on these models; the hand check covers the
  messages of defecting senders, in part by sample.
- **The served model is what the server reports.** The smoke runs check it
  before any run.
- **Server updates:**
  - if one stops the runs, a new smoke run comes before any further run;
  - a lane cut short keeps its runs if it has at least 4 of 5; otherwise it
    is run again whole;
  - the write-up names every run made after an update.

## Reproduce

From `cheaptalk_bench`. First the two smoke runs, then the three lanes side
by side:

```
python campaign.py --provider pharos --model Qwen/Qwen3.8-27B-FP8 --agent-model 0=Qwen/Qwen3.5-9B --session PROBE --topology star --games pd --n-runs 1 --n-rounds 2 --max-new-tokens 4096 --out-root ..\pharos_runs\smoke_hetero_9b_hub\runs --zip-mirror=
python campaign.py --provider pharos --model Qwen/Qwen3.5-122B-A10B --agent-model 0=Qwen/Qwen3.5-9B --session PROBE --topology star --games pd --n-runs 1 --n-rounds 2 --max-new-tokens 4096 --out-root ..\pharos_runs\smoke_hetero_9b_hub\runs --zip-mirror=
python campaign.py --provider pharos --model Qwen/Qwen3.8-27B-FP8 --agent-model 0=Qwen/Qwen3.5-9B --session PROBE --topology star --games pd --n-runs 5 --n-rounds 16 --max-new-tokens 4096 --out-root ..\pharos_runs\tok4096\hetero_9b_hub\runs --zip-mirror=
python campaign.py --provider pharos --model Qwen/Qwen3.5-122B-A10B --agent-model 0=Qwen/Qwen3.5-9B --session PROBE --topology star --games pd --n-runs 5 --n-rounds 16 --max-new-tokens 4096 --out-root ..\pharos_runs\tok4096\hetero_9b_hub\runs --zip-mirror=
python campaign.py --provider pharos --model Qwen/Qwen3.5-9B --session PROBE --topology star --games pd --n-runs 5 --n-rounds 16 --max-new-tokens 4096 --out-root ..\pharos_runs\tok4096\hetero_9b_hub\runs --zip-mirror=
```

Then the checks, the sheets and the reports:

```
python verify_prompts.py ..\pharos_runs\tok4096\hetero_9b_hub\runs
python audit_corpus.py ..\pharos_runs\tok4096\hetero_9b_hub\runs
python hetero_report.py --mixed ..\pharos_runs\tok4096\hetero_9b_hub\runs\Qwen3.8-27B-FP8_a0-Qwen3.5-9B --control ..\pharos_runs\tok4096\hetero_9b_hub\runs\Qwen3.5-9B --dump ..\pharos_runs\tok4096\hetero_9b_hub\analysis_27b
python hetero_report.py --mixed ..\pharos_runs\tok4096\hetero_9b_hub\runs\Qwen3.5-122B-A10B_a0-Qwen3.5-9B --control ..\pharos_runs\tok4096\hetero_9b_hub\runs\Qwen3.5-9B --dump ..\pharos_runs\tok4096\hetero_9b_hub\analysis_122b
python hetero_report.py --mixed ..\pharos_runs\tok4096\hetero_9b_hub\runs\Qwen3.8-27B-FP8_a0-Qwen3.5-9B --control ..\pharos_runs\tok4096\hetero_9b_hub\runs\Qwen3.5-9B --hub-home ..\pharos_runs\tok4096\grid\Qwen3.5-9B ..\pharos_runs\tok4096\probe_9b\Qwen3.5-9B ..\pharos_runs\tok4096\hetero_27b_9b\runs\Qwen3.5-9B --leaves-home ..\pharos_runs\tok4096\grid\Qwen3.8-27B-FP8 ..\pharos_runs\tok4096\probe_27b\Qwen3.8-27B-FP8 --hand ..\pharos_runs\tok4096\hetero_9b_hub\analysis_27b --lies leaves
python hetero_report.py --mixed ..\pharos_runs\tok4096\hetero_9b_hub\runs\Qwen3.5-122B-A10B_a0-Qwen3.5-9B --control ..\pharos_runs\tok4096\hetero_9b_hub\runs\Qwen3.5-9B --hub-home ..\pharos_runs\tok4096\grid\Qwen3.5-9B ..\pharos_runs\tok4096\probe_9b\Qwen3.5-9B ..\pharos_runs\tok4096\hetero_27b_9b\runs\Qwen3.5-9B --leaves-home ..\pharos_runs\tok4096\hetero\runs\Qwen3.5-122B-A10B ..\pharos_runs\tok4096\hetero_122b_9b\runs\Qwen3.5-122B-A10B --hand ..\pharos_runs\tok4096\hetero_9b_hub\analysis_122b --lies leaves
```

**Timing.** On 11-12 the 9B's lanes ran at 2.5-2.8 s per call with four
lanes side by side, and a run took 4-17 minutes. A lane of 5 runs should take
40-80 minutes. Each smoke run takes 1-3 minutes.
