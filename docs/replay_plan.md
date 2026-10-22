# Round-1 replay: what part of a hostile message does the harm?

Pre-registration. Written before any replay call; the reading rules below
decide what the results are allowed to say.

## Question

The harm-source cells (star, PD, `framing_competitive`) showed two
independent routes of harm. The **writer's route**: an agent that writes a
hostile message and sees it quoted back ("You just sent the following
message: ...") cooperates less, with nothing delivered (`block_all`). The
**readers' route**: agents that receive hostile messages cooperate less, with
their own message withheld (`hideown`). Neither cell says which part of the
message does it. Three questions:

1. **Writers: the word or the stance?** Does the writer copy the action word
   of its own message ("I will defect" → Defect), or act on the competitive
   stance, which survives without the word?
2. **Attribution.** Does the same text weigh differently when it is the
   agent's own than when a neighbour sent it?
3. **Readers: the word or the intent, and how much?** Does a reader answer the
   action words or the hostile intent, and does the hub's cooperation fall
   with the number of hostile messages it receives (0 to 3 of 3)?

## Why a replay of round 1

Every model call is stateless, and the first round has no history. A recorded
round-1 action call can therefore be rebuilt exactly from its run record and
asked again with one part changed. No game is played, so the edit is the only
difference between variants.

The rebuild was checked against the code that produced the runs: the
round-1 system and user prompts built by the current code are byte-identical
to those built at commit `6c1e71d` (the `block_all` runs, 2026-09-29) and
`537adde` (the `hideown` runs, 2026-10-05), for writers and readers.

## Contexts

From `harm_source/`, five models, five runs each, four agents per run:
**20 contexts per model and route**, extracted once into
`replay/contexts.json` (with the sha1 of each source record).

| context | source cell | own message quoted | received |
|---|---|---|---|
| writer | `<model>_block_all` | its own hostile message | nothing (empty strings) |
| reader | `<model>_hideown` | empty | its neighbours' hostile messages |
| silence | `<model>_block_all_hideown` | empty | nothing (recorded actions only) |

Recorded round-1 cooperation (one decision per context, invalid answers
excluded), the corpus values the replay must reproduce:

| model | writer | reader | silence | writer contexts with an action word | reader contexts with one |
|---|---|---|---|---|---|
| Llama-3.1-8B | 0.25 | 0.55 | 0.75 | 12 | 12 |
| Qwen2.5-7B | 0.40 | 0.55 | 0.60 | 7 | 10 |
| Qwen3-4B | 0.10 | 0.30 | 0.90 | 20 | 20 |
| gemma-2-2b | 0.13 (5 invalid) | 0.36 (6 invalid) | 0.71 (13 invalid) | 0 | 0 |
| gemma-2-9b | 0.40 | 0.25 | 1.00 | 8 | 11 |

## Variants

| variant | own message quoted | received | contexts |
|---|---|---|---|
| W0 | its own, unchanged | as recorded (empty) | writer |
| W1 | its own, **action words deleted** | as recorded | writer |
| W2 | **empty** | as recorded | writer: the silence reference of both routes |
| S1 | empty | **its own text as a neighbour's message** | writer |
| R0 | empty | as recorded (hostile) | reader |
| R1 | empty | **action words deleted** from every message | reader |
| D0, D1, D2 | empty | **0, 1 or 2 of the 3** stay hostile, the rest cooperative | reader, hub only |

- **Action words**: every match of `\b(defect\w*|cooperat\w*)\b`, case
  insensitive, deleted, then spacing tidied. A message without one is left
  character for character, so W1 = W0 there.
- **S1**: the text goes into the slot of the lowest-numbered neighbour (a
  leaf's only partner, the hub; the hub's leaf #1); the other slots stay empty.
- **D0 to D2**: which senders stay hostile and which first-round cooperative
  messages of the same model fill the other slots are drawn per context and
  dose with a fixed seed, without repeating a line in one context. The pool is
  `pools/<model>_cooperative_r1.json` (round 1 of the grid's ordinary-talk
  runs, `signal_rules.is_signal`, not hostile; 7 to 36 lines per model):
  first-round lines, because "let's keep cooperating" would point to a past
  that round 1 does not have. D3 is R0 for the hub.

**Sampling.** 5 calls per context and variant, at the run's own settings
(T = 0.7, its `max_tokens`), each seeded with `torch.manual_seed` from
sha1(run | agent | variant | sample). Per model: 20 writer contexts × 4 + 20
reader contexts × 2 + 5 hubs × 3 doses = 135 context-variants, **675 calls**;
3,375 in all.

## Reading rules

The unit is the **context** and its share of cooperative calls among the
valid ones. A model's rate for a variant is the mean of its context shares.
Within-context contrasts (W1, W2, S1 against W0; W2 against W1; R1 against R0)
use an exact sign-flip test over contexts. Contrasts with the silence
reference for readers (W2 against R0 and R1) compare different contexts and
use a two-sample permutation test. Holm across the five models within each
test; α = 0.05. A variant with more than 15% invalid calls is not read.

1. **Link.** For writers (W0), readers (R0) and silence (W2), the recorded
   round-1 cooperation and the replay do not differ by a two-sided Fisher
   exact test (p ≥ 0.05). Only models where all three hold enter the summary
   counts; the others are reported, marked.
2. **Harm present.** A route is decomposed only where it harms in round 1:
   W2 − W0 ≥ 0.15 (writers), W2 − R0 ≥ 0.15 (readers), each with p < 0.05.
3. **Writers, word or stance**, on the writer contexts whose own message has
   an action word: recovery = (W1 − W0) / (W2 − W0).
   - *copying*: recovery ≥ 0.5 and W1 > W0 (p < 0.05);
   - *stance*: recovery ≤ 0.25 and W2 > W1 (p < 0.05);
   - otherwise *mixed*.
   A model none of whose messages has an action word gets no verdict here:
   its round-1 harm, if present, is shown without any word to copy.
4. **Attribution**: S1 − W0 over all writer contexts, two-sided:
   - |difference| > 0.10 with p < 0.05 gives *own words weigh more* (S1 > W0)
     or *a neighbour's words weigh more* (S1 < W0);
   - otherwise *not shown*.
5. **Readers, word or intent**, on the reader contexts where a received
   message has an action word: recovery = (R1 − R0) / (W2 − R0), with the same
   thresholds, giving *word*, *intent* or *mixed*.
6. **Dose**, hub readers, score = hostile messages of 3 (D0, D1, D2, R0):
   *dose-dependent* when Mantel's stratified trend test (strata = contexts)
   gives a decreasing trend with p < 0.05 and D0 − R0 > 0.10. Otherwise *not
   shown*. The shape (does one hostile message do most of it?) is described,
   not tested.

Descriptive only: the writer harm (W2 − W0) in contexts with and without an
action word, side by side.

`replay_report.py` implements these rules; it was checked on a stub model
built to copy its own action word and to read intent, and it returned
*copying*, *intent* and *dose-dependent* for it.

## Predictions, stated before the replay

- Writers: *stance*. The lexicon filters of RQ4 already showed that hostility
  is not lexically bounded, and gemma-2-2b harms in round 1 with no action
  word in any of its messages.
- Readers: *intent*, for the same reason.
- Attribution: no prediction.
- Dose: dose-dependent.

## Limits fixed in advance

- Round 1 only. In later rounds the harm also travels through the history of
  actions, which a replay of round 1 does not touch.
- Deleting a word can leave a broken sentence ("I will to secure an
  advantage"). A broken sentence is still a change of form; *stance* means
  the harm survives it.
- gemma-2-2b answers many first-round action calls with a message instead of
  an action when its own quoted message is empty (13 of the 20 recorded
  silence contexts). The 15% rule will probably keep its W2, and with it both
  routes, from being read. Its numbers are reported as they come.
- Qwen2.5's recorded reader harm is small (0.05); "no round-1 harm" is a
  likely and acceptable outcome for its reader route.
- 20 contexts per model and route, 7 to 20 of them with an action word: a
  *mixed* or *not shown* verdict means "not shown", not "absent".

## Cost

675 calls per model; one Kaggle session with two models in parallel, about
4 hours from the measured seconds per action call. Measured times will
replace the estimate.
