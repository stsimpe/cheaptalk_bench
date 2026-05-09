# Cheap-Talk Benchmark v2: Star Topology × PD/SH

Pilot benchmark for the thesis "The Role of Pre-Communication (cheap talk) in LLM Societies"
(Tsimperis, NTUA, sup. Voulodimos).

## Mapping to thesis Research Questions

The thesis poses four research questions (Section I-C of the report):

1. **Direction:** Does cheap talk push LLM agents toward cooperative or harmful equilibria?
   Does the answer depend on payoff structure, models, or message content?
2. **Topology:** How does network structure modulate cheap talk? In particular, do hub
   agents in star topologies disproportionately steer outcomes?
3. **Heterogeneity:** Different effects in mixed vs homogeneous LLM populations?
4. **Intervention:** Can the protocol or topology be modified to preserve coordination
   benefits while limiting harmful shifts?

This pilot focuses on **RQ2 (Topology)** as the primary target and provides a
**baseline measurement for RQ1 (Direction)** by varying game structure (PD vs SH).
RQ3 and RQ4 are out of scope for this pilot and addressed in subsequent work.

### Specific pilot question

> *"In a 4-agent star topology with homogeneous LLM agents, does edge-routed cheap talk
> produce a measurable hub-vs-leaf asymmetry in cooperation behavior across PD and SH
> games, compared to a no-communication baseline?"*

Concrete hypotheses (to be confirmed/refuted by the data):

- **H1 (RQ1, game structure):** Cheap talk boosts cooperation more in SH (coordination
  with multiple equilibria) than in PD (where defection is the dominant strategy).
  Predicted by Farrell (1987), confirmed in LLMs by Madmoun & Lahlou (2025).
- **H2 (RQ2, hub asymmetry):** With cheap talk, the hub's cooperation rate drives
  leaves' cooperation rates more than the reverse. The hub becomes a coordination
  anchor.
- **H3 (RQ2, hub exploitation):** In PD, the hub has structurally higher temptation
  to defect (3× the temptation payoff per round). Cheap talk may either suppress this
  exploitation (the hub commits and follows through) or amplify it (the hub uses
  cheap talk to lull leaves into cooperating, then defects).

## What the experiments measure

Four homogeneous LLM agents interact in a star topology (1 hub + 3 leaves) over 16
rounds (Georgousis 2025) of a repeated 2x2 game, with a 10-round sliding memory window
(Sabani 2025). Each edge runs a pairwise instance of the game; each agent commits to
one action per round, applied across all its edges.

We compare two conditions:

1. **No communication** (`run_no_comm.py`) — agents see only interaction history.
2. **Cheap talk** (`run_cheap_talk.py`) — each round, agents first exchange one
   free-form sentence along their edges, *then* choose an action. The hub broadcasts
   one message reaching all leaves; each leaf sends one message reaching only the hub.
   Leaves do **not** see each other's messages — this edge-restricted routing is what
   makes the topology structurally non-trivial for cheap talk.

Games:

- **PD (Prisoner's Dilemma):** social dilemma, defection is dominant. Payoffs from
  Georgousis Table 5.4(a): CC=(4,4), CD=(1,6), DC=(6,1), DD=(2,2).
- **SH (Stag Hunt):** coordination game with two pure-strategy equilibria. Payoffs
  from Georgousis Table 5.4(d): SS=(6,6), SH=(1,4), HS=(4,1), HH=(2,2).

## Setup

```bash
pip install -r requirements.txt
```

Copy the template environment file and paste your API key into it:

```bash
cp .env.example .env
# now edit .env and replace the placeholder with your real key
```

The `.env` file is git-ignored — your key stays local. The runners load it
automatically; you do NOT need to `export` anything in your shell.

## Running the pilot

```bash
# Baseline — uses Groq + Llama 3.3 70B by default (free tier)
python run_no_comm.py --game pd
python run_no_comm.py --game sh

# Cheap talk
python run_cheap_talk.py --game pd
python run_cheap_talk.py --game sh

# Aggregate metrics & RQ-aligned analysis
python analysis.py
```

### Free-tier rate limit budgeting

Groq's free tier caps: 30 req/min, 6K tok/min, 100K tok/day for `llama-3.3-70b-versatile`
(500K/day for `llama-3.1-8b-instant`).

API call budget for the full pilot:

| Condition | Calls per run | Total (5 runs × 2 games) |
|---|---|---|
| No communication | 4 agents × 16 rounds × 1 = 64 | 640 |
| Cheap talk       | 4 agents × 16 rounds × 2 = 128 | 1,280 |
| **Total**        |   | **1,920** |

For the 70B model this exceeds 1 day of free quota. Two options:

1. **Spread across days** (recommended): no-comm Day 1, cheap-talk Day 2.
2. **Use the smaller `llama-3.1-8b-instant`** (5× quota): adds the comparison "model
   capability × cheap talk effect" to the analysis, which is itself relevant to RQ1.

## Design choices and citations

| Choice | Source | Why |
|---|---|---|
| 4 agents, 1 hub + 3 leaves | Sabani §4.3.2, §4.3.3 | Direct extension of Sabani's star setup |
| Pairwise game per edge, sum across neighbors | Sabani §4.3.2, eq. for `c_i^t` | Network formulation that produces topology asymmetry |
| Single action per agent per round | Sabani §4.1.2.2 | Standard in networked IPD |
| 16 rounds, hidden horizon | Georgousis §5.5 | Avoids backward-induction defection |
| 10-round memory window in prompt | Sabani §4.1.4 | Matches reference methodology, fits context budget |
| 5 runs per condition | Georgousis §6.1 | Adequate for variance estimation |
| One sentence cheap-talk (≤20 words) | Extension of Madmoun §4.1 (one word) | Allows richer signaling than one-word; still cheap |
| Edge-restricted message routing | This work | Makes topology structurally meaningful for comm |
| No "leader/follower" labels in prompts | This work (departure from Sabani) | Avoids confounding centrality with role priming |
| Neutral framing (no business/team context) | Lorè & Heydari, framing controls | Baseline for future framing sweeps (RQ1) |

## Roadmap to full thesis coverage

| Version | Adds | Covers RQs |
|---|---|---|
| **v2 (this)** | Star + PD/SH + cheap talk | RQ2 (primary), RQ1 (game-structure baseline) |
| v3 | Heterogeneous populations | RQ3 |
| v4 | Framing variations | RQ1 (full) |
| v5 | Adversarial leaf agents | RQ4 |
| v6 | Cycle/line topologies for comparison | RQ2 (extended) |
