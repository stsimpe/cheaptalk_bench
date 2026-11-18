# Eight agents: the grid of the three lab-server models at twice the size

This is the plan for an exploratory follow-up: the grid of the three models on
the lab server (Qwen/Qwen3.5-122B-A10B, Qwen/Qwen3.8-27B-FP8, Qwen/Qwen3.5-9B),
run again with eight agents instead of four. It was written on 2026-11-14,
before any eight-agent run. The reading rules below decide what the results
are allowed to say. Committing this file before the first run fixes them. No
earlier cell, plan or rule is touched.

## Question

Every run so far has had four agents. In a network of four, degree and size
are tied:
- the star's leaves have degree 1 and its hub degree 3;
- the ring has degree 2;
- the clique has degree 3.

The thesis lists this as a limit: degree and network size are not separated.
With eight agents they come apart:
- **the star:** the leaves keep degree 1, and the hub has degree 7;
- **the ring:** degree 2, as with four;
- **the clique:** degree 7.

So the eight-agent grid asks four things:
- **Size at a fixed degree.** The ring at eight against the ring at four: the
  same two neighbours, in a network twice the size.
- **Degree at a fixed size.** The clique against the ring at eight: degree 7
  against 2. With four agents the same contrast was 3 against 2, and the ring
  and the clique could not be told apart.
- **The star.** With four agents the star is the outlier: its agents
  cooperate least. At eight, do they still, when the hub that each leaf
  depends on plays seven edges?
- **The hub of seven.** One action for seven edges: does the hub still
  cooperate as its leaves do?

What changes for the agents is only what the network gives them:
- the network paragraph names eight agents and the agent's own number of
  neighbours (7 for the hub and in the clique, 1 for a leaf, 2 on the ring);
- a hub and a clique agent read seven messages a round and see seven
  neighbours' actions in their history.

## Design

- **The grid of the three models, with `--n-agents 8`.**
  - Sessions A, B and C: the star with the original prompt; the ring and the
    clique with the corrected routing prompt (`--topology-aware-comm-prompt`).
  - Prisoner's Dilemma and Stag Hunt, 5 runs per cell: 420 runs per model,
    1,260 in all.
  - 16 rounds, hidden horizon, memory 10, T = 0.7, output cap 4096, thinking
    off. Nothing else changes.
- **Placement.** The runs go to `pharos_runs/tok4096/grid_n8/runs/`, three
  trees per model: `<model>_n8`, `<model>_cycle_n8_commfix` and
  `<model>_clique_n8_commfix`. The session zips land in `tok4096/grid_n8/`,
  for example `Qwen3.8-27B-FP8_star_sessionA_n8.zip` and
  `Qwen3.8-27B-FP8_cycle_sessionA_n8_commfix.zip`. A dry run of `campaign.py`
  gave these names, and the paths were free when this was written.
- **The drift control.** Rules 2 and 6 compare two periods: the four-agent
  grids ran on 10-30/31 (122B), 11-06/07 (9B) and 11-10 (27B), on both sides
  of the server's model update of 11-09, and the eight-agent runs come later.
  - Per model, two cells of the four-agent grid run again in the eight-agent
    period: the PD baseline on the ring with four agents, both arms
    (`no_comm` and `baseline_cheap_talk`), 5 runs each. That is 10 runs per
    model, 30 in all.
  - They go to `tok4096/grid_n8/drift/<model>_cycle_commfix`. The zip is
    `tok4096/grid_n8/<model>_cycle_sessionA_commfix_pd.zip`.
  - Each model's control runs in the same days as its lanes.
- **Smoke runs first,** per model, before its lanes. Each is session A's
  baseline, PD, eight agents, 1 run of 2 rounds per arm, one per topology, in
  `pharos_runs/smoke_grid_n8/runs`. Each must pass:
  - the config: eight agents, the model, cap 4096, T = 0.7, the topology, and
    the corrected routing prompt on the ring and the clique;
  - no `<think>` block, and every reply finished normally. If a block shows,
    that smoke run is made once more. If the second shows one too, the runs
    wait for the author's decision;
  - every action is valid;
  - the round-1 message prompt tokens of the `cheap_talk` run are the same for
    every model on each topology, checked again as each model's smoke runs
    come in;
  - `verify_prompts.py` finds nothing.
- **Order.** The order of models, lanes and sessions is free, and a lane may
  be spread over several days. Suggested: the 27B first (the fastest with four
  agents), then the 122B, then the 9B. A model is read once its 420 runs and
  its control are in. The pooled readings wait for all three.
- **Code.**
  - `campaign.py` runs the grid as it is: `--n-agents` exists. The contagion
    line used six agents.
  - `audit_corpus.py` gets `--n-agents N`. Its protocol check had four agents
    fixed, so it flags every eight-agent run as `n_agents=8`.
  - A new `size_report.py` reads the rules below.
- **The test of the code, before any run.** A fake model, kept outside the
  repo, drives the real engine, prompts and run records with replies drawn at
  random. It made the whole eight-agent grid for the three model ids, the
  drift control and the smoke runs. Nothing from it is a result.
  - `verify_prompts.py` rebuilt the 138,240 prompts of one model's 420 runs
    and found no problem.
  - `audit_corpus.py --n-agents 8` found no issue in the 1,260 runs. Without
    the option, it flags `n_agents=8` in every run.
  - `size_report.py` agreed with an independent count in all 33 of its
    contrasts, drift cells and markers.
  - On the real four-agent trees, `size_report.py` reproduces the references
    below, which were first counted from the tracker's `Pharos_Runs` sheet.

## Definitions

- **A cell's value** is the mean of its run means over valid decisions, as in
  `scale_report.py`. The 28 cells of a topology are the 14 grid cells in both
  games.
- **A contrast** compares two sets of cells one by one: a cell is higher or
  lower if it differs by at least 0.05, and tied otherwise. A two-sided exact
  sign test runs on the cells that are not tied.
  - Its verdict is "higher" or "lower" at p < 0.05, and "not detected"
    otherwise.
  - It is read per model, and pooled over the models that are read.
  - This is how Part I read topology (RQ2).
- **The star's value** is the mean over all eight agents, as with four agents
  over four. At eight it is seven-eighths leaves, at four three-quarters.

## References, four agents

From `size_report.py` on the four-agent grid trees listed under "Reproduce",
and from the tracker's `Pharos_Runs` sheet. Each entry is higher / lower /
tied, with the sign test's p.

| model | clique vs ring (rule 3) | star vs ring (rule 4) | hub vs leaves (rule 5) |
|---|---|---|---|
| Qwen3.5-122B-A10B | 2 / 3 / 23, p 1.00 | 0 / 8 / 20, p 0.008 | 2 / 0 / 26, p 0.50 |
| Qwen3.8-27B-FP8 | 6 / 3 / 19, p 0.51 | 2 / 9 / 17, p 0.065 | 1 / 0 / 27, p 1.00 |
| Qwen3.5-9B | 1 / 4 / 23, p 0.38 | 2 / 9 / 17, p 0.065 | 1 / 4 / 23, p 0.38 |
| **pooled** | **9 / 10 / 65, p 1.00** | **4 / 26 / 54, p < 0.001** | **4 / 4 / 76, p 1.00** |

- With four agents, the star is the outlier and the ring and the clique
  cannot be told apart. That is the shape Part I found in the corpus's
  low-communication PD cells: ring above star 13 to 2, clique above star 12 to
  3, clique against ring 7 to 8.
- The hub and its leaves are tied in 76 of 84 cells. Over the star runs their
  correlation is 1.00 (122B), 1.00 (27B) and 0.99 (9B).

The markers of rule 6, from `scale_report.py` and the 27B plan:

| model | M1 talk | M2 no channel | M3 frame gap | S1 empty channel |
|---|---|---|---|---|
| Qwen3.5-122B-A10B | 0.71 | 0.00 | 0.74 | 0.00 |
| Qwen3.8-27B-FP8 | 1.00 | 0.35 | 0.19 | 0.51 |
| Qwen3.5-9B | 0.03 | 0.03 | 0.33 | 0.12 |

The drift control's cells in the four-agent grid (PD, the ring):

| model | `baseline_cheap_talk` | `no_comm` |
|---|---|---|
| Qwen3.5-122B-A10B | 0.78 | 0.00 |
| Qwen3.8-27B-FP8 | 1.00 | 0.57 |
| Qwen3.5-9B | 0.05 | 0.07 |

## Reading rules

Every reading is exploratory: one model per condition, five runs per cell,
and runs that are all or nothing.

1. **Compliance, read first, per model.**
   - `verify_prompts.py` finds nothing, apart from "horizon leak" flags whose
     every hit lies in an agent's own message. Each such run is copied with
     those phrases masked, in the messages as sent, as composed and as each
     receiver saw them, and the copies must give no problem. HANDOFF lists
     the case as a known false positive.
   - `audit_corpus.py --n-agents 8` finds no issue.
   - Each tree has 140 runs, 5 in each of its 28 cells.
   - At most 10% of decisions are invalid on every topology.
   - The round-1 message prompt tokens of PD `baseline_cheap_talk` are the
     same for every model on each topology.

   If rule 1 fails for a model, nothing of that model is read.

   **The drift control.** Each control cell must lie within 0.20 of its value
   in the four-agent grid. If either moves by 0.20 or more, that model's rules
   2 and 6 are not read. Rules 3 to 5 compare topologies inside the
   eight-agent period, so they stand.
2. **Size at a fixed degree:** the ring at eight against the ring at four, as
   a contrast. Verdict per model and pooled: "higher at eight", "lower at
   eight" or "not detected".
3. **Degree at a fixed size:** the clique against the ring at eight (degree 7
   against 2), as a contrast, per model and pooled. The same contrast at four
   (3 against 2) is printed beside it as the reference.
4. **The star:** the star against the ring at eight, as a contrast, per model
   and pooled, beside the same contrast at four.
   - Descriptive, not part of the rule: the leaves alone against the ring at
     eight; the leaves at eight against the leaves at four; the hub at eight
     against the hub at four.
5. **The hub of seven:** on the star at eight, the hub against the mean of its
   leaves, as a contrast, per model and pooled, beside the same at four.
   - Descriptive: the correlation over the star's runs between the hub and its
     leaves, "coupled" at 0.90 or more.
6. **The markers** M1, M2, M3 (`docs/qwen35_scale_plan.md`) and S1
   (`docs/qwen38_27b_plan.md`), at eight against four, per model. A marker
   "holds" if it moves by less than 0.20, and otherwise "moves up" or "moves
   down".
7. **Descriptive, not rules.**
   - Each model's whole grid at eight beside four, per cell, game and
     topology.
   - **The talk:** promises and broken promises, per model, in PD
     `baseline_cheap_talk` and `framing_team`, at eight against four.
     - It uses the project's promise detector, which is not validated on
       these models.
     - 50 messages per model drawn at random (seed 7), 25 from each cell, are
       read by hand blind to the detector's label, with sheet and key kept
       apart. The agreement is reported beside the table.
   - The seconds per call.

## Prediction, stated before the run

- **Rule 1** passes for all three models, and every drift control holds.
- **Rule 2: not detected,** for every model and pooled. A ring agent's world
  does not change with the size: two neighbours, two messages, two edges. Only
  the count in the network paragraph changes.
- **Rule 3: not detected pooled.** Per model:
  - **122B: lower.** Degree 7 lowers its cooperation in the clique. It
    punishes a defection it sees:
    - in its own star its hub punished all 30 broken promises of its leaves;
    - after a betrayal it cooperates 16% of the time when its forecast is
      below 50 (64% when it is 50 or more).

    With talk on the star at four, 12 of its 20 round-1 decisions were
    cooperative. At that rate, an agent with seven neighbours almost surely
    sees a defection in round 1 (1 - 0.6^7 = 0.97). On the ring the chance is
    1 - 0.6^2 = 0.64.
  - **27B: not detected.** It tolerates a defector among cooperators. As a hub
    beside three lying 122B leaves, it cooperated in the next round after 15
    of 17 broken promises; its belief is the mean over its neighbours.
  - **9B: not detected.** It sits at the floor in the PD and near the ceiling
    in most Stag Hunt cells, so most of its cells tie.
- **Rule 4: lower pooled,** as at four. Per model: lower for the 122B; for the
  27B and the 9B, more cells lower than higher.
- **Rule 5: not detected,** for every model and pooled. The hub cooperates as
  its leaves do, as at four, and the correlation stays at 0.90 or more.
- **Rule 6:**
  - every marker of the 27B and the 9B holds;
  - for the 122B, M1 moves down, through the clique (rule 3) and the star;
  - its M2, M3 and S1 hold.
- **The talk (descriptive):** for each model, the share of promises broken in
  PD `baseline_cheap_talk` moves by less than 5 points from four to eight.
  Shi et al. found the rate moves by about one point between three and five
  agents, and in the corpus it does not depend on the wiring.

## Seen before writing

- Every cell of the three models' four-agent grids, and the references above.
  They were counted from the tracker's `Pharos_Runs` sheet and again by
  `size_report.py` from the trees.
- The corpus results of Part I, including its RQ2 contrasts.
- Every lab-server experiment that has been read: the forecast, intention and
  team-frame cells, contagion, the harm sources, the manipulator, and the
  first four mixed stars.
- These had run but had not been read:
  - the fifth and sixth mixed stars (a 9B hub) and their control, 11-12 19:15
    to 11-13 00:36;
  - the 122B's competitive cell with forecasts, 11-13 01:42 to 02:42.
- The plan for a 27B star with one or two 9B leaves was written and not
  committed. None of its runs existed.
- The fake-model test data described under "Design".

No eight-agent run existed when this was written.

## Limits fixed in advance

- **Scope.** One model per condition, five runs per cell, and runs that are
  all or nothing. One flipped run moves a cell by about 0.2.
- **The cells are not independent.** A model's 28 cells share one model and
  overlapping prompts. The sign test treats them as independent, as Part I
  did. Pooling over three models adds cells, not models. Every verdict is a
  direction for these three models.
- **Ties.** Floor and ceiling cells tie. A model with most cells at the floor
  or the ceiling adds little to a contrast: the 9B in the PD, and all three in
  much of the Stag Hunt.
- **Two periods.** Rules 2 and 6 compare runs made weeks apart, across at
  least one server update for the 122B and the 9B. The drift control covers
  two cells on one topology.
- **The description.** The network paragraph changes with the size ("one of 8
  agents", the neighbour counts). Size and its description cannot be
  separated here. A silent-topology version could separate them; it is not
  part of this plan.
- **Degree and reading.** At the hub and in the clique, degree comes with
  seven messages a round, and the prompt grows with them. Their length is
  recorded, not controlled.
- **The star's mix.** The star's value weighs the hub less at eight (one
  agent in eight) than at four (one in four). Rule 4 compares whole stars, as
  Part I did. The leaves alone are descriptive.
- **The hub of seven** is one agent per run: 80 decisions per cell.
- **The detector** is not validated on these models.
- **Server updates.**
  - If an update stops a lane, a new smoke run for that model comes before any
    further run of it. If the smoke run fails a check, nothing of that model
    after the update is read.
  - A cell cut short keeps its runs if it has at least 4 of 5. Otherwise its
    runs are set aside, and the cell is run again whole.
  - The write-up names every cell that ran after an update.
- **Speed.** A run at eight makes twice the calls of a run at four.
  - With four agents, a lane (one topology, sessions A, B and C) took 7.4-7.5
    h for the 27B, 11.0-11.2 h for the 9B and about 15 h for the 122B (3.2-6.1
    h per session).
  - At eight, at those speeds, a lane takes about 15 h (27B), 22 h (9B) and
    29 h (122B).
  - On 11-12 the 27B answered in 15-25 s per call, against 1.5-2.5 s on
    11-10. At that speed a lane takes days.
  - Measure the first session of each lane before relying on this. Speed
    enters no rule.

## Next, not covered by these rules

- The forecast cells and the mixed stars at eight, in plans of their own once
  the grid is read.
- A silent-topology grid at eight, to separate the size from its
  description.

## Reproduce

From `cheaptalk_bench`. The commands are the 27B's; for the other two models,
replace the model id and the tree names (`Qwen3.5-122B-A10B`, `Qwen3.5-9B`).

The smoke runs, one per topology, before a model's first lane:

```
python campaign.py --provider pharos --model Qwen/Qwen3.8-27B-FP8 --session A --scenarios baseline --games pd --topology star --n-agents 8 --n-runs 1 --n-rounds 2 --max-new-tokens 4096 --out-root ..\pharos_runs\smoke_grid_n8\runs --zip-mirror=
# the ring: --topology cycle --topology-aware-comm-prompt; the clique: --topology clique --topology-aware-comm-prompt
python verify_prompts.py ..\pharos_runs\smoke_grid_n8\runs\Qwen3.8-27B-FP8_n8 ..\pharos_runs\smoke_grid_n8\runs\Qwen3.8-27B-FP8_cycle_n8_commfix ..\pharos_runs\smoke_grid_n8\runs\Qwen3.8-27B-FP8_clique_n8_commfix
```

The grid, in three lanes side by side, one per topology. Each lane runs
sessions A, B and C in turn:

```
python campaign.py --provider pharos --model Qwen/Qwen3.8-27B-FP8 --session A --topology star --n-agents 8 --n-runs 5 --n-rounds 16 --max-new-tokens 4096 --out-root ..\pharos_runs\tok4096\grid_n8\runs --zip-mirror=
# then --session B and --session C; the ring: --topology cycle --topology-aware-comm-prompt; the clique: --topology clique --topology-aware-comm-prompt
```

The drift control, in the same days as the model's lanes (four agents):

```
python campaign.py --provider pharos --model Qwen/Qwen3.8-27B-FP8 --session A --scenarios baseline --games pd --topology cycle --topology-aware-comm-prompt --n-runs 5 --n-rounds 16 --max-new-tokens 4096 --out-root ..\pharos_runs\tok4096\grid_n8\drift --zip-mirror=
```

The checks and the reading, once a model's lanes and control are in:

```
python verify_prompts.py ..\pharos_runs\tok4096\grid_n8\runs\Qwen3.8-27B-FP8_n8 ..\pharos_runs\tok4096\grid_n8\runs\Qwen3.8-27B-FP8_cycle_n8_commfix ..\pharos_runs\tok4096\grid_n8\runs\Qwen3.8-27B-FP8_clique_n8_commfix
python audit_corpus.py --n-agents 8 ..\pharos_runs\tok4096\grid_n8\runs\Qwen3.8-27B-FP8_n8 ..\pharos_runs\tok4096\grid_n8\runs\Qwen3.8-27B-FP8_cycle_n8_commfix ..\pharos_runs\tok4096\grid_n8\runs\Qwen3.8-27B-FP8_clique_n8_commfix
python audit_corpus.py ..\pharos_runs\tok4096\grid_n8\drift\Qwen3.8-27B-FP8_cycle_commfix
python size_report.py --four ..\pharos_runs\tok4096\grid\Qwen3.5-122B-A10B ..\pharos_runs\tok4096\grid\Qwen3.5-122B-A10B_cycle_commfix ..\pharos_runs\tok4096\grid\Qwen3.5-122B-A10B_clique_commfix ..\pharos_runs\tok4096\grid\Qwen3.8-27B-FP8 ..\pharos_runs\tok4096\grid\Qwen3.8-27B-FP8_cycle_commfix ..\pharos_runs\tok4096\grid\Qwen3.8-27B-FP8_clique_commfix ..\pharos_runs\tok4096\grid\Qwen3.5-9B ..\pharos_runs\tok4096\grid\Qwen3.5-9B_cycle_commfix ..\pharos_runs\tok4096\grid\Qwen3.5-9B_clique_commfix --eight ..\pharos_runs\tok4096\grid_n8\runs\Qwen3.8-27B-FP8_n8 ..\pharos_runs\tok4096\grid_n8\runs\Qwen3.8-27B-FP8_cycle_n8_commfix ..\pharos_runs\tok4096\grid_n8\runs\Qwen3.8-27B-FP8_clique_n8_commfix --drift ..\pharos_runs\tok4096\grid_n8\drift\Qwen3.8-27B-FP8_cycle_commfix
```

`size_report.py` reads every model that has runs at both sizes. Give it the
eight-agent and drift trees of every model that is in; the pooled lines count
only the models read.

## Results, 2026-11-18

The three eight-agent grids ran from 11-14 to 11-18, 420 runs per model, each
with its drift control. They were read by `size_report.py` as committed in
`5d6384f`: each model once its runs were in, and pooled once the 9B's were.
Every reading is exploratory, as the plan fixed.

| model | smoke runs | three lanes, side by side | drift control |
|---|---|---|---|
| Qwen3.8-27B-FP8 | 11-14 19:44-19:49 | sessions A and B 11-14 20:51 -> 11-15 08:13; session C 11-15 15:00 -> 21:30 | 11-14 21:08-22:21 |
| Qwen3.5-122B-A10B | none | 11-16 13:38 -> 11-17 08:38 | 11-16 13:38-14:16 |
| Qwen3.5-9B | 11-17 15:39-15:40 | 11-17 16:06 -> 11-18 08:00 | 11-17 16:06-16:56 |

- **The 122B ran without its smoke runs.** Its lanes were started directly.
  The smoke runs' checks were made on its lane runs instead: the config, the
  round-1 tokens, `verify_prompts.py`, and the tags and cuts of the replies.
- **The 27B's session C** started about seven hours after its session B had
  ended, because the chained command for it did not run. No run was cut, and
  no lane stopped, in any model.

### Rule 1: it passes for all three

| | 122B | 27B | 9B |
|---|---|---|---|
| runs per tree, 5 in each of 28 cells | 140 | 140 | 140 |
| invalid decisions, star / ring / clique, of 17,920 each | 6 / 13 / 7 | 16 / 47 / 103 | 28 / 37 / 34 |
| round-1 message prompt tokens, PD `baseline_cheap_talk` | 464 / 462 / 437 | 464 / 462 / 437 | 464 / 462 / 437 |
| `verify_prompts.py`: prompts rebuilt; runs flagged | 139,840; 9 | 138,240; 2 | 139,840; 5 |
| flags in the agents' own words; their masked copies | 9 of 9; clean (3,456 prompts) | 2 of 2; clean (768) | 5 of 5; clean (1,920) |
| `audit_corpus.py --n-agents 8` | no issue | no issue | no issue |

The 122B's and the 9B's counts include their drift controls. The 27B's
control was checked on 11-15 with its first 240 lane runs (82,240 prompts,
nothing found).
- **The flags.**
  - Most are horizon wording in the agents' messages: payoff sums ("28
    instead of 16", "our shared payoff of 16"), counts of the rounds played
    ("our perfect sixteen-round streak" in round 16, "Sixteen rounds of
    mutual Stag"), "for all remaining rounds" (the 27B, round 3), and
    rhetoric ("one final round of mutual cooperation", the 122B, round 4;
    "This is the final round of domination", the 9B, round 15). No agent was
    told the horizon.
  - One 122B run was flagged by the history check, not the horizon check.
    On the ring, an agent's counterfactual "If Neighbor #6 chose Stag..."
    reached neighbours of agent 7, and the check reads it as agent 6's
    action shown to them. The rule names only horizon flags. This flag is of
    the same kind, words in a message, and its masked copy is clean. HANDOFF
    lists both kinds as known false positives.
- **Tags and cuts.** No reply of the 27B has a think tag, and one is cut at
  the cap. The 122B and the 9B write a stray `</think>`, with no opening tag,
  in 0.20% and 0.06% of their calls, and 0.09% and 0.14% of their replies
  are cut at 4,096 tokens, leaving an invalid action or an empty message
  (counted above). Their four-agent grids show about the same rates: 0.19%
  and 0.09% stray tags, 0.08% and 0.17% cut replies. No tag reaches a
  message that another agent reads.
- **The zips.** The 30 session zips and the 6 smoke-run zips are intact, and
  equal the runs on disk byte for byte.

### The drift control: none in any model

| model | `baseline_cheap_talk`: control / four-agent grid | `no_comm`: control / grid |
|---|---|---|
| 122B | 0.90 / 0.78 | 0.00 / 0.00 |
| 27B | 1.00 / 1.00 | 0.53 / 0.57 |
| 9B | 0.08 / 0.05 | 0.10 / 0.07 |

Rules 2 and 6 are read for all three.

### Rules 2 to 6

A contrast counts, over a model's 28 cells, those higher and those lower by
at least 0.05, and the ties (higher / lower / tied). Pooled, over 84.

| rule | 122B | 27B | 9B | pooled |
|---|---|---|---|---|
| 2. the ring at eight against the ring at four | 3 / 2 / 23, not detected | 4 / 4 / 20, not detected | 4 / 2 / 22, not detected | 11 / 8 / 65, p 0.65, not detected |
| 3. the clique against the ring, at eight | 4 / 3 / 21, not detected | 4 / 6 / 18, not detected | 2 / 3 / 23, not detected | 10 / 12 / 62, p 0.83, not detected |
| (the same at four) | 2 / 3 / 23 | 6 / 3 / 19 | 1 / 4 / 23 | 9 / 10 / 65 |
| 4. the star against the ring, at eight | 0 / 7 / 21, p 0.016, lower | 1 / 10 / 17, p 0.012, lower | 0 / 7 / 21, p 0.016, lower | 1 / 24 / 59, p < 0.001, lower |
| (the same at four) | 0 / 8 / 20, p 0.008, lower | 2 / 9 / 17, p 0.065 | 2 / 9 / 17, p 0.065 | 4 / 26 / 54, lower |
| 5. the hub against its leaves, at eight | 3 / 0 / 25, not detected | 2 / 0 / 26, not detected | 0 / 2 / 26, not detected | 5 / 2 / 77, p 0.45, not detected |
| (the same at four) | 2 / 0 / 26 | 1 / 0 / 27 | 1 / 4 / 23 | 4 / 4 / 76 |

- **Rule 4, descriptive.**
  - The leaves alone against the ring at eight give the star's counts: 0 /
    7, 1 / 10 and 0 / 7.
  - The leaves at eight against the leaves at four: 4 / 4, 4 / 5 and 6 / 4.
  - The hub at eight against the hub at four: 4 / 1, 5 / 5 and 8 / 4.
- **Rule 5, descriptive.** Over each model's 140 star runs at eight, the hub
  and the mean of its leaves correlate at r = 0.99 (0.99-1.00 at four):
  coupled. The hub minus its leaves is +0.02, +0.00 and -0.01.
- **Rule 6, the markers, four -> eight:**

| model | M1 talk | M2 no channel | M3 frame gap | S1 empty channel |
|---|---|---|---|---|
| 122B | 0.71 -> 0.85, holds | 0.00 -> 0.00, holds | 0.74 -> 0.78, holds | 0.00 -> 0.00, holds |
| 27B | 1.00 -> 0.98, holds | 0.35 -> 0.25, holds | 0.19 -> 0.15, holds | 0.51 -> 0.42, holds |
| 9B | 0.03 -> 0.05, holds | 0.03 -> 0.03, holds | 0.33 -> 0.25, holds | 0.12 -> 0.22, holds |

### Descriptive, not rules

- **Single cells.** Each model has 84 values (28 cells on three topologies).
  From four to eight, 0.30 or more moved 5 of the 122B's, 8 of the 27B's and
  1 of the 9B's. One flipped run moves a cell by about 0.2.
  - 122B: PD `baseline_cheap_talk` on the star 0.52 -> 0.82; PD
    `framing_team` on the ring 0.82 -> 0.37; PD `framing_business` on the
    ring 0.42 -> 0.73; PD `framing_competitive_context[cheap_talk]` on the
    clique 0.14 -> 0.51; SH `framing_competitive_context[no_comm]` on the
    clique 0.24 -> 0.58.
  - 27B: PD `no_comm` on the clique 0.74 -> 0.26, and `no_sense` 0.44 ->
    0.02; SH `silence` 0.96 -> 0.30 on the star, 0.99 -> 0.62 on the ring and
    0.62 -> 0.97 on the clique; SH `framing_competitive` on the star 0.77 ->
    0.26; SH `framing_competitive_context[no_comm]` on the star 0.95 -> 0.63;
    PD `framing_competitive_context[cheap_talk]` on the clique 0.21 -> 0.69.
  - 9B: SH `silence` on the ring 0.31 -> 0.70.
- **The talk (rule 7),** by the project's promise detector, over the three
  topologies: 957-960 decisions per cell at four, 1,915-1,920 at eight.

| PD cell | model | cooperate, 4 -> 8 | promise | broken, of promises |
|---|---|---|---|---|
| `baseline_cheap_talk` | 122B | 0.71 -> 0.85 | 0.79 -> 0.88 | 123/761 = 0.162 -> 133/1,690 = 0.079 |
| | 27B | 1.00 -> 0.98 | 1.00 -> 0.98 | 1/957 = 0.001 -> 22/1,891 = 0.012 |
| | 9B | 0.03 -> 0.05 | 0.18 -> 0.26 | 163/177 = 0.921 -> 439/502 = 0.875 |
| `framing_team` | 122B | 0.45 -> 0.27 | 0.99 -> 0.99 | 522/949 = 0.550 -> 1,376/1,894 = 0.727 |
| | 27B | 0.87 -> 0.90 | 0.99 -> 1.00 | 110/948 = 0.116 -> 188/1,920 = 0.098 |
| | 9B | 0.03 -> 0.04 | 0.97 -> 0.97 | 903/935 = 0.966 -> 1,797/1,870 = 0.961 |

  - In ordinary talk the 122B breaks fewer promises at eight. Most of the
    change is on the star (0.30 -> 0.08 of its promises). In round 1 it
    cooperates 0.87, against 0.67 at four. Under the team frame in the
    messages it breaks more, most of all on the ring (0.17 -> 0.63).
  - The 27B keeps its word in ordinary talk. Its 22 broken promises are all
    on the star; under the team frame, as at four, all of its broken
    promises are on the star.
  - The 9B still defects, and mostly says so: 1,372 of its 1,811 defections
    in `baseline_cheap_talk` come without a promise. It promises more at
    eight (502 decisions against 177), and breaks 439 of those promises.
- **The hand check.** 50 messages per model at eight, 25 from each cell
  (seed 7), read blind, with the sheets and keys apart:

| model | U | K | DU | N | agreement with the detector |
|---|---|---|---|---|---|
| 122B | 40 | 7 | 3 | 0 | 47 / 50 |
| 27B | 42 | 8 | 0 | 0 | 49 / 50 |
| 9B | 27 | 6 | 0 | 17 | 49 / 50 |

  - Each of the five disagreements is a promise that the detector misses.
    Four of them carry a defection clause, as in "I will Cooperate if you
    do; otherwise, I will Defect to protect my score". The fifth is a team
    message. The detector found no promise that the hand did not.
  - 16 of the 9B's 17 N announce its own defection, all in
    `baseline_cheap_talk`. The seventeenth, from the team cell, accuses its
    neighbours and commits to nothing.
  - Team talk that names no action: 6 of the 122B's 25 team messages, 23 of
    the 27B's and 9 of the 9B's.
- **Seconds per call,** three lanes side by side:

| model | session A | session B | session C | one lane, running |
|---|---|---|---|---|
| 27B | 3.05-3.16 | 1.58-1.67 | 1.88-2.03 | 17-18 h |
| 122B | 2.14-2.70 | 2.24-2.62 | 1.93-2.09 | 17-19 h |
| 9B | 3.15-3.26 | 1.31-1.38 | 1.51-1.60 | 15.5-16 h |

  The plan expected 15 h, 29 h and 22 h from the four-agent speeds.

### The prediction against the result

- **Rule 1 passes for all three, and every drift control holds:** yes. The
  122B's smoke runs were skipped (see above).
- **Rule 2, not detected for every model and pooled:** yes.
- **Rule 3, not detected pooled:** yes (10 / 12 / 62).
  - The 122B lower: **no**, not detected (4 / 3 / 21).
  - The 27B and the 9B not detected: yes.
- **Rule 4, lower pooled:** yes (1 / 24 / 59).
  - The 122B lower: yes.
  - More cells lower than higher for the 27B and the 9B: yes (1 / 10 and 0 /
    7). Each also reads "lower", at p 0.012 and 0.016.
- **Rule 5, not detected for every model and pooled, with the correlation at
  0.90 or more:** yes (r = 0.99 for each).
- **Rule 6:**
  - every marker of the 27B and the 9B holds: yes;
  - the 122B's M1 moves down: **no**. It holds, and rose (0.71 -> 0.85);
  - its M2, M3 and S1 hold: yes.
- **The talk (descriptive):** the share of promises broken in PD
  `baseline_cheap_talk` moves by less than 5 points: yes for the 27B (+1.1)
  and the 9B (-4.6); **no** for the 122B (-8.3).

### In words

- **Doubling the network changes little.** A ring of eight cooperates as a
  ring of four, in every model and pooled.
- **Neither does the number of neighbours.** At eight, a clique (seven
  neighbours) cooperates as a ring (two), as it does at four.
- **The star is the one shape that lowers cooperation.** Its leaves, each
  with one neighbour, cooperate less than the agents of a ring, and the hub
  moves with them. At eight, each model reaches p < 0.05 on its own; at four
  only the 122B did.
- **The 122B's punishment did not spread through the clique.** With talk it
  cooperates more at eight, breaks fewer promises in ordinary talk, and
  starts more cooperatively. Both of the plan's misses come from this one
  expectation.
- **The talk keeps its kind.** The 27B keeps its word, and the 9B announces
  its defection. Under the team frame the 122B breaks more of its promises at
  eight (0.55 -> 0.73), and the 9B breaks nearly all of them at both sizes.

**Limits.**
- **Scope and the test,** as fixed above: five runs per cell; a model's 28
  cells are not independent; pooling adds cells, not models.
- **The 122B's lanes ran without the smoke runs** that the design asked for.
- **One flag outside the letter of rule 1:** the 122B's history-check flag.
- **The detector** is not validated on these models. On the 150 messages read
  by hand it agrees on 145.

**Files.** The read-only scripts, their outputs, the hand sheets with their
keys and labels, and the smoke runs' checks are kept beside the runs, outside
the repo, in `..\pharos_runs\tok4096\grid_n8\analysis\`. Its `README.md` lists
them.

**Next.**
- The plan's own next steps: the forecast cells and the mixed stars at eight,
  and a silent-topology grid at eight, each in a plan of its own.
- The plan for a 27B star with one or two 9B leaves
  (`docs/hetero_star_9b_dose_plan.md`) was committed as `defb396`. Its runs
  come next.
