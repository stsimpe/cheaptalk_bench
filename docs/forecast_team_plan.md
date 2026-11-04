# Private forecasts under the team frame in the messages

This is the plan for an exploratory follow-up on one model: Qwen3.5-122B-A10B
on the lab server. It was written on 2026-11-04, after the results of the
forecast probe (`docs/forecast_probe_plan.md`) and before any run of this cell.
The reading rules below decide what the results are allowed to say. Committing
this file before the first run fixes them. No earlier cell, plan or rule is
touched.

## Question

What the grid showed for the team frame:
- **In the system prompt** (`framing_team_context`), cooperation is 1.00 on
  every topology.
- **In the messages** (`framing_team`), it is 0.26 on the star, 0.82 on the
  ring and 0.25 on the clique. That is below ordinary talk on the star and on
  the clique.
- **This cell breaks the most promises in the grid:** 233 of 315 on the star
  and 233 of 314 on the clique (0.74), and 56 of 320 on the ring.
- **Its runs are all or nothing.** On the star and on the clique, four runs of
  five collapse to 0.03-0.12 and the fifth stays at 1.00.
- **Forgiveness is gone.** After a neighbour's defection, cooperation is
  0.02-0.05. With ordinary talk it is 0.17, 0.39 and 0.56.
- **The instruction sets only a tone:** "phrase your message in a
  team-cooperative tone ... Use vocabulary like 'team', 'together' ...". So
  the messages come out alike, whoever writes them: "Let's work together as a
  team to support our shared goal of mutual success."

What the forecast probe showed for ordinary talk (2026-11-04):
- **Talk works by changing what the agents expect.** In round 1, the forecast
  of a neighbour who promises rises from 24 to 91.
- **Lies are seen through, mostly from history.** The matched gap is 25.3, or
  27.0 with the hand check.
- **Forgiveness follows belief.**
  - A defector's new promise raises its forecast by +31.6 points, to 44.7.
  - An agent that believes the defector cooperates again 64% of the time,
    against 16% when it does not.

So the frame in the messages can fail in two ways:
- **Disbelief.** The receivers discount team talk, so it never builds trust.
- **Empty words.** Team talk is believed, but it carries no information.
  - A liar writes the same words as a cooperator, so its lies pass.
  - After a betrayal the defector has no words left that could repair it.

This plan asks four things:
1. Is team talk believed?
2. Are its broken promises seen through?
3. After a betrayal, does the defector's new team message restore belief?
4. Does the sender mean its team talk?

## Design

- **As in the forecast probe, with its addendum.**
  - The grid of four: the star with the original prompt; the ring and the
    clique with the corrected routing prompt.
  - Prisoner's Dilemma, 16 rounds, hidden horizon, memory 10, T = 0.7, output
    cap 4096.
  - The same two private forecast calls, read by the same parser.
- **The change.** The messages carry the team frame of `framing_team`
  (scenario `framing_team_probe`, session `PROBE_TEAM`).
  - The system prompt, the message prompt with its frame, and the action prompt
    are `framing_team`'s, byte for byte.
  - The forecast prompts are the probe's. They carry no frame.
  - An offline run with a stub server checked this on the three topologies.
- **Size.** 5 runs per topology, 15 runs, written to `tok4096/probe_team`.
- **References,** with the same model, server and cap:

| topology | `framing_team` cooperation (runs) | broken promises | cooperation after a neighbour's D | round-1 message prompt tokens | `framing_team_context[cheap_talk]` |
|---|---|---|---|---|---|
| star | 0.26 (0.11, 0.03, 0.09, 0.06, 1.00) | 233/315 | 0.02 | 516 | 1.00 |
| ring | 0.82 (1.00, 1.00, 1.00, 1.00, 0.12) | 56/320 | 0.05 | 514 | 0.99 |
| clique | 0.25 (0.12, 0.06, 0.05, 0.03, 1.00) | 233/314 | 0.03 | 489 | 1.00 |

From the forecast probe, with ordinary talk:
- round 1, the forecast after a promise: 91.3;
- the matched gap: 25.3;
- a defector's new promise: shift +31.6. A message from a defector that does
  not promise: shift +13.9;
- messages that promise: 0.86;
- L: 0.64;
- P: 0.94.

## Definitions

As in the forecast probe plan: forecast, shift, promise, kept and broken
promise, intention before and after, P, L and the matched gap.

- **Repair:** the shift of i's forecast of j, when j defected the round before
  and j's new message promises.

## Reading rules

Every reading is exploratory: one model, five runs per topology, and runs that
are all or nothing.

**The hand check comes before rules 3 and 5.**
- Under the frame, the detector reads nearly every message as a promise: 949
  of 960 in the grid cell.
- A random sample of the messages whose sender then defected is read by hand:
  50 per topology, or all of them where there are fewer. The reading is the
  strict one of the forecast probe.
- If the detector disagrees with the hand on more than 10% of the sample, every
  such message is read, and rules 3 and 5 are given both ways.

1. **Compliance and the untouched game, read first.** This is rule 1 of the
   forecast probe plan, against `framing_team`:
   - at least 90% of forecast calls valid, before and after, pooled and on
     every topology;
   - `verify_prompts.py` finds nothing;
   - the round-1 message prompt tokens equal `framing_team`'s: 516, 514 and
     489.

   Cooperation is reported against the grid cell. It is not a gate. If rule 1
   fails, nothing else is read.
2. **Is team talk believed?** In round 1, the mean forecast after a promise is
   set against ordinary talk's 91.3. That cell's tree is given to the same
   report.
   - Within 10 points: "team talk is believed as ordinary talk".
   - 20 or more points below: "team talk is discounted".
   - In between: "partly".
3. **Are its lies seen?** The matched gap of this cell, read with at least 20
   broken promises.
   - Below 10: "lies are believed as much as kept promises".
   - 25 or more: "lies are seen through".
   - In between: "partly".
   - Reported beside it: the ordinary cell's gap, the share of broken promises
     believed (forecast after >= 50), and how often their receivers
     cooperated.
4. **Does team talk repair a betrayal?** The mean repair shift.
   - Below +15, no more than a message without a promise gave in ordinary
     talk (+13.9): "team talk does not repair".
   - +25 or more: "team talk repairs as ordinary talk does". Ordinary talk
     gave +31.6.
   - In between: "partly".
   - Reported beside it: the forecast after, and cooperation by a forecast of
     at least 50 or below it (the probe's rule 5).
5. **Does the sender mean it?** This rule is descriptive: the share of messages
   that promise, L and P, against ordinary talk.

The rules R2-R5 of `forecast_report.py` also run for this cell, and they are
reported as they come out. The reading is the one above, printed as T2-T5.

**In words.**
- If rule 2 says "believed" and rule 4 says "does not repair", the frame fails
  as empty words.
- If rule 2 says "discounted", it fails as disbelief.
- Anything else is mixed.

## Prediction, stated before the run

- **Rule 1:** it passes. Cooperation is within 0.20 of the grid cell on every
  topology; with runs that are all or nothing, one run flipping moves a cell
  by about 0.2.
- **Rule 2:** team talk is believed as ordinary talk, within 10 points of 91.3.
  A receiver cannot know that the tone was asked for.
- **Rule 3:** lies are believed as much as kept promises (matched gap below
  10). Identical words carry no warning.
- **Rule 4:** team talk does not repair (shift below +15). After a betrayal,
  the defector writes the same team words it wrote before.
- **Rule 5:** at least 0.95 of the messages promise, so L is at least 0.90. P is
  near ordinary talk's.
- So the frame fails as **empty words**.

## Seen before writing

- The grid's `framing_team` runs: their cooperation and their messages.
- From the same runs, the broken promises and what their receivers did. In
  the grid cell only 59 of 1,160 such receivers cooperated: most broken
  promises fall in runs that have already collapsed.
- Every result of the forecast probe.

No forecast under the team frame existed when this was written.

## Limits fixed in advance

- **Scope.** One model, five runs per topology, Prisoner's Dilemma only.
- **The level of a cell rests on how many runs collapse,** because the runs are
  all or nothing.
- **The comparison crosses two cells.** The ordinary cell ran on 2026-11-04,
  00:42-01:37; this one runs later, on the same server and the same code, but
  not in the same session. The tokens and the cooperation against the grid
  cell check for drift.
- **The limits of the forecast probe hold here too.**
  - The forecasts are stated beliefs, given in separate samples.
  - The forecast after the messages reads every message of the round.
  - A broadcast counts once per receiver.
  - A forecast before near 100 leaves no room to rise.
- **The promises under the frame are formulaic,** and the hand check reads only
  a sample of them.
- **The frame is in the message prompt only.** The forecast calls carry none,
  so the intention before the messages comes from an unframed call, as in the
  ordinary cell.

## Reproduce

From `cheaptalk_bench`:

```
python campaign.py --provider pharos --model Qwen/Qwen3.5-122B-A10B --session PROBE_TEAM --topology star --games pd --n-runs 5 --n-rounds 16 --max-new-tokens 4096 --out-root ..\pharos_runs\tok4096\probe_team --zip-mirror=
python campaign.py --provider pharos --model Qwen/Qwen3.5-122B-A10B --session PROBE_TEAM --topology cycle --topology-aware-comm-prompt --games pd --n-runs 5 --n-rounds 16 --max-new-tokens 4096 --out-root ..\pharos_runs\tok4096\probe_team --zip-mirror=
python campaign.py --provider pharos --model Qwen/Qwen3.5-122B-A10B --session PROBE_TEAM --topology clique --topology-aware-comm-prompt --games pd --n-runs 5 --n-rounds 16 --max-new-tokens 4096 --out-root ..\pharos_runs\tok4096\probe_team --zip-mirror=
python verify_prompts.py ..\pharos_runs\tok4096\probe_team
python audit_corpus.py ..\pharos_runs\tok4096\probe_team
python forecast_report.py --roots ..\pharos_runs\tok4096\grid\Qwen3.5-122B-A10B ..\pharos_runs\tok4096\grid\Qwen3.5-122B-A10B_cycle_commfix ..\pharos_runs\tok4096\grid\Qwen3.5-122B-A10B_clique_commfix ..\pharos_runs\tok4096\intent_control ..\pharos_runs\tok4096\probe ..\pharos_runs\tok4096\probe_team --csv ..\pharos_runs\tok4096\probe_team\forecast_pairs.csv
```

No smoke run is needed. The code path is the forecast probe's, smoke-tested on
2026-11-04, and this cell adds only a scenario. With three cells side by side,
the forecast probe took 10-11 minutes per run, so this cell should take about an
hour.
