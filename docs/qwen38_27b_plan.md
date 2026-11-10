# A later generation: Qwen3.8-27B on the lab server

This is the plan for an exploratory follow-up: Qwen/Qwen3.8-27B-FP8 on the lab
server, set against the two Qwen3.5 models and the five corpus models. It was
written on 2026-11-09, before any grid run of the 27B. The reading rules below
decide what the results are allowed to say. Committing this file before the
first run fixes them. No earlier cell, plan or rule is touched.

## Question

Qwen3.5-122B-A10B plays the Prisoner's Dilemma unlike the five corpus models
on three markers. Qwen3.5-9B, its generation at the corpus's size, departs the
same way on two of them and lies just outside the corpus range on the third.
The 9B plan's verdict was therefore "generation": the departures come with
Qwen3.5, not with the total number of parameters (`docs/qwen35_scale_plan.md`,
results of 2026-11-07).

That plan left the engine open.
- The corpus ran with transformers on Kaggle, in 4-bit. Both Qwen3.5 models
  run with vLLM on the lab server.
- So "like the 122B" can come from the generation or from the engine. Only a
  corpus model on the lab server could tell them apart, and none is served.

The lab server also serves Qwen/Qwen3.8-27B-FP8: a later Qwen generation,
dense, with 27B parameters, served in FP8. It is not a corpus model, but it
runs on the same engine as the Qwen3.5 models, and its prompts pass through
the same chat template (464 tokens in its smoke runs, as for Qwen3.5).
- **If it plays as the corpus,** the server and its engine do not by
  themselves produce the Qwen3.5 pattern. The pattern comes with the Qwen3.5
  models and does not survive the change to the 27B. Which of the three
  changes below removes it, the rules cannot say.
- **If it plays as the Qwen3.5 models,** the pattern survives all three
  changes: it carries over to a later generation of the family, at a third
  size and another precision. The engine stays open.

Three things change at once from the Qwen3.5 models:
- **the generation:** Qwen3.8 against Qwen3.5;
- **the size:** 27B dense, so more active parameters than either Qwen3.5
  model (9B dense; 10B active of 122B);
- **the precision:** FP8, while the Qwen3.5 model ids name no quantization.

## Design

- **The grid of the 122B and the 9B, unchanged, with the 27B.**
  - Sessions A, B and C: the star with the original prompt; the ring and the
    clique with the corrected routing prompt (`--topology-aware-comm-prompt`).
  - Prisoner's Dilemma and Stag Hunt, 5 runs per cell: 420 runs.
  - 16 rounds, hidden horizon, memory 10, T = 0.7, output cap 4096 (given
    explicitly, as for both Qwen3.5 models), thinking off.
- **Placement.** The runs go to `tok4096/grid`. The trees are
  `Qwen3.8-27B-FP8`, `Qwen3.8-27B-FP8_cycle_commfix` and
  `Qwen3.8-27B-FP8_clique_commfix`, beside the 122B's and the 9B's.
- **Code.** Nothing changes.
  - `scale_report.py` reads the rules with `--target Qwen3.8-27B-FP8`. It
    prints the verdict in the 9B plan's words: here "generation" reads "like
    Qwen3.5", and "size" reads "like the corpus" (rule 3).
  - S1 and the talk table (rule 4) are read by read-only scripts kept beside
    the runs, as for the 9B.
- **Two smoke runs,** each `forecast_probe` on the star, 2 rounds, on
  2026-11-09:
  - 13:44, in `pharos_runs/smoke_new_models`;
  - 22:06, in `pharos_runs/smoke_27b_after_update`, after a model update on
    the server at about 16:15.

  Both pass the four checks of the 9B forecast plan:
  - **thinking is off:** replies average 170 and 171 tokens, at 0.231 and
    0.230 tokens per character, with no `<think>` block, and every reply
    finished normally;
  - **every forecast parses:** 16 of 16 in each run, none recovered;
  - **the round-1 message prompt** has 464 tokens, Qwen3.5's template;
  - **the speed:** 3.5 and 2.3 s per call, one run at a time.

  `verify_prompts.py` finds nothing in the 40 prompts of either run.

## Markers

The 9B plan's three Prisoner's Dilemma markers, unchanged. On each of them,
the 122B lies outside the range of the five corpus models.
- Each marker is a mean of cell values, where a cell's value is the mean of its
  run means over valid decisions.
- It is taken over the topologies where the corpus ran the cells under the
  same prompt as the lab server.

The markers:
- **M1 talk:** `baseline_cheap_talk`, over the star, the ring and the clique.
- **M2 no channel:** the mean of `no_comm`, `silence` and `no_sense`, over the
  star, the ring and the clique.
- **M3 frame gap:** `framing_team_context[cheap_talk]` minus `framing_team`,
  over the star and the clique. The corpus ring has only session A and
  `framing_competitive`.

One Stag Hunt marker is added, outside the verdict:
- **S1 empty channel:** the mean of the Stag Hunt's `silence` and `no_sense`,
  over the star and the clique, the two topologies where the corpus ran the
  Stag Hunt.
- It was noticed in the 9B's results, after its run: an open channel left
  empty, or filled with noise, collapses Stag Hunt cooperation in both
  Qwen3.5 models. The 27B is its first test on a model not seen when it was
  noticed.

**References**, from `scale_report.py` with the trees listed under
"Reproduce" (S1 from the same cells):

| model | M1 talk | M2 no channel | M3 frame gap | S1 empty channel |
|---|---|---|---|---|
| Llama-3.1-8B-Instruct | 0.98 | 0.56 | 0.32 | 0.70 |
| Qwen2.5-7B-Instruct | 1.00 | 0.30 | 0.01 | 0.98 |
| Qwen3-4B | 1.00 | 0.60 | 0.00 | 1.00 |
| gemma-2-2b-it | 0.93 | 0.23 | 0.01 | 0.52 |
| gemma-2-9b-it | 1.00 | 0.31 | 0.00 | 0.87 |
| **corpus range** | **0.93-1.00** | **0.23-0.60** | **0.00-0.32** | **0.52-1.00** |
| **Qwen3.5-122B-A10B** | **0.71** | **0.00** | **0.74** | **0.00** |
| Qwen3.5-9B | 0.03 | 0.03 | 0.33 | 0.12 |

## Reading rules

Every reading is exploratory: one model, five runs per cell, and runs that are
all or nothing.

1. **Compliance, read first.**
   - `verify_prompts.py` finds nothing, apart from "horizon leak" flags whose
     every hit lies in an agent's own message. Each such run is copied with
     those phrases masked, in the messages as sent, as composed and as each
     receiver saw them, and the copies must give no problem. That is how the
     9B's four flags were read; HANDOFF lists the case as a known false
     positive.
   - `audit_corpus.py` finds no issue.
   - At most 10% of decisions are invalid on every topology.
   - The round-1 message prompt tokens of `baseline_cheap_talk` equal the
     122B's on every topology: 463 and 464 on the star, 461 and 462 on the
     ring, 436 and 437 on the clique.

   If rule 1 fails, nothing else is read.
2. **Each marker** sets the 27B's value against the 122B's (L) and the corpus
   range (lo to hi), as in the 9B plan.
   - **When L is below the range (M1, M2):**
     - "like the 122B" if the value is at most the midpoint (L + lo) / 2;
     - "like the corpus" if it is at least lo;
     - otherwise "between".
   - **When L is above the range (M3):**
     - "like the 122B" if the value is at least (L + hi) / 2;
     - "like the corpus" if it is at most hi;
     - otherwise "between".
   - **The midpoints:** M1 0.82, M2 0.12, M3 0.53.
3. **The verdict.**
   - **Like Qwen3.5:** at least two markers read "like the 122B", and none
     "like the corpus". `scale_report.py` prints this as "generation".
   - **Like the corpus:** at least two read "like the corpus", and none "like
     the 122B". `scale_report.py` prints this as "size".
   - **Mixed:** anything else.
4. **Descriptive, not rules.**
   - **S1,** read as rule 2 reads M1 and M2: L 0.00, lo 0.52, midpoint 0.26.
     By that reading the 9B's 0.12 is "like the 122B".
   - **The 27B's whole grid,** beside the 9B's and the 122B's, per topology
     and game.
   - **The talk.** The table of the 9B's results, for the PD
     `baseline_cheap_talk` and `framing_team` cells over the three
     topologies: decisions, cooperation, promises, promises followed by
     defection, defections without a promise, and the same in round 1.
     - It uses the project's promise detector, which is not validated on
       these models.
     - 50 messages drawn at random (seed 7), 25 from each cell, are read by
       hand blind to the detector's label (sheet and key apart, as in the
       9B's hand checks). The agreement is reported beside the table.

## Prediction, stated before the run

- **Rule 1:** it passes.
- **The verdict:** like the corpus, with all three markers like the corpus.
  - **M1 at least 0.93.** Talk brings the 27B the corpus's near-full
    cooperation.
  - **M2 at least 0.23.** Without real talk, it still cooperates in part.
    This is the least certain of the three: neither smoke run had a closed
    channel.
  - **M3 at most 0.32.** With talk already near full cooperation, the team
    frame has little room to add, in the messages or in the system prompt.
- **S1 at least 0.52,** like the corpus. It is as uncertain as M2.
- **The basis: the two smoke runs.**
  - In both, every agent cooperated in both rounds.
  - Before any message in round 1, every agent intended to cooperate and
    forecast 50-75 for its neighbours. After the messages, the forecasts
    rose to 85-95.
  - The 9B, under the same probe, intended to defect in all 60 of its
    round-1 forecasts before the talk, and forecast 11 on average.

## Seen before writing

- Every grid number of the 122B, the 9B and the corpus, as in the table
  above.
- The 9B's private-forecast cells (`docs/qwen35_9b_forecast_plan.md`, results
  of 2026-11-09).
- The 27B's two smoke runs, every message and forecast in them, as in the
  design above.
- The 27B's latency on 2026-11-09: 3.5 s per call at 13:44 and 2.3 s at
  22:06, one run at a time.
- The server's model update at about 16:15. Its notice stopped one of the
  9B's forecast runs. What it changed is not known.

No grid run of the 27B existed when this was written.

## Limits fixed in advance

- **Scope.** One model, five runs per cell, runs that are all or nothing.
  - One flipped run moves a cell by about 0.2.
  - The markers average 15 runs (M1), 45 (M2) and 20 (M3). S1 averages 20.
- **Three changes at once:** the generation, the size and the precision.
  "Like the corpus" cannot be pinned on one of them. "Like Qwen3.5" says that
  the pattern survives all three.
- **The engine.** The 27B shares the Qwen3.5 models' server and engine.
  - "Like the corpus" therefore shows that the engine does not by itself
    produce the pattern. That was the 9B plan's open limit.
  - "Like Qwen3.5" leaves the engine open, as for the 9B.
- **Precision.** The corpus ran in 4-bit and the 27B runs in FP8; the Qwen3.5
  ids name no quantization. If lower precision moved a model toward the
  corpus, "like the corpus" could come from it. The rules cannot tell.
- **Sampling.** The client sends only the temperature and the output cap.
  Every other sampling setting is the server's default for each model, as for
  the Qwen3.5 models.
- **The output cap:** 4096, as for both Qwen3.5 models.
- **Server updates.** The server's models changed once during the 9B's
  forecast cells.
  - If an update stops the grid, a new smoke run comes before any further run.
    If the smoke run fails one of the four checks, nothing after the update is
    read.
  - A cell cut short keeps its runs if it has at least 4 of 5, as the 9B's
    clique team cell did. Otherwise its runs are set aside, and the cell is run
    again whole.
  - The write-up names every cell that ran after an update.
- **Server load.** The latency varies with the server's other users. Each
  session's `_progress.json` records the seconds per run, and nothing in the
  protocol depends on them.

## Next, not covered by these rules

- **The two private-forecast cells for the 27B** (`forecast_probe`,
  `framing_team_probe`), in a short plan of their own once the grid is read.

## Reproduce

From `cheaptalk_bench`, in three lanes side by side, one per topology. Each
lane runs sessions A, B and C in turn:

```
python campaign.py --provider pharos --model Qwen/Qwen3.8-27B-FP8 --session A --topology star --n-runs 5 --n-rounds 16 --max-new-tokens 4096 --out-root ..\pharos_runs\tok4096\grid --zip-mirror=
# then --session B and --session C; the ring: --topology cycle --topology-aware-comm-prompt; the clique: --topology clique --topology-aware-comm-prompt
python verify_prompts.py ..\pharos_runs\tok4096\grid\Qwen3.8-27B-FP8 ..\pharos_runs\tok4096\grid\Qwen3.8-27B-FP8_cycle_commfix ..\pharos_runs\tok4096\grid\Qwen3.8-27B-FP8_clique_commfix
python audit_corpus.py ..\pharos_runs\tok4096\grid\Qwen3.8-27B-FP8 ..\pharos_runs\tok4096\grid\Qwen3.8-27B-FP8_cycle_commfix ..\pharos_runs\tok4096\grid\Qwen3.8-27B-FP8_clique_commfix
python scale_report.py --target Qwen3.8-27B-FP8 --roots ..\star_runs\Llama-3.1-8B-Instruct_star ..\star_runs\Qwen2.5-7B-Instruct_star ..\star_runs\Qwen3-4B_star ..\star_runs\gemma-2-2b-it_star ..\star_runs\gemma-2-9b-it_star ..\cycle_runs\Llama-3.1-8B-Instruct_cycle_commfix ..\cycle_runs\Qwen2.5-7B-Instruct_cycle_commfix ..\cycle_runs\Qwen3-4B_cycle_commfix ..\cycle_runs\gemma-2-2b-it_cycle_commfix ..\cycle_runs\gemma-2-9b-it_cycle_commfix ..\clique_runs\Llama-3.1-8B-Instruct_clique ..\clique_runs\Qwen2.5-7B-Instruct_clique ..\clique_runs\Qwen3-4B_clique ..\clique_runs\gemma-2-2b-it_clique ..\clique_runs\gemma-2-9b-it_clique ..\pharos_runs\tok4096\grid\Qwen3.5-122B-A10B ..\pharos_runs\tok4096\grid\Qwen3.5-122B-A10B_cycle_commfix ..\pharos_runs\tok4096\grid\Qwen3.5-122B-A10B_clique_commfix ..\pharos_runs\tok4096\grid\Qwen3.5-9B ..\pharos_runs\tok4096\grid\Qwen3.5-9B_cycle_commfix ..\pharos_runs\tok4096\grid\Qwen3.5-9B_clique_commfix ..\pharos_runs\tok4096\grid\Qwen3.8-27B-FP8 ..\pharos_runs\tok4096\grid\Qwen3.8-27B-FP8_cycle_commfix ..\pharos_runs\tok4096\grid\Qwen3.8-27B-FP8_clique_commfix
```

The references above come from exactly these trees, without the 27B's. Do
not add `star_runs/gemma-2-2b-it_star_commfix` or `cycle_runs/<model>_cycle`,
which has the old prompt.

**Timing.** A lane of 140 runs makes about 14,000 calls. The 9B's lanes ran
at 2.6-3.1 s per call and took 11.0-11.2 h; the 122B ran at 3.0-4.9 s per
call. At those rates a lane takes 10-19 h. The 27B's replies in its smoke
runs are a little longer than the 9B's (171 tokens against 134). Measure the
first session of each lane before relying on this.

## Results, 2026-11-10

Read on 2026-11-10 after all 420 runs. Every reading is exploratory, as fixed
above.

**Runs and checks.**
- **When and on what.** The 420 runs ran on 2026-11-10 from 00:54 to 08:24, on
  `0c8809a`. That commit holds this plan and was pushed at 00:42.
  - Three lanes ran in parallel, one per topology, each running sessions A, B
    and C in turn.
  - A lane took 7.4-7.5 h, and a session 1.7-3.3 h: 1.55-2.14 s per call.
    That is faster than the 10-19 h foreseen.
  - No run stalled. The longest gap between two run files of a lane is 7.6
    minutes.
  - No server update came during the grid, so no cell ran after one.
- **The trees.** Each tree has 140 runs of 16 rounds, with no duplicate. Every
  config names the model and the output cap of 4096.
- **The configs.** Every config field equals the 122B's for the same cell and
  run, apart from three: the model id, the output folder, and the
  `forecast_probe` switch, which is off here.
- **Cuts.** 3 of 42,240 calls were cut at the output cap, all action calls (2
  on the ring, 1 on the clique). Each left an invalid decision. No reply
  contains a `<think>` block.
- **The zips.** The nine session zips are intact and byte-identical to the
  runs on disk. `campaign.py` zips the whole tree, so session B's zip also
  holds session A's runs, and session C's holds all 140.
- **A third smoke run.** At 23:00 on 2026-11-09, before this plan was
  committed, the second smoke run's command ran again into the same folder,
  `pharos_runs/smoke_27b_after_update/runs`. It was found at 00:49 on 11-10,
  after the commit, which is why the design above names two.
  - `campaign.py` found two runs where it expected one, so it wrote no zip for
    this run. The 22:07 zip still holds the 22:06 run, byte for byte.
  - It passes the same four checks: replies of 157 tokens on average, at
    0.229 tokens per character, with no `<think>` block; 16 of 16 forecasts,
    none recovered; 464 tokens; 1.8 s per call.
  - All four agents cooperated in both rounds. `verify_prompts.py` finds
    nothing in the 80 prompts of the folder.

### Rule 1: it passes

| topology | invalid decisions | round-1 tokens, 27B | 122B |
|---|---|---|---|
| star | 15/8,960 = 0.002 | 463, 464 | 463, 464 |
| ring | 17/8,960 = 0.002 | 461, 462 | 461, 462 |
| clique | 33/8,960 = 0.004 | 436, 437 | 436, 437 |

The two token values are the Stag Hunt and the Prisoner's Dilemma prompts.

- `audit_corpus.py` finds no issue, no duplicate history and no cell above 10%
  invalid.
- **`verify_prompts.py` rebuilt 69,120 prompts and flags 5 runs for "horizon
  leak".** As the rule foresees, every hit is in an agent's own message:

| run | round | the words |
|---|---|---|
| star, SH `baseline_cheap_talk`, run 5 | 16 | "Let's continue this optimal cooperation for round sixteen" |
| ring, PD `counterfactual`, run 5 | 16 | "we would secure our sixteenth consecutive round of maximum mutual gain" |
| ring, PD `framing_competitive_context[cheap_talk]`, run 3 | 10-16 | "Let's lock in cooperation for all remaining rounds", in 10 messages |
| ring, PD `framing_competitive_context[cheap_talk]`, run 5 | 6 | "let's continue this winning pattern for all remaining rounds" |
| ring, SH `framing_competitive_context[cheap_talk]`, run 1 | 16 | "Sixteen rounds of success" |

- The three in round 16 count the rounds so far: every prompt states the
  current round. The other two speak of the rounds still to come, whose
  number they do not know.
- **The masked copies are clean.** In copies of the five runs, these phrases
  were masked in the agents' messages: as sent, as composed, and as each
  receiver saw them. The copies give no problem in 960 rebuilt prompts.

### Rules 2 and 3: the verdict is "like the corpus"

| marker | 27B | 122B (L) | corpus | midpoint | reading |
|---|---|---|---|---|---|
| M1 talk | 1.00 | 0.71 | 0.93-1.00 | 0.82 | like the corpus |
| M2 no channel | 0.35 | 0.00 | 0.23-0.60 | 0.12 | like the corpus |
| M3 frame gap | 0.19 | 0.74 | 0.00-0.32 | 0.53 | like the corpus |

**All three markers read "like the corpus", and none "like the 122B". The
verdict is "like the corpus".** `scale_report.py` prints it as "size".

- **The margins.** Unrounded, the markers are 0.9990, 0.3472 and 0.1875. They
  lie 0.071, 0.116 and 0.131 inside the corpus edge that faces the 122B.
- **M3 comes from the star alone.** There `framing_team_context[cheap_talk]`
  is 0.99 and `framing_team` 0.62, a gap of 0.375. On the clique both are
  1.00.
- **M2 mixes full runs with collapsed ones.** Six of its nine cells hold a run
  at 0.95 or more beside runs at 0.43 or less. The other three hold only runs
  at 0.27 or less.

### Rule 4, descriptive: the 27B's grid

Mean of run means over valid decisions, n = 5 per cell:

| cell | PD star | PD ring | PD clique | SH star | SH ring | SH clique |
|---|---|---|---|---|---|---|
| `no_comm` | 0.38 | 0.57 | 0.74 | 0.99 | 1.00 | 1.00 |
| `baseline_cheap_talk` | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| `no_sense` | 0.06 | 0.26 | 0.44 | 0.23 | 0.02 | 0.22 |
| `silence` | 0.17 | 0.05 | 0.46 | 0.96 | 0.99 | 0.62 |
| `counterfactual` | 0.86 | 1.00 | 0.98 | 1.00 | 1.00 | 1.00 |
| `framing_business` | 0.81 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| `framing_team` | 0.62 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| `framing_competitive` | 0.01 | 0.10 | 0.39 | 0.77 | 0.74 | 0.99 |
| `framing_business_context[no_comm]` | 0.91 | 1.00 | 0.85 | 1.00 | 0.99 | 1.00 |
| `framing_business_context[cheap_talk]` | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| `framing_team_context[no_comm]` | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| `framing_team_context[cheap_talk]` | 0.99 | 0.99 | 1.00 | 1.00 | 1.00 | 1.00 |
| `framing_competitive_context[no_comm]` | 0.06 | 0.08 | 0.06 | 0.95 | 0.98 | 0.94 |
| `framing_competitive_context[cheap_talk]` | 0.59 | 0.75 | 0.21 | 0.81 | 1.00 | 1.00 |

- **In the PD, talk brings the 27B full cooperation, as it does the corpus.**
  - Ordinary talk gives 1.00 on every topology.
  - Without a channel it still cooperates in part (0.38, 0.57, 0.74). An empty
    channel gives less: `silence` 0.17, 0.05 and 0.46; `no_sense` 0.06, 0.26
    and 0.44.
- **S1, the Stag Hunt's empty channel, is 0.51: "between".**
  - Unrounded it is 0.5078. The corpus low is gemma-2-2b-it's 0.5199, so it
    misses "like the corpus" by 0.012.
  - **Its two halves split.** `no_sense` collapses the Stag Hunt: 0.23, 0.02
    and 0.22, below every corpus model's 0.37 or more, as in both Qwen3.5
    models. `silence` does not: 0.96, 0.99 and 0.62. Two of the five clique
    runs collapse there (0.11 and 0.09).
  - **Under `no_sense`, the round-1 Hare players speak of risk.** In round 1,
    43 of the 60 agents play Hare. Every one of their reasonings speaks of
    risk or safety, and 37 of them also refer to the message, as in
    "non-binding small talk, providing no signal of intent".
- **The talk.** The table reads the messages with the promise detector, so it
  is descriptive.

| PD cell | model | decisions | cooperate | promise | promise, then Defect | no promise, then Defect | round 1: cooperate, promise, promise then Defect |
|---|---|---|---|---|---|---|---|
| `baseline_cheap_talk` | 27B | 960 | 959 | 957 | 1 | 0 | 59, 59, 1 of 60 |
| | 9B | 957 | 24 | 177 | 163 | 770 | 1, 20, 19 of 60 |
| | 122B | 958 | 678 | 761 | 123 | 157 | 40, 57, 18 of 60 |
| `framing_team` | 27B | 960 | 838 | 948 | 110 | 12 | 58, 60, 2 of 60 |
| | 9B | 959 | 32 | 935 | 903 | 24 | 20, 60, 40 of 60 |
| | 122B | 960 | 428 | 949 | 522 | 10 | 45, 60, 15 of 60 |

  - **In ordinary talk it keeps its word.** It promises in 957 of 960
    decisions and breaks one promise, in round 1 on the star. Typical
    messages: "Cooperation is optimal; I will continue cooperating every
    round for maximum mutual scores." "I appreciate our cooperation; I'll keep
    cooperating as long as you do."
  - **Under the team frame in the messages, its broken promises sit on the
    star.** All 110 are there. The star's five runs give 1.00, 0.81, 1.00,
    0.16 and 0.12.
    - Runs 4 and 5 collapse after agent 1, a leaf, defects in round 1.
    - Run 2 falls to 0.81 after the same leaf defects in round 7.
    - On the ring and the clique the cell is 1.00.
  - **Elsewhere in the grid** (by the detector), the 27B breaks promises in
    two more cells. With the competitive frame in the system prompt and talk
    it breaks 116, on every topology (47, 42 and 27). With the business frame
    in the messages it breaks 54, on the star (0.81).
- **The hand check.** 50 messages were read blind, 25 from each cell (seed 7):
  U 46, K 4, and none DU, M or N.
  - The detector agrees on 49. The miss is a team message, "Let's unite as a
    team to support our shared goal of mutual success and victory together",
    which the detector does not read as a promise.
  - 24 of the 25 team messages name no action and say nothing of what the
    sender itself will do. They are team talk only.

### The prediction against the result

- **Rule 1,** it passes: yes.
- **The verdict,** like the corpus with all three markers like the corpus:
  yes.
  - M1 at least 0.93: yes (1.00).
  - M2 at least 0.23: yes (0.35).
  - M3 at most 0.32: yes (0.19).
- **S1 at least 0.52:** no, narrowly. It is 0.51, "between". `no_sense`
  collapses the Stag Hunt and `silence` does not.

### In words

- **The 27B plays the Prisoner's Dilemma as the corpus does.** Talk brings it
  full cooperation, and without talk it still cooperates in part.
- **So the server and its engine do not by themselves produce the Qwen3.5
  pattern.** The 27B runs on the same server and engine as both Qwen3.5
  models, through the same chat template. Which of the three changes removes
  the pattern (the generation, the size or the precision), the design cannot
  say.
- **It keeps its word in ordinary talk.** Its broken promises sit in framed
  cells, most of all where a single round-1 defection on the star brought the
  run down.
- **One Qwen3.5 trait survives.** A channel filled with noise collapses its
  Stag Hunt, below every corpus model.

**Limits.**
- **Scope.** One model, five runs per cell, and runs that are all or nothing.
- **Three changes at once.** "Like the corpus" cannot be pinned on the
  generation, the size or the precision.
- **Precision.** The corpus ran in 4-bit; the 27B runs in FP8.
- **The detector** is not validated on these models. On the 50 messages read
  by hand it agrees on 49.

**Files.** The read-only scripts of the reading, their outputs and the hand
check are kept beside the runs, outside the repo, in
`..\pharos_runs\tok4096\grid\analysis_27b\`.

**Next.** The two private-forecast cells for the 27B ran on 2026-11-10, by
their own plan: `docs/qwen38_27b_forecast_plan.md`.
