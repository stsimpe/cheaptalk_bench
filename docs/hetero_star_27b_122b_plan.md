# A fourth mixed star: Qwen3.8-27B in the hub, Qwen3.5-122B in the leaves

This is the plan for the fourth exploratory experiment with two models in one
network, on the lab server. It was written on 2026-11-12 at 15:45, before any
run of it, and its rules and prediction are fixed here. Its two lanes ran
from 16:40 to 18:16, before it was committed, and without the smoke run it
asks for: rule 1 reads the smoke run's five checks on the runs themselves. It
was committed after they had ended, before any of their runs was read. Its
text is as written at 15:45, with these sentences added. It is the first
mixed star (`docs/hetero_star_plan.md`) with the two models swapped, and takes
its definitions, hand checks and code. The second and third mixed stars
(`docs/hetero_star_27b_9b_plan.md`, `docs/hetero_star_122b_9b_plan.md`) are
read beside it.

## Question

In the first mixed star the 122B, which lies, sat in the hub, and three 27B
agents, which keep their word, sat in its leaves. The leaves kept it honest
(3 broken promises in 80 decisions) and cooperating (0.95). This plan swaps
the roles: three 122B agents around a 27B hub.
- **Qwen/Qwen3.8-27B-FP8, the hub:**
  - it cooperates in every seat of its own star (1.00), and keeps its word:
    no broken promise in its 160 hub decisions;
  - it believes promises: its forecast of a neighbour after a promise is
    95.9, a round-1 shift of +29.3;
  - it does what it expects: it cooperates 0.99 at a belief of 50 or more
    and 0.08 below (its forecast cells);
  - as the leaves of the first mixed star, it believed the 122B hub's two
    unwarned lies (85-95), defected in the next round, and then returned to
    cooperation;
  - as the hub of the second mixed star, beside 9B leaves that announced
    defection, it defected from round 1 and broke 17 promises.
- **Qwen/Qwen3.5-122B-A10B, the leaves:**
  - in its own star after the server's update (11-11 and 11-12, 10 runs),
    its leaves cooperate 0.60, and its hub breaks 39 of its 146 promises;
  - its leaves act on their beliefs: 0.91 at a belief of 50 or more, 0.08
    below;
  - they lie too. Before their hub's first defection they defect in 6% of
    their decisions, and every such defection breaks a promise;
  - in round 1 they intend to defect before the talk (29 of 30 calls), and
    after their hub's promise 25 of 30 intend to cooperate. 7 of 30 defect,
    and all 7 had promised.

The second mixed star asked what a neighbourhood that defects, and says so,
does to the 27B. This one asks what a neighbourhood that promises, and
sometimes lies, does to it.
- **The hub.** A hub plays one action for all three of its edges. When one
  leaf lies, does the 27B tolerate it and keep cooperating with all three,
  or punish it by defecting on all three? Does cooperation come back?
- **The leaves.** Does a hub that keeps its word keep the 122B leaves
  cooperating, as the 27B leaves kept the 122B hub in the first mixed star?
- **The lies.** Do the 122B leaves exploit a hub that believes them? Does
  the 27B believe their lies, and does lying pay against it?

The agents are never told which model a neighbour is: the prompts are those
of a homogeneous star. Any difference is made by play and talk alone.

## Design

- **The mixed star:** four agents. Agent 0, the hub with three edges, is
  served Qwen/Qwen3.8-27B-FP8; agents 1-3, the leaves,
  Qwen/Qwen3.5-122B-A10B.
- **The cell:** `forecast_probe` (session `PROBE`), as in the first three
  mixed stars.
  - It is the baseline with cheap talk: Prisoner's Dilemma, 16 rounds with a
    hidden horizon, memory 10, temperature 0.7, cap 4096, thinking off.
  - Each agent also gives two private forecasts per round, before and after
    the messages. The game's prompts are the baseline's, byte for byte.
- **5 runs.**
- **A same-day control: the 122B alone on the star,** the same cell, 5 runs,
  in a second lane beside the first. It is the leaves' model, as the 9B was
  in the second mixed star. Its stars of 11-11 and 11-12 are reported beside
  it.
- **The hub's reference** is the 27B's own star: its grid and its forecast
  cell (11-10, 160 hub decisions, both after the update), as in the second
  mixed star.
- **A smoke run first:** one run of 2 rounds of the mixed star, into
  `pharos_runs/smoke_hetero_27b_122b/runs`. It must pass the first plan's
  five checks before the runs:
  - every call of agent 0 is answered by the 27B, and every call of a leaf by
    the 122B, as the server reports;
  - no `<think>` block, from either model. The 122B writes about 5 in 1,000
    calls in its forecast cells. If the smoke run shows one, it is made once
    more; if the second shows one too, the runs wait for the author's
    decision;
  - every forecast call parses;
  - the round-1 message prompt has 464 tokens for every agent, as on both
    models' stars;
  - `verify_prompts.py` finds nothing.
- **Placement.** `pharos_runs/tok4096/hetero_27b_122b/runs/` holds two trees:
  - `Qwen3.5-122B-A10B_a0-Qwen3.8-27B-FP8`, the mixed star;
  - `Qwen3.5-122B-A10B`, the control.

  The two campaign zips land in `tok4096/hetero_27b_122b/`. The control's,
  `Qwen3.5-122B-A10B_star_sessionPROBE_pd.zip`, has the same name as the
  122B's forecast-cell zips in `tok4096/` (11-04), `tok4096/hetero/` (11-11)
  and `tok4096/hetero_122b_9b/` (11-12).
- **The code:** none. `hetero_report.py` (as generalised in `74406fc`) reads
  this star as it is:
  - the control is the leaves' model, so rule 2 reads the hub against its
    own star (`--hub-home`), and rule 3 the leaves against the control,
    either way;
  - `--lies leaves` reads rule 5 for the leaves' broken promises, with the
    hub's forecast of each leaf after that leaf's promise.

  A fixture checks this before any run (see "Seen before writing").

## References

The two models' own stars, by role (hub = agent 0, leaves = agents 1-3).
Promises and broken promises are the detector's; announced defections follow
the 9B plan's pattern. The payoff is per neighbour and per round.

| model, cell | runs | hub cooperation | leaves cooperation | hub payoff | leaves payoff | hub broken | leaves broken | leaves' messages announcing defection |
|---|---|---|---|---|---|---|---|---|
| 27B, grid baseline (11-10) | 5 | 1.00 | 1.00 | 3.99 | 4.01 | 0/80 | 1/238 | 1/240 |
| 27B, grid no_comm (11-10) | 5 | 0.37 | 0.38 | 2.90 | 2.76 | | | |
| 27B, forecast cell (11-10) | 5 | 1.00 | 1.00 | 4.00 | 4.00 | 0/80 | 0/237 | 0/240 |
| 122B, grid baseline (10-30) | 5 | 0.60 | 0.50 | 2.95 | 3.47 | 25/68 | 45/162 | 72/240 |
| 122B, grid no_comm (10-30) | 5 | 0.01 | 0.01 | 2.02 | 2.04 | | | |
| 122B, forecast cell (11-04) | 5 | 0.66 | 0.56 | 3.11 | 3.63 | 21/73 | 49/178 | 56/240 |
| **122B, forecast cell (11-11, after the update)** | 5 | 0.71 | **0.61** | 3.20 | 3.72 | 20/74 | 40/183 | 56/240 |
| **122B, forecast cell (11-12, after the update)** | 5 | 0.68 | **0.60** | 3.19 | 3.59 | 19/72 | 47/185 | 53/240 |
| the first mixed star: 122B hub, 27B leaves (11-11) | 5 | 0.95 | 0.95 | 3.95 | 3.92 | 2/77 | 5/233 | 7/240 |
| the second mixed star: 27B hub, 9B leaves (11-12) | 5 | 0.05 | 0.02 | 2.01 | 2.18 | 19/21 | 33/36 | 196/240 |

- **Runs.** In the 27B's star every run's hub is at 1.00. In the 122B's two
  stars after the update, the leaves' run means are 0.19, 0.88, 0.77, 0.98,
  0.23, 0.85, 1.00, 0.77, 0.12 and 0.23.
- **Round 1, before the talk** (forecast cells):
  - the 27B's hub intends to cooperate in 5 of 5 calls (forecast 60.0);
  - the 122B's leaves intend to defect in 29 of 30 calls after the update
    (forecast 24.7), and in 15 of 15 on 11-04.
- **Round 1, the 122B's leaves** (11-04, 11-11, 11-12):
  - 4, 4 and 3 of 15 defect, each time after their hub's promise;
  - 10 of these 11 had promised, and every one intended to defect before
    the talk;
  - 8 of the 11 gave the hub 50 or more after the messages.
- **Before the hub's first defection.** The 122B hubs defect early, in
  round 1-3 in most runs. Before that, in the three 122B forecast cells, the
  leaves defected in 12 of 195 decisions (6%). Every one broke a promise. 11
  were planned before the talk, and 8 came at a belief of 50 or more. In
  the first mixed star, the 27B leaves defected in 1 of 153.
- **Belief and action** (forecast cells), cooperation at a belief of 50 or
  more against below 50:
  - the 27B: 1.00, and never below 50 (its two forecast cells: 0.99 against
    0.08);
  - the 122B's leaves after the update: 0.91 (303 decisions) against 0.08
    (176). Its hub: 0.89 against 0.24.
- **Forecasts of a neighbour** (forecast cells):
  - the 27B after a promise: 95.9, a round-1 shift of +29.3. As the leaves
    of the first mixed star: 92.7;
  - the 122B's leaves after their hub's promise, after the update: 66.8, a
    round-1 shift of +55.5.
- **The kind of lie** of the 122B's leaves after the update (both stars, by
  the detector): of 86 broken promises with an intention and a belief, 17
  are planned exploitation (0.20), 66 planned defence, 1 decided after
  expecting cooperation and 2 expecting defection.
- **The edges.** In the 122B's two stars after the update, of 480 hub-leaf
  edge-rounds, a leaf defects on a cooperating hub in 84 and the hub on a
  cooperating leaf in 40; 249 are both cooperate. In the 27B's forecast
  cell, 240 of 240 are both cooperate.
- **Round-1 message prompt tokens:** 464 for every agent, on both stars.

## Definitions

Those of `docs/hetero_star_plan.md` and `docs/hetero_star_27b_9b_plan.md`,
by role.
- **The hub's forecast of a leaf:** the hub's forecast call gives one number
  per leaf. Rule 5 reads the number for a leaf after that leaf's message.
- **A leaf's lie is tolerated** when the hub cooperates in the next round,
  and **punished** when it defects.

## Hand checks

Those of `docs/hetero_star_plan.md`: blind, with the same seeds, over the
mixed star's and the control's runs together.
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

  In the first mixed star none of the 112 calls read was inverted. The calls
  found inverted leave rules 5 and 6, which are given both with them and
  without them.

## Reading rules

Every reading is exploratory: one composition, one cell, five runs.

1. **Routing, compliance and the untouched game, read first, for both
   cells.** If rule 1 fails, nothing else is read.
   - **Routing:** in the mixed star, every one of the hub's calls is
     answered by Qwen/Qwen3.8-27B-FP8, and every one of the leaves' by
     Qwen/Qwen3.5-122B-A10B, as the server reports.
   - **Forecasts:** at least 90% of forecast calls are valid, before and
     after, for each role in each cell.
   - **Inversion:** at most 5 calls of the random 100 are inverted.
   - **`verify_prompts.py`** finds nothing, or every hit is in an agent's own
     words.
   - **Tokens:** the round-1 message prompt tokens equal the references, role
     by role: 464.
2. **Does the neighbourhood change the hub?** The hub's cooperation in the
   mixed star minus the 27B's hub in its own star (its grid and its forecast
   cell, 160 decisions).
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
   - Reported beside it: run means; the 122B's stars of 11-11 and 11-12,
     and all three of its stars after the update pooled; its earlier stars.
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
   - **Whether the hub believes them:** the share of the leaves' broken
     promises after which the hub's forecast of that leaf is 50 or more.
     Read with the same 10 or more: at least 0.50, "the hub believes them";
     below 0.50, "it does not".
   - Reported beside it:
     - P and the four kinds, in the mixed star and the control;
     - the hub's forecast of a leaf after that leaf's kept and broken
       promises, and the AUC;
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
   - **tolerated or punished:** after each broken promise of a leaf, the
     hub's action in the next round, and whether all four agents cooperate
     again later in the run;
   - **does lying pay?** By role, the sender's payoff per neighbour when it
     broke a promise, kept one, or defected without one, and its neighbours'
     cooperation in that round and the next;
   - the hub's own broken promises (`--lies hub`): does the 27B start to lie
     here too?
   - the 27B hub in its three neighbourhoods (27B, 9B and 122B leaves), and
     the 122B in the hub and in the leaves.

**How the numbers are computed.**
- `hetero_report.py` with `--lies leaves` prints rules 1-6 and the
  descriptive splits, and reads the hand labels with `--hand`. With `--lies
  hub` it gives the hub's own broken promises.
- The tolerated-or-punished split, the return of cooperation, and the
  122B's other stars beside rule 3 are counted apart from the report, by a
  read-only script kept with the outputs.
- `verify_prompts.py` and `audit_corpus.py` run on both trees.
- The scripts, sheets, keys, labels and outputs are kept beside the runs, in
  `pharos_runs/tok4096/hetero_27b_122b/analysis/`.

## Prediction, stated before the run

- **Rule 1** passes for both cells. The risk is the 122B's `<think>` blocks
  (about 5 in 1,000 calls), which can leave a message empty.
- **The control** plays as the 122B's stars after the update: its leaves
  within 0.20 of 0.60, and its hub within 0.20 of 0.69.
- **Rule 2: "the hub plays as in its own star"** (within 0.10 of 1.00).
  - The 122B's leaves promise in round 1 and mostly keep it. A lying leaf
    lowers one of the three forecasts that make the 27B's belief, and the
    27B does what it expects.
  - The risk: the 27B punishes a lying leaf by defecting on all three. Its
    leaves act on their beliefs and answer in kind, so a run can collapse as
    in the 122B's own star. The reading would then be "partly" or "lower".
- **Rule 3: "the hub raises the leaves' cooperation"** (+0.20 or more).
  - In its own star the 122B's hub breaks 39 promises in 160 decisions.
    The 27B hub keeps its word (0 of 160), so the leaves' beliefs about it
    should stay high, and they act on their beliefs (0.91 against 0.08).
  - It is the first mixed star seen from the other side, where the 27B
    raised the 122B hub's cooperation by 23.7 points.
  - The risk is the control itself: the 122B's star swings by run (leaves
    0.12-1.00). If the control's leaves cooperate 0.80 or more, a rise of
    0.20 is out of reach.
- **Rule 4: "even".**
  - A leaf that defects on a hub that cooperates gains 2 points, and the hub
    loses 3. If the other edge-rounds are mutual cooperation, "the leaves
    gain" needs such edge-rounds in 10% or more of them. Before the hub's
    first defection, the 122B's leaves defect in 6% of their decisions.
  - The risk: the leaves exploit a hub that tolerates them, and the reading
    is "the leaves gain at the hub's expense".
- **Rule 5:** readable, "mostly planned exploitation", and "the hub
  believes them".
  - With a hub that keeps its word, a leaf's belief stays high, so a lie
    planned before the talk is planned exploitation.
  - In round 1 of its own stars, 8 of the 11 leaves that defected gave the
    hub 50 or more. Beside the 122B hub, 18 of the 9B leaves' 38 lies were
    planned exploitation.
  - The 27B believes promises (95.9 after one). In round 1 its forecast of a
    leaf moves +20 or more after that leaf's promise (+29.3 at home).
  - The risk: fewer than 10 lies, "too few to read". The 27B leaves broke 6
    in the first mixed star.
- **Rule 6:** the hub's actions follow its beliefs, or its side below 50 is
  too few to read. The leaves' actions follow their beliefs, or their side
  below 50 is too few to read.

## Seen before writing

- Every number of the two models' stars above, and of their other cells.
- The results of the first three mixed stars.
- The test of the code: a fixture, the 122B's star of 11-12 relabelled as a
  mixed star with the 27B in the hub, read by `hetero_report.py` against the
  122B's star of 11-11 as the control.
  - It reads the control as the leaves' model, rules 2 and 3 as a count made
    apart gives them, and passes routing and tokens.
  - With `--lies leaves`, the leaves' kinds of lie and the hub's forecasts
    of each leaf agree with a count made apart; so do the hub's kinds with
    `--lies hub`.
  - `--dump` takes both cells into the sheets.

No run of this experiment existed when this was written.

## Limits fixed in advance

- **Scope.** One composition, one cell, five runs. The hub is one agent per
  run: 80 decisions.
- **Two changes at once.** The two models differ in generation, size,
  architecture and precision. "Liar" and "truster" describe what they did in
  their own stars, not what they are.
- **One action for three edges.** The hub cannot punish one leaf without
  defecting on the other two. This is the star's design, not a confound; it
  is why the hub's answer to a lie is read on its own (rule 7).
- **Stated beliefs.** The forecasts come from separate calls, and nothing
  rewards their accuracy.
- **The detector** is not validated on these models; the hand check covers the
  messages of defecting senders, in part by sample.
- **The served model is what the server reports.** The smoke run checks it
  before any run.
- **Server updates:**
  - if one stops the runs, a new smoke run comes before any further run;
  - a lane cut short keeps its runs if it has at least 4 of 5; otherwise it
    is run again whole;
  - the write-up names every run made after an update.
- **Other compositions** (a 9B hub with 27B or 122B leaves) are not part of
  this plan.

## Reproduce

From `cheaptalk_bench`. First the smoke run, then the two lanes side by
side:

```
python campaign.py --provider pharos --model Qwen/Qwen3.5-122B-A10B --agent-model 0=Qwen/Qwen3.8-27B-FP8 --session PROBE --topology star --games pd --n-runs 1 --n-rounds 2 --max-new-tokens 4096 --out-root ..\pharos_runs\smoke_hetero_27b_122b\runs --zip-mirror=
python campaign.py --provider pharos --model Qwen/Qwen3.5-122B-A10B --agent-model 0=Qwen/Qwen3.8-27B-FP8 --session PROBE --topology star --games pd --n-runs 5 --n-rounds 16 --max-new-tokens 4096 --out-root ..\pharos_runs\tok4096\hetero_27b_122b\runs --zip-mirror=
python campaign.py --provider pharos --model Qwen/Qwen3.5-122B-A10B --session PROBE --topology star --games pd --n-runs 5 --n-rounds 16 --max-new-tokens 4096 --out-root ..\pharos_runs\tok4096\hetero_27b_122b\runs --zip-mirror=
```

Then the checks, the sheets and the report:

```
python verify_prompts.py ..\pharos_runs\tok4096\hetero_27b_122b\runs\Qwen3.5-122B-A10B_a0-Qwen3.8-27B-FP8 ..\pharos_runs\tok4096\hetero_27b_122b\runs\Qwen3.5-122B-A10B
python audit_corpus.py ..\pharos_runs\tok4096\hetero_27b_122b\runs\Qwen3.5-122B-A10B_a0-Qwen3.8-27B-FP8 ..\pharos_runs\tok4096\hetero_27b_122b\runs\Qwen3.5-122B-A10B
python hetero_report.py --mixed ..\pharos_runs\tok4096\hetero_27b_122b\runs\Qwen3.5-122B-A10B_a0-Qwen3.8-27B-FP8 --control ..\pharos_runs\tok4096\hetero_27b_122b\runs\Qwen3.5-122B-A10B --dump ..\pharos_runs\tok4096\hetero_27b_122b\analysis
python hetero_report.py --mixed ..\pharos_runs\tok4096\hetero_27b_122b\runs\Qwen3.5-122B-A10B_a0-Qwen3.8-27B-FP8 --control ..\pharos_runs\tok4096\hetero_27b_122b\runs\Qwen3.5-122B-A10B --hub-home ..\pharos_runs\tok4096\grid\Qwen3.8-27B-FP8 ..\pharos_runs\tok4096\probe_27b\Qwen3.8-27B-FP8 --leaves-home ..\pharos_runs\tok4096\grid\Qwen3.5-122B-A10B ..\pharos_runs\tok4096\probe\Qwen3.5-122B-A10B --hand ..\pharos_runs\tok4096\hetero_27b_122b\analysis --lies leaves
```

**Timing.** The first mixed star (the same two models) ran at 1.69 s per
call with two lanes, and the 122B's star of 11-12 at 1.70. A run has 256
calls, so a lane of 5 runs should take 35-60 minutes. The smoke run takes
1-3 minutes.
