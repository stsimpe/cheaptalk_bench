# A 27B star with one or two 9B leaves: how many defectors does it take?

This is the plan for the seventh and eighth exploratory experiments with two
models in one network, on the lab server. It was written on 2026-11-13,
before any run of them, and its rules and prediction are fixed here. It was
committed on 2026-11-18; what was seen in between is listed at the end of
"Seen before writing", and nothing in the rules, the references or the
prediction changed. It takes the cell, the hand checks and the definitions of
`docs/hetero_star_plan.md` and `docs/hetero_star_27b_9b_plan.md`, and reads
its two stars beside the 27B's own star and the second mixed star, where all
three leaves were the 9B. It is the first plan whose leaves are not all one
model, so it comes with its own report, `dose_report.py`.

## Question

The 27B cooperates in every seat of its own star (1.00). Beside three 9B
leaves, which defect and say so, it fell from round 1 (0.05) and broke 17
promises. This plan asks what one or two such leaves do to it.
- **Qwen/Qwen3.8-27B-FP8, the hub and the other leaves:**
  - it keeps its word in its own star: no broken promise in 160 hub
    decisions, 1 in its leaves' 475 promises;
  - it believes promises (95.6 after one, a round-1 shift of +28.3) and
    announced defections (3.9 after one, as the hub of the second mixed
    star);
  - it does what it expects. Its own stars never put it below a belief of
    50. Across its two forecast cells it cooperates 0.99 at a belief of 50
    or more and 0.08 below; as the hub of the second mixed star, 3 of 5 at
    50 or more and 1 of 75 below;
  - as a hub, its belief is the mean of its three forecasts. In the fourth
    mixed star, in the 9 rounds after exactly one leaf had defected while
    the other two cooperated, it cooperated in 7. Both defections came at a
    belief of 65-67, from a sum of the round's payoffs (14 points against
    9);
  - as the leaves of the first mixed star, it answered the 122B hub's
    defection in the next round, and returned to cooperation.
- **Qwen/Qwen3.5-9B, one or two leaves:** in its own star after the update
  (11-12) its leaves cooperate 0.04 and its hub 0.01. Its leaves announce
  their defection in 180 of 239 messages; it breaks 52 of its 56 promises;
  its actions do not follow its beliefs.

The questions:
- **The threshold.** How many of the three leaves must defect, and say so,
  before a 27B hub falls? With one, the mean of its three forecasts should
  stay above 50 (about (95.6 + 95.6 + 3.9) / 3 = 65); with two it should
  fall below (about 34). Does the hub do what it expects, or what the
  round's payoff sum says?
- **The contagion.** A hub plays one action for its three edges. When it
  defects because of a 9B leaf, it defects on its 27B leaves too, and breaks
  its promise to them. Does the defection reach the 27B leaves, which never
  defect in their own star?
- **Honesty and lies.** Does announced defection pay against a 27B hub? Does
  the 27B hub lie to its own kind, and do they believe it?

The agents are never told which model a neighbour is: the prompts are those
of a homogeneous star. Any difference is made by play and talk alone.

## Design

- **Two mixed stars,** four agents each. Agent 0, the hub, is served
  Qwen/Qwen3.8-27B-FP8 in both.
  - **Star 1 (one 9B leaf):** agents 1 and 2 are served the 27B, agent 3
    Qwen/Qwen3.5-9B.
  - **Star 2 (two 9B leaves):** agent 1 is served the 27B, agents 2 and 3
    the 9B.
  - In a star the leaves are alike: each has the hub as its only neighbour.
    Which leaf gets the 9B changes nothing in the prompts but its number.
- **The cell:** `forecast_probe` (session `PROBE`), as in the earlier mixed
  stars: Prisoner's Dilemma, 16 rounds with a hidden horizon, memory 10,
  temperature 0.7, cap 4096, thinking off, two private forecasts per round.
- **5 runs per star.**
- **The references,** all run after the server's update of 11-09:
  - no 9B leaf: the 27B's own star, its grid baseline and its forecast cell
    (11-10, 10 runs);
  - three 9B leaves: the second mixed star (11-12, 5 runs);
  - the 9B alone: the second mixed star's control (11-12, 5 runs), for the
    9B leaves.
- **No same-day control, but a drift probe.** In round 1, before any
  message, every 27B agent sees exactly the prompt of its own star. Rule 1
  asks that at least 80% of the 27B agents' round-1 calls before the talk
  intend to cooperate (its own star's forecast cell: 19 of 20). If fewer do,
  a same-day star of the 27B alone (5 runs) is run before anything else is
  read, and rules 2 and 3 read against it.
- **Two smoke runs first,** one of 2 rounds per star, into
  `pharos_runs/smoke_hetero_9b_dose/runs`. Each must pass the five checks of
  the earlier mixed stars:
  - every call of a 27B agent is answered by the 27B, and every call of a 9B
    leaf by the 9B, as the server reports;
  - no `<think>` block. If one shows, that smoke run is made once more; if
    the second shows one too, the runs wait for the author's decision;
  - every forecast call parses;
  - the round-1 message prompt has 464 tokens for every agent;
  - `verify_prompts.py` finds nothing.

  They also measure the server's speed (see "Limits").
- **Placement.** `pharos_runs/tok4096/hetero_9b_dose/runs/` holds two trees:
  - `Qwen3.8-27B-FP8_a3-Qwen3.5-9B`, star 1;
  - `Qwen3.8-27B-FP8_a23-Qwen3.5-9B`, star 2.

  The campaign zips land in `tok4096/hetero_9b_dose/`:
  `Qwen3.8-27B-FP8_star_sessionPROBE_pd_a3-Qwen3.5-9B.zip` and
  `Qwen3.8-27B-FP8_star_sessionPROBE_pd_a23-Qwen3.5-9B.zip`. The smoke runs'
  trees have the same names under `smoke_hetero_9b_dose/runs`, and their
  zips end in `_runs01-01`. A dry run of `campaign.py` gave these names, and
  every path was free when this was written.
- **The code.** `campaign.py` runs both stars as it is: `--agent-model` may
  be repeated, one agent each. `hetero_report.py` reads only stars whose hub
  is the other model, so a new report, `dose_report.py`, reads this plan's
  rules. It takes `hetero_report.py`'s loading, rows, hand labels and sheets,
  and adds the three roles: the hub, the 27B leaves, the 9B leaves. A
  fixture checks it before any run (see "Seen before writing").

## References

By role. Promises and broken promises are the hand's reading where it was
read, and the detector's elsewhere. The payoff is per neighbour and per
round.

| star | runs | hub cooperation | 27B leaves | 9B leaves | hub payoff | hub broken / promises |
|---|---|---|---|---|---|---|
| the 27B alone: grid baseline + forecast cell (11-10) | 10 | 1.00 | 1.00 (479/480) | | 3.99 | 0/160 |
| the 27B hub, three 9B leaves (11-12) | 5 | 0.05 | | 0.02 | 2.01 | 17/19 |
| the 9B alone (11-12) | 5 | 0.01 (a 9B hub) | | 0.04 | 2.13 | 21/21 |
| the 27B hub, three 122B leaves (11-12) | 5 | 0.97 | | | 3.73 | 2/77 |

- **Runs.** In the 27B's star every run's hub is at 1.00. Beside three 9B
  leaves the hub's run means are 0.12, 0.00, 0.12, 0.00 and 0.00.
- **Round 1:**
  - in the 27B's forecast cell, before the talk, its hub intends to
    cooperate in 5 of 5 calls (forecast 60.0) and its leaves in 14 of 15
    (58.7). All 20 cooperate;
  - beside three 9B leaves, the hub intends to cooperate before the talk in
    5 of 5 calls (60.0), after it in 1 of 5 (25.3), and cooperates in 1 of
    5: the run where its belief after the talk was 63.3. In the other four
    it was 5-30;
  - the 9B leaves intend to defect before the talk in all 30 calls of the
    two 11-12 stars.
- **The 27B's forecasts:** after a neighbour's promise, 95.6 (its forecast
  cell); as the hub beside three 9B leaves, 3.9 for a leaf that announced
  defection (196 forecasts), 11.2 in round 1.
- **Its lies beside three 9B leaves** (the hand's reading): 17 broken
  promises, 12 of them planned defence, 4 decided after the talk expecting
  defection, 1 planned exploitation. It promised in 19 of its 80 messages,
  and announced defection in 55.
- **The fourth mixed star, the hub after its leaves' defections.** After a
  round in which no leaf defected, the hub cooperated in 59 of 59 rounds;
  after one, in 7 of 9, defecting twice at beliefs of 65.0 and 66.7 on payoff
  sums; after two, in 7 of 7. Those two leaves had promised, so its forecasts
  of them stayed at 20-90 and its belief at 57-92.
- **The first mixed star, the 27B leaves after the 122B hub's defection.** In
  run 4 (round 5) all three defected in the next round. In run 5 (round 1)
  two of three did, and all four cooperated in round 3.
- **The edges.** In the 27B's star, 479 of 480 hub-leaf edge-rounds are both
  cooperate. Beside three 9B leaves, 225 of 240 are both defect, and in 11 a
  leaf defects on a cooperating hub.
- **Round-1 message prompt tokens:** 464 for every agent, on both models'
  stars.

## Definitions

Those of `docs/hetero_star_plan.md` and `docs/hetero_star_27b_9b_plan.md`,
with three roles: the hub (agent 0, the 27B), the 27B leaves and the 9B
leaves.
- **The hub's belief:** the mean of its three forecasts after the messages,
  one per leaf.
- **The hub-27B and hub-9B edges:** the edge-rounds between the hub and a
  leaf of each model.
- **The kinds of lie:** as before. A broken promise is planned exploitation
  when the intention before the talk was to defect and the belief is 50 or
  more, and planned defence when the belief is below 50. With an intention
  to cooperate before the talk, it is decided after the talk, expecting
  cooperation (50 or more) or defection (below 50).

## Hand checks

Those of `docs/hetero_star_plan.md`: blind, with the same seeds, over the two
stars' runs together.
- **Promises:**
  - every message of a defecting sender that the detector reads as a
    promise, and a random 100 of those it does not (seed 7; all of them if
    fewer);
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

  The 9B inverts many of its forecasts: in the reading of the second mixed
  star and its control, 45 of the 57 flagged calls, and 2 of the random 100.
  The calls found inverted leave rules 5 and 6, which are given both with
  them and without them.

## Reading rules

Every reading is exploratory: one composition per star, one cell, five runs.

1. **Routing, compliance and the untouched game, read first, for both
   stars.** If rule 1 fails, nothing else is read.
   - **Routing:** every call of agent 0 and of a 27B leaf is answered by
     Qwen/Qwen3.8-27B-FP8, and every call of a 9B leaf by Qwen/Qwen3.5-9B, as
     the server reports.
   - **Forecasts:** at least 90% of forecast calls are valid, before and
     after, for each role in each star.
   - **Inversion:** at most 5 calls of the random 100 are inverted.
   - **`verify_prompts.py`** finds nothing, or every hit is in an agent's own
     words.
   - **Tokens:** the round-1 message prompt tokens equal the references, role
     by role: 464.
   - **The drift probe:** at least 80% of the 27B agents' round-1 calls
     before the talk intend to cooperate, both stars together (25 calls).
     Below that, the same-day 27B star comes first (see "Design").
2. **How many 9B leaves does the hub take?** The hub's cooperation in each
   star:
   - 0.90 or more: "the hub holds", as in its own star (1.00);
   - 0.25 or less: "the hub falls", as beside three 9B leaves (0.05);
   - in between: "partly".
   - **The threshold** is the fewest 9B leaves at which the hub falls,
     counting the second mixed star as three. It is "a step" if the hub holds
     at every smaller number, and "graded" otherwise.
   - Reported beside it: run means; the hub's belief, as a mean and as the
     share of its decisions at 50 or more.
3. **Does the defection reach the 27B leaves?** The 27B leaves' cooperation
   in each star, against their own star (479 of 480):
   - a drop of 0.20 or more: "the defection reaches the 27B leaves";
   - a drop below 0.10: "the 27B leaves hold";
   - in between: "partly".
   - Reported beside it: the share of hub-27B edges where both cooperate; the
     27B leaves' forecast of the hub; run means.
4. **Does announced defection pay?** On the hub-9B edges, the 9B leaf's
   payoff minus the hub's, per edge-round:
   - +0.5 or more: "the 9B leaves gain at the hub's expense";
   - -0.5 or less: "the hub gains at the 9B leaves' expense";
   - in between: "even".
   - Reported beside it: the four kinds of hub-9B edge-round; each role's
     payoff per neighbour; the 9B leaves' cooperation against the 9B's own
     star and beside a 27B hub with three of them.
5. **The hub's lies, and whether the 27B leaves believe them.** The hub's
   broken promises that have a valid intention before the talk and a belief,
   in each star and in both together. Each is read only with at least 10;
   otherwise "too few to read".
   - The share of planned exploitation:
     - 0.50 or more: "mostly planned exploitation";
     - below 0.25: "rarely";
     - in between: "partly".
   - **Whether the 27B leaves believe them:** of the 27B leaves' forecasts of
     the hub in the rounds of its broken promises, the share at 50 or more.
     At least 0.50: "the 27B leaves believe them"; below 0.50: "they do not".
   - Reported beside it:
     - P and the four kinds;
     - the 27B leaves' forecast of the hub after its kept and broken
       promises, and the AUC;
     - the round-1 shift of a 27B leaf's forecast of the hub after the hub's
       promise;
     - the hub beside three 9B leaves (by the detector).
6. **Belief and action, by role.** Cooperation at a belief of 50 or more,
   against below 50, for each role in each star, each side with at least 20
   decisions; otherwise "too few to read".
   - A difference of 0.50 or more: "its actions follow its beliefs".
   - Below 0.20: "its actions ignore its beliefs".
   - In between: "partly".
7. **Descriptive, not rules:**
   - round 1 before and after the talk, by role;
   - the first defection of a 27B agent in each run, and the hub's reasoning
     when it first defects: a payoff sum, retaliation, or exploitation;
   - **tolerated or punished:** the hub's action in the round after a 9B leaf
     defected while the 27B leaves cooperated;
   - the hub-27B edges by blocks of four rounds, and the runs whose 27B pair
     breaks and comes back;
   - **does lying pay?** By role, the sender's payoff per neighbour when it
     broke a promise, kept one, or defected without one, and its neighbours'
     cooperation in that round and the next;
   - the 27B hub with 0, 1, 2 and 3 9B leaves: the curve, beside the 27B hub
     with three 122B leaves.

**How the numbers are computed.**
- `dose_report.py` prints rules 1-6 and the descriptive lines, reads the
  hand labels with `--hand`, and writes the blind sheets with `--dump`.
- `verify_prompts.py` and `audit_corpus.py` run on both trees.
- The scripts, sheets, keys, labels and outputs are kept beside the runs, in
  `pharos_runs/tok4096/hetero_9b_dose/analysis/`.

## Prediction, stated before the run

- **Rule 1** passes for both stars, the drift probe included. The risk is the
  9B's inversions, which could put more than 5 in the random 100 (2 in the
  second mixed star).
- **Rule 2: star 1 "partly", star 2 "the hub falls"; the threshold is two 9B
  leaves, graded.**
  - With one 9B leaf the hub's belief should stay above 50, and the 27B does
    what it expects. But in the fourth mixed star, after one leaf had
    defected while two cooperated, it defected in 2 of 9 rounds, on payoff
    sums. Here a 9B leaf defects in almost every round, so the hub meets that
    sum in almost every round: a hub near 0.75-0.85.
  - With two, its belief falls to about 34, and below 50 the 27B cooperates
    0.08.
  - The risks: star 1 "holds" if the 27B keeps to its belief; star 1 "falls"
    if the hub's defections and the 27B leaves' answers feed each other until
    the run collapses.
- **Rule 3: star 1 "partly", star 2 "the defection reaches the 27B leaves".**
  - In star 1 each defection of the hub breaks its promise to the 27B
    leaves. They answer it in the next round, as after the 122B hub's
    defections, and come back.
  - In star 2 the hub falls, and its one 27B leaf with it.
- **Rule 4: star 1 "the 9B leaves gain at the hub's expense", star 2
  "even".** A hub that cooperates with its 27B leaves cooperates with the 9B
  leaf too, while the 9B defects; a fallen hub defects on all three.
- **Rule 5:**
  - star 1: readable, "rarely planned exploitation", and "the 27B leaves
    believe them". The hub promises in every round, as in its own star, and
    decides its defections at the action call, as both of its lies in the
    fourth mixed star;
  - star 2: readable, "rarely planned exploitation", and "they do not". The
    risk is "too few to read": beside three 9B leaves, the fallen hub
    promised in only 19 of its 80 messages;
  - both together: readable, "rarely planned exploitation", and "the 27B
    leaves believe them", since star 1, with two 27B leaves, gives most of
    the forecasts.
- **Rule 6:** the 27B's actions (the hub's and the 27B leaves') follow its
  beliefs, or a side is too few to read; the 9B leaves' actions ignore their
  beliefs, or a side is too few to read.

## Seen before writing

- Every number of the references above, and of the two models' other cells.
- The results of the first four mixed stars. The fourth was read on 11-12,
  before this was written.
- The fifth and sixth mixed stars (a 9B hub with 27B or 122B leaves) and their
  control had run, from 11-12 19:15 to 11-13 00:36. None of their runs was
  read.
- The 122B's competitive cell: its smoke run had passed, and its runs had not
  started.
- The test of the code: a fixture, the fourth mixed star's two cells (its
  mixed star and its control) relabelled as the two stars, with agent 3 (star
  1) and agents 2 and 3 (star 2) marked as the 9B.
  - `dose_report.py`'s rules 1-6, its drift probe and its tolerated count
    agree with counts made apart. It passes routing (2560 of 2560 calls) and
    tokens. Its drift probe reads 5 of 25 (the real 27B hub's 5 of 5, none of
    the 20 relabelled 122B agents), and fails, as it should.
  - The fixture's sheets equal those of the fourth star's reading, message
    for message. With that reading's labels, the report reads the hand as
    `hetero_report.py` did.
  - It refuses a tree whose hub is the other model.

No run of this experiment existed when this was written.

**Between the writing and the commit (11-13 to 11-18).** Three things were
added at the commit: the sentence on the two dates at the top, this
paragraph, and one line under "Limits" (speed).
- The 122B's competitive cell ran on 11-13, from 01:42 to 02:42. None of its
  runs was read.
- The fifth and sixth mixed stars and their control were still unread.
- The eight-agent grid of the three lab-server models
  (`docs/grid_n8_plan.md`) ran from 11-14 to 11-18. Its rules 1 to 6 were
  read; its talk table was not yet made. Its cells are those of the plain
  grid, with no forecasts and no mixed network.
- Every path under "Placement" was still free. The patch applied to the
  current `main` without a change to `dose_report.py`, and both tests gave
  their earlier output.

No run of this experiment existed at the commit.

## Limits fixed in advance

- **Scope.** One composition per star, one cell, five runs. The hub is one
  agent per star: 80 decisions. Star 2 has a single 27B leaf, so its rule 3
  reads 80 decisions.
- **Two changes at once.** The 27B and the 9B differ in generation, size and
  precision. "Defects and says so" describes what the 9B did in its own star,
  not what it is.
- **One action for three edges.** The hub cannot answer a 9B leaf without
  answering its 27B leaves. This is the star's design, and the reason for
  rule 3.
- **No same-day control.** The 27B's own star is from 11-10, after the
  update. The drift probe covers its round 1 only.
- **Stated beliefs.** The forecasts come from separate calls, and nothing
  rewards their accuracy. The 9B inverts many of its own.
- **The detector** is not validated on these models. The hand check covers
  the messages of defecting senders, in part by sample.
- **Speed.** On 11-12 the 27B answered in about 15-25 s per call (the runs
  of the mixed star with a 9B hub and 27B leaves took 53-85 minutes),
  against 1.5-2.5 s on 11-10. Star 1 has 192 27B calls per run, star 2 has
  128. At 11-12's speed a lane takes about 3-7 hours; at 11-10's, under an
  hour. Speed enters no rule. (Added at the commit: in the eight-agent grid,
  11-14 to 11-18, the 27B answered in 1.6-3.1 s per call and the 9B in
  1.3-3.3 s.)
- **Server updates:**
  - if one stops the runs, a new smoke run comes before any further run;
  - a lane cut short keeps its runs if it has at least 4 of 5; otherwise it
    is run again whole;
  - the write-up names every run made after an update.
- **Other compositions** (a clique, a line, 122B leaves in place of the 9B)
  are not part of this plan.

## Reproduce

From `cheaptalk_bench`. First the two smoke runs, then the two lanes side by
side:

```
python campaign.py --provider pharos --model Qwen/Qwen3.8-27B-FP8 --agent-model 3=Qwen/Qwen3.5-9B --session PROBE --topology star --games pd --n-runs 1 --n-rounds 2 --max-new-tokens 4096 --out-root ..\pharos_runs\smoke_hetero_9b_dose\runs --zip-mirror=
python campaign.py --provider pharos --model Qwen/Qwen3.8-27B-FP8 --agent-model 2=Qwen/Qwen3.5-9B --agent-model 3=Qwen/Qwen3.5-9B --session PROBE --topology star --games pd --n-runs 1 --n-rounds 2 --max-new-tokens 4096 --out-root ..\pharos_runs\smoke_hetero_9b_dose\runs --zip-mirror=
python campaign.py --provider pharos --model Qwen/Qwen3.8-27B-FP8 --agent-model 3=Qwen/Qwen3.5-9B --session PROBE --topology star --games pd --n-runs 5 --n-rounds 16 --max-new-tokens 4096 --out-root ..\pharos_runs\tok4096\hetero_9b_dose\runs --zip-mirror=
python campaign.py --provider pharos --model Qwen/Qwen3.8-27B-FP8 --agent-model 2=Qwen/Qwen3.5-9B --agent-model 3=Qwen/Qwen3.5-9B --session PROBE --topology star --games pd --n-runs 5 --n-rounds 16 --max-new-tokens 4096 --out-root ..\pharos_runs\tok4096\hetero_9b_dose\runs --zip-mirror=
```

Then the checks, the sheets and the report:

```
python verify_prompts.py ..\pharos_runs\tok4096\hetero_9b_dose\runs\Qwen3.8-27B-FP8_a3-Qwen3.5-9B ..\pharos_runs\tok4096\hetero_9b_dose\runs\Qwen3.8-27B-FP8_a23-Qwen3.5-9B
python audit_corpus.py ..\pharos_runs\tok4096\hetero_9b_dose\runs\Qwen3.8-27B-FP8_a3-Qwen3.5-9B ..\pharos_runs\tok4096\hetero_9b_dose\runs\Qwen3.8-27B-FP8_a23-Qwen3.5-9B
python dose_report.py --dose ..\pharos_runs\tok4096\hetero_9b_dose\runs --dump ..\pharos_runs\tok4096\hetero_9b_dose\analysis
python dose_report.py --dose ..\pharos_runs\tok4096\hetero_9b_dose\runs --home ..\pharos_runs\tok4096\grid\Qwen3.8-27B-FP8 ..\pharos_runs\tok4096\probe_27b\Qwen3.8-27B-FP8 --three ..\pharos_runs\tok4096\hetero_27b_9b\runs\Qwen3.5-9B_a0-Qwen3.8-27B-FP8 --nine ..\pharos_runs\tok4096\hetero_27b_9b\runs\Qwen3.5-9B --hand ..\pharos_runs\tok4096\hetero_9b_dose\analysis
```

If the drift probe fails, the same-day star of the 27B alone, read with
`--home` pointed at its tree (`hetero_9b_dose\runs\Qwen3.8-27B-FP8`):

```
python campaign.py --provider pharos --model Qwen/Qwen3.8-27B-FP8 --session PROBE --topology star --games pd --n-runs 5 --n-rounds 16 --max-new-tokens 4096 --out-root ..\pharos_runs\tok4096\hetero_9b_dose\runs --zip-mirror=
```
