# Pilot results — cheap-talk benchmark (Llama-3.1-8B-Instant, 4-node star)

**Setup.** Two repetitions per cell, 8 rounds each, hidden horizon. Conditions: {no_comm, cheap_talk} × {PD, SH} × 4 agents (1 hub + 3 leaves). Total: 256 LLM calls, 0 invalid outputs. Results in `results/no_comm/` and `results/cheap_talk/`.

## 1. Aggregate cooperation rates

| Game | Condition | Cooperation rate (mean ± sd) | Full-cooperation rounds |
|------|-----------|------------------------------|-------------------------|
| PD   | no_comm   | 0.594 ± 0.177                | 18.8% (3/16 rounds)     |
| PD   | cheap_talk| **1.000 ± 0.000**            | **100% (16/16)**        |
| SH   | no_comm   | 0.844 ± 0.044                | 50.0% (8/16)            |
| SH   | cheap_talk| 0.984 ± 0.022                | 93.8% (15/16)           |

**Cheap-talk Δ:** PD `+40.6 pp`, SH `+14.1 pp`.

## 2. Round-by-round cooperation trajectory (PD)

| Round  | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|--------|---|---|---|---|---|---|---|---|
| no_comm| 0.875 | 0.875 | 0.625 | 0.375 | 0.500 | 0.625 | 0.500 | **0.375** |
| cheap_talk | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | **1.00** |

The no_comm trajectory shows the canonical PD defection cascade: cooperation drops from 87.5% to 37.5% over 8 rounds. The cheap_talk trajectory is flat at 100% across every single round.

## 3. Hub vs leaf asymmetry

| Condition × Game     | hub coop | leaf coop | gap   | hub exploit |
|----------------------|----------|-----------|-------|-------------|
| no_comm × PD         | 62.5%    | 58.3%     | +4.2 pp | n/a         |
| cheap_talk × PD      | 100%     | 100%      | 0.0 pp  | **0.0%**    |
| no_comm × SH         | 87.5%    | 83.3%     | +4.2 pp | n/a         |
| cheap_talk × SH      | 100%     | 97.9%     | +2.1 pp | n/a         |

Hub-vs-leaf cooperation gap is ≤ 4.2 pp across all four cells. **Hub exploitation rate** (the hub sends a cooperative-sounding message but defects): 0/64 messages. H3 is not supported in this pilot.

## 4. Representative messages

The full message log is in `results/cheap_talk/*.json` under `history[*].messages`. Five examples worth highlighting:

**Example 1 — typical PD cheap-talk template (PD run 1, round 3):**
> Hub: *"I plan to cooperate this round and expect reciprocation from all my neighbors."*
> Leaf #1: *"I expect cooperation and will reciprocate if you choose to cooperate this round."*
> All 4 agents play Cooperate. Payoffs: hub=12, each leaf=4.

**Example 2 — first conditional/threat language (PD run 2, round 4):**
> Hub: *"I plan to cooperate this round, but **will reassess if mutual cooperation isn't reciprocated**."*

This is the only PD message across both runs that uses conditional language. It is not followed by any defection — all 4 agents continue to cooperate.

**Example 3 — explicit action-name signaling (SH run 1, round 1):**
> Leaf #2: *"I'm open to cooperation but **will play Stag** if I perceive a high chance of getting Hare in return."*

In SH the agents reference the action name (`Stag`) explicitly 35 times, against 0 explicit references to `Cooperate`/`Defect` in PD. Consistent with Farrell (1987): in coordination games with multiple equilibria, cheap talk operates by *naming* the equilibrium.

**Example 4 — message preceding the only SH defection (SH run 2, round 5):**
> Leaf #1: *"I'll maintain cooperation, but **it's time to explore alternative strategies to avoid stagnation**."*
> Leaf #1's actual action: **Hare**.

This is the clearest evidence in the pilot that messages carry meaningful information. The agent explicitly signals the deviation before playing it.

**Example 5 — hub mirroring after a defection (SH run 2, round 6):**
> Hub: *"I prefer cooperation but **may need to consider alternative strategies** in future rounds to maintain mutual benefit."*

The hub echoes Leaf #1's vocabulary from round 5 ("alternative strategies") but stays at Stag. Round 7 onwards: full cooperation resumes. Episode lasts exactly 1 round.

## 5. Message lexicon — top words preceding each action

| Game | Word           | Count | P(word \| coop) | P(word \| defect) |
|------|----------------|-------|-----------------|---------------------|
| PD   | `cooperate`    | 36    | 7.0%            | 0.0%                |
| PD   | `cooperation`  | 33    | 6.4%            | 0.0%                |
| PD   | `mutual`       | 17    | 3.3%            | 0.0%                |
| SH   | `stag`         | 35    | 6.6%            | 0.0%                |
| SH   | `mutual`       | 25    | 4.7%            | 0.0%                |
| SH   | `beneficial`   | 24    | 4.6%            | 0.0%                |

In PD, 64/64 messages preceded a cooperative action. In SH, 63/64 preceded a cooperative action; the single deviation is Example 4 above.

## 6. Findings (subject to small N)

1. **Cheap talk fully arrests the PD defection cascade.** PD cooperation falls from 87.5% to 37.5% over 8 rounds without communication; with communication it stays at 100% throughout.
2. **The PD effect (+41 pp) substantially exceeds the SH effect (+14 pp).** This inverts the Farrell (1987) prediction, but the absolute level reached by both games under cheap talk is comparable (~100%). The asymmetry reflects ceiling effects on the SH baseline rather than weaker cheap-talk efficacy in PD.
3. **Hub does not exploit its structural advantage.** 0/64 hub messages preceded a hub defection. Hub-vs-leaf cooperation gap is ≤ 4.2 pp in every cell. H3 not supported in this pilot.
4. **Messages are signal, not noise.** The single SH defection is preceded by an explicit announcement of the deviation. The hub responds with mirrored vocabulary and the system returns to full cooperation in one round.
5. **Game-specific dialect.** PD messages use abstract cooperative vocabulary (`cooperate`, `mutual`, `trust`); SH messages reference the action name explicitly (`stag` 35×). Consistent with cheap talk's role as equilibrium-selection device in coordination games.

## 7. Limitations

- **N=2 runs per cell** vs. Sabani (2025) and Georgousis (2025) standard of N=5. Reported sd's are unstable.
- **8 rounds** vs. canonical 16. Whether SH cooperation also begins to decay between rounds 9–16 cannot be determined from this data.
- **Single model** (Llama-3.1-8B-instant). Cross-model variation is the natural next test for RQ1.
- **Single topology** (4-node star). RQ2 ("does network structure modulate cheap talk?") cannot be answered without a comparison topology (clique or line). Within-star hub-vs-leaf asymmetry is small but this does not generalize to a between-topology claim.
- **Hub exploitation heuristic** is keyword-based; an LLM-as-judge classifier would be more robust before any strong claim about deception.
- **20-word message cap** produces post-truncation in ~8% of messages. A larger cap (25–30 words) is recommended for the next iteration.
