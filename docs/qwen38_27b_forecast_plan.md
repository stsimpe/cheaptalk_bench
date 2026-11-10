# Private forecasts for Qwen3.8-27B: what a cooperator expects

This is the plan for an exploratory follow-up on one model:
Qwen/Qwen3.8-27B-FP8 on the lab server. It was written on 2026-11-10, after
the 27B's grid (`docs/qwen38_27b_plan.md`), which named these two cells as its
next step. No forecast run of the 27B existed then, apart from its three smoke
runs. The reading rules below decide what the results are allowed to say.
Committing this file before the first run fixes them. No earlier cell, plan or
rule is touched, and nothing in the code changes.

## Question

What the 27B's grid showed in the Prisoner's Dilemma (read on 2026-11-10):
- **It plays as the corpus** on all three markers of its plan. Ordinary talk
  gives 1.00 on every topology. Without talk it still cooperates in part
  (0.35).
- **It keeps its word.** In the baseline it promises in 957 of 960 decisions
  and breaks one promise.
- **Its broken promises sit in one cell:** the team frame in the messages, on
  the star (0.62).
  - Two of the five runs collapse after a leaf defects in round 1, and a
    third falls to 0.81.
  - On the ring and the clique the cell is 1.00.
  - 110 of the cell's 948 promises are broken, all of them on the star.

The forecast cells of the two Qwen3.5 models found two things that the 27B
can now be set against:
- **Before any talk,** both intended to defect in every round-1 call. They
  forecast 24 (122B) and 11.2 (9B) for their neighbours.
- **The 122B's actions follow its beliefs and the 9B's do not.** When its
  mean forecast is 50 or more, the 122B cooperates 0.93 of the time and the
  9B 0.12.

This plan runs the same two cells with the 27B and asks four things:
1. What does it intend and expect before any talk?
2. Does a promise move its forecast of the sender, from a forecast that
   already starts high?
3. Do its actions follow its beliefs?
4. Where it does break promises, under the team frame, did it intend the
   defection before the talk? Does it say so? Is its team talk believed?

## Design

- **The two cells of the 122B and the 9B, unchanged, with the 27B:**
  `forecast_probe` (session `PROBE`) and `framing_team_probe` (session
  `PROBE_TEAM`).
  - The star has the original prompt. The ring and the clique have the
    corrected routing prompt.
  - Prisoner's Dilemma, 16 rounds, hidden horizon, memory 10, T = 0.7, output
    cap 4096.
  - 5 runs per topology and cell: 30 runs.
  - The same two private forecast calls, read by the same parser.
- **Placement.** The runs go to `tok4096/probe_27b` and
  `tok4096/probe_team_27b`. The trees are `Qwen3.8-27B-FP8`,
  `Qwen3.8-27B-FP8_cycle_commfix` and `Qwen3.8-27B-FP8_clique_commfix`.
- **References:** the 27B's grid cells, with the same server and cap.

| 27B grid cell | cooperation (star / ring / clique) | promises | broken | round-1 message prompt tokens |
|---|---|---|---|---|
| `baseline_cheap_talk` | 1.00 / 1.00 / 1.00 | 957 of 960 decisions | 1 | 464 / 462 / 437 |
| `framing_team` | 0.62 / 1.00 / 1.00 | 948 of 960 | 110 | 516 / 514 / 489 |

- **Promise pairs** count one per receiver, as `forecast_report.py` forms them.
  - In the baseline: 2,074 kept and 1 broken. 129 of them come in round 1.
  - Under the team frame: 1,896 kept and 162 broken, every broken pair on the
    star. 130 of them come in round 1.
- **From the Qwen3.5 models' forecast cells** (their plans' results; ordinary
  cell unless named):

| | 122B | 9B |
|---|---|---|
| round 1 before the talk: intend to defect; mean forecast | 60 of 60; 24 | 60 of 60; 11.2 |
| round 1: the forecast after a promise (shift) | 91.3 (+67.6) | 48.1 (+34.8) |
| P; L | 0.94; 0.64 | 0.96; 0.21 |
| a defector's new promise (repair) | +31.6 | +20.4 |
| team cell: round-1 forecast after a promise; repair | 82.9; +2.6 | 73.8; +2.0 |
| cooperates when its mean forecast after is >= 50; < 50 | 0.93; 0.15 | 0.12; 0.03 |

## Definitions and hand checks

The definitions are those of the 9B's forecast plan
(`docs/qwen35_9b_forecast_plan.md`):
- forecast, shift, promise, kept and broken promise;
- intention before and after, P and L;
- repair;
- announced defection, with its pattern unchanged;
- the matched gap with 10-point bands;
- inverted forecasts.

Its three hand checks are read the same way, blind, with the same seeds. There
is one change: where fewer messages or calls exist than a sample asks for, all
of them are read.
- **Promises in the ordinary cell:** every message of a defecting sender that
  the detector reads as a promise, and a random 100 of those it does not
  (seed 7).
- **Promises in the team cell:** a random 50 messages of defecting senders per
  topology (seed 11).
- **Inverted forecasts:**
  - every forecast call after the messages that gives at least 50 to a
    neighbour whose message that round is an announced defection (a random
    100 of them if there are more, seed 13);
  - a random 100 of the other forecast calls, 50 before the messages and 50
    after them (seed 13).

The hand classes and the strict reading (U + K) are the forecast probe's. Each
sheet shows the text only, shuffled, and its key is kept apart.

## Reading rules

Every reading is exploratory: one model and five runs per topology. Rules 1-6
are the 9B forecast plan's, with the 27B in the 9B's place. The changes are
stated below; rule 7 is new.

1. **Compliance and the untouched game, read first,** against the 27B's grid:
   - at least 90% of forecast calls are valid, before and after, pooled and on
     every topology;
   - at most 5 calls of the random 100 are inverted;
   - `verify_prompts.py` finds nothing, or every hit is in an agent's own
     words. That is shown as for the grids, with `horizon_hits.py` and
     `mask_horizon.py`;
   - the round-1 message prompt tokens equal the 27B grid's: 464 / 462 / 437
     for `forecast_probe`, and 516 / 514 / 489 for `framing_team_probe`.

   Cooperation is reported against the 27B's grid; it is not a gate. If rule 1
   fails, nothing else is read.
2. **Does a promise move the forecast?** Unchanged: the mean round-1 shift
   after a promise, over at least 20 pairs.
   - +25 or more: "promises are believed".
   - Below +10: "promises are discounted".
   - In between: "partly".
   - Reported beside it: the forecasts before and after, all rounds, and the
     shift after an announced defection.
3. **Are broken promises believed?** Unchanged: the matched gap with 10-point
   bands in the ordinary cell. It needs at least 20 kept and 20 broken
   promises in bands that hold both; otherwise "too few to read".
4. **Premeditation and honesty.** The thresholds are unchanged. P and L are
   read in each cell that has at least 20 broken promises, not in the ordinary
   cell alone.
   - In the ordinary cell, the count is the hand's (strict).
   - In the team cell, only a sample is read by hand. The detector's count is
     used if the hand agrees with it on at least 90% of the sample. Otherwise
     every message is read, as the team plan says, and the hand's count is
     used.
5. **Descriptive, not rules.** As in the 9B plan: before the talk in round 1,
   forgiveness and calibration. One addition:
   - every defection in round 1, in both cells, with the sender's intention
     before and after the talk and its message. This shows whether the first
     defection of a run was planned before the talk or decided after the
     messages.
6. **The team frame (T2 and T4),** with one addition: T4 needs at least 20
   pairs of a defector's new promise; otherwise "too few to read". T3 and T5
   are reported as `forecast_report.py` prints them; rule 4 reads the team
   cell's P and L.
7. **New: belief and action.**
   - **The decisions.** Each probe decision with a valid action and at least
     one valid forecast after the messages. Its belief is the mean of its
     forecasts of its neighbours, after the messages.
   - **What is compared.** Cooperation when that mean is 50 or more, against
     cooperation when it is below 50, on the two cells pooled. Each side needs
     at least 20 decisions; otherwise "too few to read".
   - **The reading:**
     - a difference of 0.50 or more: "its actions follow its beliefs";
     - below 0.20: "its actions ignore its beliefs";
     - in between: "partly".
   - **Reported beside it:** each cell alone, and the Qwen3.5 models' values:
     122B 0.93 / 0.15 (ordinary) and 0.75 / 0.03 (team); 9B 0.12 / 0.03 and
     0.12 / 0.02.
   - The 9B's results showed this split after its run. It is fixed here
     before the 27B's.

**How the numbers are computed.**
- `forecast_report.py` prints rules 1-5 and T2-T5, with the 27B's grid and
  forecast trees as roots. Where its verdict lines differ from the rules
  above, the rules above are read, and its lines are reported as printed.
- The hand checks, the inversion check, the 10-band gap, rule 7 and the
  descriptive splits are computed by read-only scripts kept beside the runs,
  as for the 9B (`pharos_runs/tok4096/probe_9b/analysis/`).

## Prediction, stated before the run

- **Rule 1** passes:
  - forecasts valid at 90% or more;
  - at most 5 of the random 100 inverted;
  - tokens equal;
  - cooperation within 0.20 of the grid on every topology. The exception may
    be the team cell on the star, whose runs in the grid were all or nothing
    (1.00, 0.81, 1.00, 0.16, 0.12).
- **Before the talk in round 1,** at least 75% of the intentions are Cooperate,
  and the mean forecast is between 40 and 75. That is the opposite of both
  Qwen3.5 models.
- **Rule 2:** "promises are believed", a round-1 shift of +25 or more. The risk
  is the ceiling: the forecasts start at 50-75.
- **Rule 3:** too few to read. The grid had 1 broken promise pair in the
  ordinary cell.
- **Rule 4:**
  - the ordinary cell: too few to read;
  - the team cell, if it has 20 broken promises: P 0.50 or more ("mostly
    premeditated") and L 0.50 or more ("it mostly hides it behind a
    promise"). After a collapse, the team talk goes on while the agent
    defects.
- **T2:** believed as ordinary talk. **T4:** does not repair, if readable.
- **Rule 7:** its actions follow its beliefs, as the 122B's do. If the team
  cell does not collapse, the side below 50 may have too few decisions.
- **The basis:**
  - In the three smoke runs, all 12 agents intended to cooperate before the
    talk in round 1, with forecasts of 50-75 (mean 57.5).
  - After the messages the forecasts rose to 85-95, apart from one that
    stayed at 60. The round-1 shift was +30.3 over 18 pairs.
  - In the grid, ordinary talk was kept almost always, and the team frame
    broke down only on the star.

## Seen before writing

- Every number of the 27B's grid and its messages, including a hand check of
  50 of them (2026-11-10).
- The 27B's three smoke runs of `forecast_probe` on the star, on 2026-11-09 at
  13:44, 22:06 and 23:00: every forecast, intention and message.
  - The third repeated the second command into the same folder.
  - It was found after the grid plan was committed. It passes the same four
    checks.
- Every result of the two Qwen3.5 models' forecast cells.

No forecast of the 27B existed when this was written, apart from the smoke
runs'.

## Limits fixed in advance

- **Scope.** One model, five runs per topology, Prisoner's Dilemma only.
- **Few broken promises.** The 27B almost never breaks a promise in ordinary
  talk, so rules 3 and 4 are likely unreadable there. Under the team frame,
  the broken promises depend on how many star runs collapse.
- **The ceiling.** Its forecasts start at 50-75. A promise has less room to
  move them than for the Qwen3.5 models, whose forecasts started at 11-24.
- **Stated beliefs.** The forecasts are beliefs stated in separate calls.
  Nothing rewards their accuracy.
- **The inversion check reads reasoning.** A call whose reasoning is ambiguous
  counts as not inverted.
- **The detector** is not validated on these models. In the grid's hand check
  it agreed on 49 of 50 messages; the miss was a team message ("...and victory
  together").
- **Server updates,** as in the grid plan:
  - if an update stops the runs, a new smoke run comes before any further
    run;
  - a cell cut short keeps its runs if it has at least 4 of 5; otherwise it is
    run again whole;
  - the write-up names every cell that ran after an update.

## Reproduce

From `cheaptalk_bench`, in three lanes side by side, one per topology. Each
lane runs `PROBE`, then `PROBE_TEAM`:

```
python campaign.py --provider pharos --model Qwen/Qwen3.8-27B-FP8 --session PROBE --topology star --games pd --n-runs 5 --n-rounds 16 --max-new-tokens 4096 --out-root ..\pharos_runs\tok4096\probe_27b --zip-mirror=
python campaign.py --provider pharos --model Qwen/Qwen3.8-27B-FP8 --session PROBE_TEAM --topology star --games pd --n-runs 5 --n-rounds 16 --max-new-tokens 4096 --out-root ..\pharos_runs\tok4096\probe_team_27b --zip-mirror=
# the ring: --topology cycle --topology-aware-comm-prompt; the clique: --topology clique --topology-aware-comm-prompt
```

Then the checks and the report:

```
python verify_prompts.py ..\pharos_runs\tok4096\probe_27b ..\pharos_runs\tok4096\probe_team_27b
python audit_corpus.py ..\pharos_runs\tok4096\probe_27b ..\pharos_runs\tok4096\probe_team_27b
python forecast_report.py --roots ..\pharos_runs\tok4096\grid\Qwen3.8-27B-FP8 ..\pharos_runs\tok4096\grid\Qwen3.8-27B-FP8_cycle_commfix ..\pharos_runs\tok4096\grid\Qwen3.8-27B-FP8_clique_commfix ..\pharos_runs\tok4096\probe_27b ..\pharos_runs\tok4096\probe_team_27b
```

**Timing.** The 27B's grid ran at 1.6-2.1 s per call with three lanes. A
forecast run has 256 calls, so it should take 7-9 minutes, and a lane about
1.2-1.5 hours for its 10 runs. Measure the first runs before relying on this.
