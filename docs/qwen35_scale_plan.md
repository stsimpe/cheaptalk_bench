# Size or generation: Qwen3.5 at 9B on the lab server

This is the plan for an exploratory follow-up: Qwen/Qwen3.5-9B on the lab
server, set against Qwen/Qwen3.5-122B-A10B and the five corpus models. It was
written on 2026-11-06, before any grid run of the 9B. The reading rules below
decide what the results are allowed to say. Committing this file before the
first run fixes them. No earlier cell, plan or rule is touched.

## Question

Qwen3.5-122B-A10B on the lab server plays the Prisoner's Dilemma unlike the
five corpus models (2-9B, run on Kaggle):
- **Ordinary talk** brings it 0.71 cooperation (0.52 star, 0.78 ring, 0.82
  clique), against 0.93-1.00 for the corpus models.
- **Every closed or empty channel** (`no_comm`, `silence`, `no_sense`) gives it
  0.00, against 0.23-0.60 for the corpus models.
- **The team frame** works in its system prompt but not in its messages: the
  gap is 0.74, against 0.00-0.32 for the corpus models.

Two things change at once between them:
- **Size:** 122B parameters in total, 10B active, against 2-9B.
- **Generation:** Qwen3.5 (2026), against models of 2024-2025.

The lab server now also serves Qwen/Qwen3.5-9B. It is Qwen3.5's generation at
the corpus's size, with about as many active parameters as the 122B (9B dense,
against 10B active).
- If the 9B plays as the 122B, the difference comes with the generation (or
  the engine: see the limits).
- If it plays as the corpus, the difference comes with size, meaning the total
  number of parameters.

## Design

- **The 122B's grid, unchanged, with the 9B.**
  - Sessions A, B and C: the star with the original prompt; the ring and the
    clique with the corrected routing prompt (`--topology-aware-comm-prompt`).
  - Prisoner's Dilemma and Stag Hunt, 5 runs per cell: 420 runs.
  - 16 rounds, hidden horizon, memory 10, T = 0.7, output cap 4096 (given
    explicitly, as for the 122B), thinking off.
- **Placement.** The runs go to `tok4096/grid`. The trees are `Qwen3.5-9B`,
  `Qwen3.5-9B_cycle_commfix` and `Qwen3.5-9B_clique_commfix`, beside the 122B's.
- **Code.** Nothing in the game changes. This plan adds `scale_report.py`,
  which reads the rules below.
- **The smoke run** (2026-11-06, `pharos_runs/smoke_new_models`):
  `forecast_probe` on the star, 2 rounds.
  - `verify_prompts.py` found nothing in its 40 prompts.
  - The round-1 message prompt has 464 tokens, as the 122B's.
  - No reply was cut. Replies average 134 tokens, at 0.245 tokens per
    character (122B: 0.241), so thinking is off.

## Markers

The plan reads three Prisoner's Dilemma markers. On each of them, the 122B lies
outside the range of the five corpus models.
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

**References**, from `scale_report.py`. The corpus trees are
`star_runs/<model>_star`, `cycle_runs/<model>_cycle_commfix` and
`clique_runs/<model>_clique`; the 122B's are in `tok4096/grid`.

| model | M1 talk | M2 no channel | M3 frame gap |
|---|---|---|---|
| Llama-3.1-8B-Instruct | 0.98 | 0.56 | 0.32 |
| Qwen2.5-7B-Instruct | 1.00 | 0.30 | 0.01 |
| Qwen3-4B | 1.00 | 0.60 | 0.00 |
| gemma-2-2b-it | 0.93 | 0.23 | 0.01 |
| gemma-2-9b-it | 1.00 | 0.31 | 0.00 |
| **corpus range** | **0.93-1.00** | **0.23-0.60** | **0.00-0.32** |
| **Qwen3.5-122B-A10B** | **0.71** | **0.00** | **0.74** |

A fourth candidate, `counterfactual`, is left out. The 122B's value (0.13)
falls inside the corpus range, because gemma-2-2b has 0.06.

## Reading rules

Every reading is exploratory: one model on each side, five runs per cell, and
runs that are all or nothing.

1. **Compliance, read first.**
   - `verify_prompts.py` finds nothing, and `audit_corpus.py` finds no issue.
   - At most 10% of decisions are invalid on every topology. That is the rate
     `audit_corpus.py` flags; the 122B had 0.05%.
   - The round-1 message prompt tokens of `baseline_cheap_talk` equal the
     122B's on every topology: the same prompts, through the same template.

   If rule 1 fails, nothing else is read.
2. **Each marker** sets the 9B's value against the 122B's (L) and the corpus
   range (lo to hi).
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
   - **Generation:** at least two markers read "like the 122B", and none
     "like the corpus".
   - **Size:** at least two read "like the corpus", and none "like the 122B".
   - **Mixed:** anything else.
4. **Descriptive, not rules:** the 9B's whole grid beside the 122B's, per
   topology and game.

`scale_report.py` prints all four. It was tested on real runs copied under the
9B's name:
- the 122B's grid gave "generation";
- gemma-2-9b's grid gave "size";
- the 122B's grid with gemma-2-9b's team cells gave "mixed";
- a grid with the wrong prompt tokens failed rule 1, and nothing was read.

## Prediction, stated before the run

- **Rule 1:** it passes.
- **The verdict:** generation, with all three markers like the 122B.
  - **M1 at most 0.82.** Talk does not bring the 9B the corpus's near-full
    cooperation.
  - **M2 at most 0.12.** Without real talk, it defects.
  - **M3 at least 0.53.** The team frame works in its system prompt and fails
    in its messages. This is the least certain of the three.
- **The basis.**
  - The smoke run: in its two rounds, every agent defected.
  - The 122B's pattern reads as a trained policy, not as an effect of size:
    defection by default, frames acting only through the system prompt.

## Seen before writing

- Every grid number of the 122B and of the corpus, as in the tables above.
- The 9B's smoke run: one run of two rounds, `forecast_probe` on the star.
  - All four agents played Defect in both rounds, and three of the four said
    so in round 1.
  - One forecast of sixteen gave the probability of defection instead of
    cooperation.
- The 9B's latency on 2026-11-06:
  - 71.5 s per call during the smoke run (13:28-14:06);
  - 0.1 s per call later the same day, with four parallel calls taking
    0.7-0.8 s.

No grid run of the 9B existed when this was written.

## Limits fixed in advance

- **Scope.** One model on each side, five runs per cell, runs that are all or
  nothing.
  - One flipped run moves a cell by about 0.2.
  - The markers average 15 runs (M1), 45 (M2) and 20 (M3).
- **The engine.** The corpus ran with transformers on Kaggle, in 4-bit. The
  122B and the 9B run with vLLM on the lab server, at the precision it serves.
  - "Like the corpus" cannot come from the engine, since the 9B shares the
    122B's engine.
  - "Like the 122B" can come from the generation or from the engine. Only a
    corpus model on the lab server could tell them apart, and none is served.
- **The output cap:** 4096 here and for the 122B, against 160-512 for the
  corpus models. For the 122B the cap moved only the invalid rate, not
  cooperation.
- **Size here means total parameters.** The two Qwen3.5 models have about the
  same active parameters.
- **One family.** The question is asked within Qwen3.5, not across families.
- **Server load.** The latency varies with the server's other users. Each
  session's `_progress.json` records the seconds per run, and nothing in the
  protocol depends on them.

## Next, not covered by these rules

- **The two private-forecast cells for the 9B** (`forecast_probe`,
  `framing_team_probe`). They get their own short plan once the grid is read.
  They need a check that a forecast is not given as the probability of
  defection.
- **Qwen/Qwen3.8-27B-FP8,** as a third point, after its own smoke run. It
  changes the generation and the precision at once.

## Reproduce

From `cheaptalk_bench`, in three lanes side by side, one per topology. Each
lane runs sessions A, B and C in turn:

```
python campaign.py --provider pharos --model Qwen/Qwen3.5-9B --session A --topology star --n-runs 5 --n-rounds 16 --max-new-tokens 4096 --out-root ..\pharos_runs\tok4096\grid --zip-mirror=
# then --session B and --session C; the ring: --topology cycle --topology-aware-comm-prompt; the clique: --topology clique --topology-aware-comm-prompt
python verify_prompts.py ..\pharos_runs\tok4096\grid\Qwen3.5-9B ..\pharos_runs\tok4096\grid\Qwen3.5-9B_cycle_commfix ..\pharos_runs\tok4096\grid\Qwen3.5-9B_clique_commfix
python audit_corpus.py ..\pharos_runs\tok4096\grid\Qwen3.5-9B ..\pharos_runs\tok4096\grid\Qwen3.5-9B_cycle_commfix ..\pharos_runs\tok4096\grid\Qwen3.5-9B_clique_commfix
python scale_report.py --roots ..\star_runs\Llama-3.1-8B-Instruct_star ..\star_runs\Qwen2.5-7B-Instruct_star ..\star_runs\Qwen3-4B_star ..\star_runs\gemma-2-2b-it_star ..\star_runs\gemma-2-9b-it_star ..\cycle_runs\Llama-3.1-8B-Instruct_cycle_commfix ..\cycle_runs\Qwen2.5-7B-Instruct_cycle_commfix ..\cycle_runs\Qwen3-4B_cycle_commfix ..\cycle_runs\gemma-2-2b-it_cycle_commfix ..\cycle_runs\gemma-2-9b-it_cycle_commfix ..\clique_runs\Llama-3.1-8B-Instruct_clique ..\clique_runs\Qwen2.5-7B-Instruct_clique ..\clique_runs\Qwen3-4B_clique ..\clique_runs\gemma-2-2b-it_clique ..\clique_runs\gemma-2-9b-it_clique ..\pharos_runs\tok4096\grid\Qwen3.5-122B-A10B ..\pharos_runs\tok4096\grid\Qwen3.5-122B-A10B_cycle_commfix ..\pharos_runs\tok4096\grid\Qwen3.5-122B-A10B_clique_commfix ..\pharos_runs\tok4096\grid\Qwen3.5-9B ..\pharos_runs\tok4096\grid\Qwen3.5-9B_cycle_commfix ..\pharos_runs\tok4096\grid\Qwen3.5-9B_clique_commfix
```

The references above come from exactly these trees. Do not add
`star_runs/gemma-2-2b-it_star_commfix` or `cycle_runs/<model>_cycle`, which
has the old prompt.

## Results, 2026-11-07

Read on 2026-11-07 after all 420 runs. Every reading is exploratory, as fixed
above.

**Runs and checks.**
- **When and on what.** The 420 runs ran from 2026-11-06 19:20 to 2026-11-07
  06:32, on `cfdcf95`. That commit holds this plan and was pushed at 15:53 on
  11-06.
  - Three lanes ran in parallel, one per topology, each running sessions A, B
    and C in turn.
  - A lane took 11.0-11.2 h, and a session 2.8-4.9 h.
  - That is 2.6-3.1 s per call, a little faster than the 122B's 3.0-4.9.
- **The trees.** Each tree has 140 runs of 16 rounds, with no duplicate.
- **The configs.** Every config field equals the 122B's for the same cell,
  apart from three:
  - the model id;
  - the output folder;
  - the `forecast_probe` switch. The code added it on 11-04, after the 122B's
    grid ran, and here it is off.
- **Cuts.** 70 of 42,240 calls were cut at the output cap:
  - 37 action calls, which left invalid decisions;
  - 33 message calls: 31 left an empty message and 2 parsed anyway.

  No reply contains a `<think>` block.

### Rule 1: it passes in substance; its wording did not foresee four flags

| topology | invalid decisions | round-1 tokens, 9B | 122B |
|---|---|---|---|
| star | 29/8,960 = 0.003 | 463, 464 | 463, 464 |
| ring | 22/8,960 = 0.002 | 461, 462 | 461, 462 |
| clique | 17/8,960 = 0.002 | 436, 437 | 436, 437 |

The two token values are the Stag Hunt and the Prisoner's Dilemma prompts.

- `audit_corpus.py` finds no issue, no duplicate history and no cell above 10%
  invalid.
- **`verify_prompts.py` rebuilt 69,120 prompts and flags 4 runs for "horizon
  leak".** Every hit is in an agent's own message:

| run | round | the words |
|---|---|---|
| star, SH `counterfactual`, run 4 | 16 | "we would extend our streak to 16 rounds of maximum mutual payoffs" |
| star, PD `framing_competitive`, run 4 | 16 | "This is the final round of supremacy" |
| ring, SH `framing_competitive`, run 2 | 3 | "This is the final round of contention" |
| clique, PD `framing_team_context[cheap_talk]`, run 1 | 7-15 | "our maximum collective payoff of 16", in 11 messages |

- **What the words are.**
  - The first counts the rounds so far: every prompt states the current
    round.
  - The second and third are competitive rhetoric. One comes in round 3.
  - The fourth counts points.
- **The masked copies are clean.** In copies of the four runs, these phrases
  were masked in the agents' messages: as sent, as composed, and as each
  receiver saw them. The copies give no problem in 768 rebuilt prompts. No
  prompt revealed the horizon.
- **The rule's wording did not foresee this.**
  - It says "`verify_prompts.py` finds nothing", and read literally it fails.
  - It should have foreseen it. The 122B's grid had two such runs ("sixteen
    flawless rounds"), and HANDOFF lists the case as a known false positive.
  - Rule 1 is read here as passing in substance. A reader who holds to the
    letter should read what follows as conditional on that.
- **A wording fix in `scale_report.py`.** It printed "passes, with
  verify_prompts.py and audit_corpus.py clean", although it runs neither. The
  line now says that its own two checks pass and that rule 1 also needs the
  other two. No number changes.

### Rules 2 and 3: the verdict is generation

| marker | 9B | 122B (L) | corpus | midpoint | reading |
|---|---|---|---|---|---|
| M1 talk | 0.03 | 0.71 | 0.93-1.00 | 0.82 | like the 122B |
| M2 no channel | 0.03 | 0.00 | 0.23-0.60 | 0.12 | like the 122B |
| M3 frame gap | 0.33 | 0.74 | 0.00-0.32 | 0.53 | between |

**Two markers read "like the 122B" and none "like the corpus". The verdict is
generation.**

Two things the rule does not show:
- **M3 reads "between" by a margin of 0.007.**
  - Unrounded, the 9B's M3 is 0.3251. The corpus top, Llama-3.1-8B's, is
    0.3180.
  - That is about five decisions of the 1,280 behind the 9B's M3. One flipped
    run moves M3 by about 0.1.
  - Had M3 read "like the corpus", the verdict would have been "mixed".
- **M1 reads "like the 122B" by direction only.** The rule asks on which side
  of the midpoint the 9B falls. At 0.03, it falls far past the 122B, 0.68 below
  it.

### Rule 4, descriptive: the 9B's grid

Mean of run means over valid decisions, n = 5 per cell:

| cell | PD star | PD ring | PD clique | SH star | SH ring | SH clique |
|---|---|---|---|---|---|---|
| `no_comm` | 0.12 | 0.07 | 0.07 | 0.99 | 0.98 | 0.98 |
| `baseline_cheap_talk` | 0.02 | 0.05 | 0.01 | 0.81 | 0.98 | 0.97 |
| `no_sense` | 0.00 | 0.00 | 0.00 | 0.08 | 0.16 | 0.08 |
| `silence` | 0.00 | 0.01 | 0.00 | 0.19 | 0.31 | 0.13 |
| `counterfactual` | 0.01 | 0.03 | 0.04 | 0.95 | 0.96 | 0.98 |
| `framing_business` | 0.03 | 0.11 | 0.07 | 0.99 | 0.98 | 1.00 |
| `framing_team` | 0.03 | 0.05 | 0.03 | 1.00 | 1.00 | 1.00 |
| `framing_competitive` | 0.00 | 0.00 | 0.00 | 0.62 | 0.92 | 0.86 |
| `framing_business_context[no_comm]` | 0.21 | 0.16 | 0.14 | 0.85 | 0.99 | 1.00 |
| `framing_business_context[cheap_talk]` | 0.08 | 0.19 | 0.15 | 0.97 | 0.96 | 1.00 |
| `framing_team_context[no_comm]` | 0.84 | 0.54 | 0.91 | 0.99 | 1.00 | 1.00 |
| `framing_team_context[cheap_talk]` | 0.35 | 0.49 | 0.35 | 0.95 | 1.00 | 1.00 |
| `framing_competitive_context[no_comm]` | 0.06 | 0.03 | 0.03 | 0.73 | 0.93 | 0.91 |
| `framing_competitive_context[cheap_talk]` | 0.02 | 0.00 | 0.01 | 0.90 | 0.90 | 0.93 |

- **In the PD, talk never brings the 9B cooperation, and often takes it
  away.**
  - Ordinary talk gives 0.02, 0.05 and 0.01, below `no_comm` (0.12, 0.07,
    0.07).
  - With the team frame in the system prompt: 0.84, 0.54 and 0.91 without
    talk, but 0.35, 0.49 and 0.35 with it.
- **Its talk is honest defection.** The table reads the PD
  `baseline_cheap_talk` messages with the promise detector, so it is
  descriptive. The detector agreed with a reading by eye on 10 sampled 9B
  messages.

| PD `baseline_cheap_talk` | decisions | cooperate | promise | promise, then Defect | no promise, then Defect | round 1: cooperate, promise |
|---|---|---|---|---|---|---|
| 9B | 957 | 24 | 177 | 163 | 770 | 1/60, 20/60 |
| 122B | 958 | 678 | 761 | 123 | 157 | 40/60, 57/60 |

  - It promises in 177 decisions and breaks 163 of those promises (0.92).
  - Typical messages:
    - "I will Defect this round. Do not trust my words; I will not
      Cooperate."
    - "I will Defect because there is no history to build trust and it is my
      dominant strategy."
    - "I will defect this round as there is no binding mechanism to enforce
      cooperation."
- **Under the team frame in the messages, it promises and defects.**
  - It promises in 935 of 959 decisions and breaks 903 of those promises
    (0.97). The 122B breaks 522 of 949 (0.55).
  - These are the "empty words" of the team-frame cell
    (`docs/forecast_team_plan.md`), at their extreme.
- **Why M3 is low.** The frame works; the 9B's talk erodes it.
  - With the team frame in the system prompt and talk, the 9B cooperates 0.85
    in round 1 but 0.40 over the run.
  - Without talk, the frame holds (0.54-0.91).
- **The Stag Hunt, outside the rules.** An open channel left empty, or filled
  with noise, collapses Stag Hunt cooperation in both Qwen3.5 models.
  - `silence` and `no_sense` give 0.08-0.31 for the 9B and 0.00-0.01 for the
    122B.
  - Every corpus model has at least 0.37 in these cells.
  - With no channel at all, the 9B cooperates 0.98-0.99.

### The prediction against the result

- **Rule 1,** it passes: yes in substance, not to the letter (above).
- **The verdict,** generation: yes.
- **M1 at most 0.82:** yes, 0.03. That it would fall 0.68 below the 122B was
  not predicted.
- **M2 at most 0.12:** yes, 0.03.
- **M3 at least 0.53:** no, 0.33, "between". It was the least certain of the
  three.

### In words

- **By the rule, the 122B's departures from the corpus come with Qwen3.5, not
  with the total number of parameters.**
  - They are defection without real talk, and a frame that acts only from the
    system prompt.
  - Whether they come from the generation or from the engine cannot be told
    apart here (see the limits).
- **But the 9B is not a small 122B.** In the PD, talk brings the 122B 0.71
  and the 9B nothing. The 9B says that it will defect, and it does. Within
  the generation, what talk achieves changes with size.
- **The verdict is thin.** It rests on M3 lying 0.007 above the corpus top.

**Limits.**
- The limits fixed above: one model on each side, five runs per cell, and the
  engine.
- M3's margin is far inside the noise of one flipped run. M1 is read by
  direction only.
- The detector is not validated on Qwen3.5, so the talk numbers are
  descriptive.

**Files.** The read-only scripts and their outputs are kept beside the runs,
outside the repo, in `..\pharos_runs\tok4096\grid\analysis_9b\`:
- the census and the timing;
- the horizon search and the masked check;
- the exact markers and the talk counts;
- the outputs of `scale_report.py`, `verify_prompts.py` and
  `audit_corpus.py`.
