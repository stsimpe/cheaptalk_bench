# Silent topology: is the star's deficit in the description or in the experience?

Pre-registration. Written before any run; the reading rule below decides what
the results are allowed to say.

## Question

Every agent in the corpus is told its network ("one of 4 agents arranged in a
star network ... You have 1 neighbor") and how messages are routed. In the
three low-communication Prisoner's Dilemma cells (`no_comm`, `silence`,
`no_sense`) the star cooperates least: the ring is above it in 13 of the 15
model-cell pairs (sign test p = 0.007). Two readings explain that:

- **Experience** (ours): a star leaf has a single partner, so one defector is
  all it observes.
- **Description** (El Mir et al. 2026): topology mattered in their study only
  when agents were told whom they could hear; the disclosure makes agents
  reason about the peers they cannot hear.

The test: the same routing, with the prompt saying nothing about the network.
An agent still sees in its history how many partners it has ("Neighbor #k
chose ..."): experience stays, description goes.

## Design

- **Prompt.** `--silent-topology` replaces the topology paragraph with "You
  interact with other agents in a network. Each round, every agent chooses one
  action that is applied in the pairwise game with each agent it is connected
  to. Your payoff in a round is the sum of these pairwise payoffs." and the
  routing sentence with "each agent sends a single message that reaches the
  agents it is connected to, and no one else". Both arms are affected; the
  cell labels carry a `+silent` tag on both, and the anchor is `no_comm+silent`.
- **Cells.** `no_comm`, `silence`, `no_sense`: the cells where topology moved
  cooperation in the corpus. Ordinary talk is at the ceiling on every
  topology, so it cannot show a deficit and is not run.
- **Networks.** Star and ring, four agents, measured side by side: in every
  session one card runs a model on the star and the other the same model on
  the ring, at the same time, on the same machine and software. The silent
  star-versus-ring comparison carries no period confound.
- **Models.** The five of the corpus. 5 runs per cell; PD, 16 rounds, hidden
  horizon, memory 10, T = 0.7, the corpus token budgets (session A values).
- **Size.** 2 networks x 3 cells x 5 models x 5 runs = 150 runs.

## Reading rule

Over the 15 model-cell pairs under the silent prompt, let k be the number of
pairs where the ring's mean cooperation is above the star's and m the number
where it is below (ties are dropped from the test).

- *The star's deficit survives silence* when k >= 12 and the two-sided sign
  test on (k, k + m) gives p < 0.05. Experience carries the effect.
- *The deficit vanishes* when k <= 9. Description carries it.
- Otherwise *inconclusive*.
- The rule is read only on the complete set of 15 pairs; with a model or a
  cell missing it is not read (the thresholds are counts out of 15).

Secondary: the share of runs ending in the cooperative state (last five
rounds >= 0.5), ring against star, by Fisher exact test. Descriptive only: the
silent cells next to the announced ones, which were measured in another
period (the A/A noise floor of a five-run star comparison is about 0.2 to 0.3
per model).

The rule applied to the announced corpus (grid star, corrected-prompt ring)
gives k = 13, m = 2, p = 0.007, which is the number in the report; the code
that reads the silent runs is the code that reproduced it.

## Prediction, stated before the runs

The experience reading predicts that the deficit survives (k >= 12).

## Limits fixed in advance

- El Mir et al. ran a unanimity Stag Hunt, and their announced condition also
  added a prompt to suspicion; this tests only the disclosure, in the PD.
- The silent text still says "network" and "connected": agents know there is
  a network, only not its form or size.
- Five runs per cell; an inconclusive result is "not shown", not "absent".

## Cost

64 model calls per run (four agents, one action call each, 16 rounds; the
`silence` and `no_sense` messages are canned): 9,600 calls in all. Kaggle
sessions are capped at 8 hours, so three sessions, the star on one card and
the ring on the other: gemma-2-9b and Qwen2.5 (about 5 hours), Qwen3-4B and
gemma-2-2b (about 5.5), Llama (about 3). The estimates come from the
measured seconds per call, the ring's being the longer; measured times will
replace them.
