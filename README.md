# Cheap-Talk Benchmark: Network Topologies × PD/SH

Benchmark for the thesis "The Role of Pre-Communication (cheap talk) in LLM Societies"
(Tsimperis, NTUA, sup. Voulodimos).

Homogeneous LLM agents play a repeated 2×2 game on a network. Each edge runs a
pairwise instance of the game; each agent commits to **one** action per round,
applied across all of its edges. In the cheap-talk condition every round has two
phases: all agents send one free-form sentence along their edges, *then* everyone
chooses an action. Messages are costless and non-binding.

## Mapping to thesis Research Questions

1. **Direction:** Does cheap talk push LLM agents toward cooperative or harmful
   equilibria? Does the answer depend on payoff structure, models, or message content?
2. **Topology:** How does network structure modulate cheap talk? Do hub agents in
   star topologies disproportionately steer outcomes?
3. **Heterogeneity:** Different effects in mixed vs homogeneous LLM populations?
4. **Intervention:** Can the protocol or topology be modified to preserve coordination
   benefits while limiting harmful shifts?

Current coverage: **RQ1** (games × models × message content, 380 runs) and **RQ2**
(star complete; clique/line/cycle supported by the engine). RQ3/RQ4 are staged in
`notebooks/` as templates — see `notebooks/EXPERIMENTS.md`.

## Repository layout

```
.                       engine + runners (flat: the modules import each other by name)
├── config.py           ExperimentConfig / ModelConfig — every knob
├── engine.py           rounds, payoffs, message routing, run records
├── topology.py         star · clique · line · cycle
├── games.py            PD / SH payoff matrices
├── agent.py            prompt assembly + robust JSON parsing
├── prompts.py          system/user templates
├── message_policies.py message content controls + context framing
├── llm_client.py       groq · openai · huggingface · openrouter · local (4-bit)
├── run_all_scenarios.py    ← the runner you want (all scenarios, one model load)
├── run_full_sweep.py       single-scenario sweep (used by kaggle_runner.ipynb)
├── analysis.py, cross_model_*.py, framing_contrast_plot.py, llm_judge.py,
│   analyze_hub_leaf.py      analysis layer
├── notebooks/          one Kaggle notebook per planned experiment
├── docs/               ARCHITECTURE_REVIEW · KAGGLE_SETUP · pilot_findings
└── cross_model_output/ generated figures/tables that the thesis cites
```

Raw run outputs (`results*/`, zips) are git-ignored — they are large and
regenerated per campaign. The analysis products that get cited are tracked.

## Setup

```bash
pip install -r requirements.txt        # API providers
pip install -r requirements_local.txt  # + transformers/bitsandbytes for local GPU
```

For API providers, create a `.env` with your key (`GROQ_API_KEY`,
`OPENAI_API_KEY`, `HUGGINGFACE_API_KEY`, or `OPENROUTER_API_KEY`). It is
git-ignored and loaded automatically — no shell `export` needed. For local
inference on Kaggle, set `HF_TOKEN` as a Kaggle Secret instead (gated models).

## Running

One model, all scenarios, model loaded once, zip written after each scenario:

```bash
python run_all_scenarios.py --provider local --model-id Qwen/Qwen2.5-7B-Instruct \
    --topology star --n-runs 5 --n-rounds 16 \
    --scenarios baseline no_sense silence counterfactual \
                framing_business framing_team framing_competitive \
    --out-dir-base results/Qwen2.5-7B-Instruct \
    --zip-mirror /kaggle/working --no-probe
```

Non-star topologies are written to their own tree (`results/..._cycle/`) so star
aggregations never mix them in by accident.

### Scenarios

| Scenario | Conditions | What it isolates |
|---|---|---|
| `baseline` | no_comm + cheap_talk | the cheap-talk effect itself |
| `no_sense` | cheap_talk | channel without content (off-topic templates) |
| `silence` | cheap_talk | channel with zero content |
| `counterfactual` | cheap_talk | IF/WOULD message framing |
| `framing_business` / `_team` / `_competitive` | cheap_talk | social framing of the **messages** |
| `framing_*_context` | no_comm + cheap_talk | social framing of the **system prompt** — the only way to test framing *without* cheap talk |

### Topologies

`star` (1 hub + 3 leaves, the original design) · `clique` (fully connected) ·
`line` (path) · `cycle` (ring: degree-regular like the clique, sparse like the
line). Message routing is edge-strict everywhere: an agent's message reaches its
neighbors and nobody else, and `messages_seen_by` is logged per round so the
restriction is verifiable post hoc.

### Analysis

```bash
python analysis.py --results-dir results/<model>      # per-campaign metrics
python cross_model_analysis.py                        # cross-model tables + report
python analyze_hub_leaf.py                            # RQ2 hub/leaf influence, cascades
```

## Games

- **PD (Prisoner's Dilemma):** defection dominant. Georgousis Table 5.4(a):
  CC=(4,4), CD=(1,6), DC=(6,1), DD=(2,2).
- **SH (Stag Hunt):** two pure-strategy equilibria. Georgousis Table 5.4(d):
  SS=(6,6), SH=(1,4), HS=(4,1), HH=(2,2).

## Design choices and citations

| Choice | Source | Why |
|---|---|---|
| 4 agents, 1 hub + 3 leaves | Sabani §4.3.2, §4.3.3 | Direct extension of Sabani's star setup |
| Pairwise game per edge, sum across neighbors | Sabani §4.3.2 | Network formulation that produces topology asymmetry |
| Single action per agent per round | Sabani §4.1.2.2 | Standard in networked IPD |
| 16 rounds, hidden horizon | Georgousis §5.5 | Avoids backward-induction defection |
| 10-round memory window in prompt | Sabani §4.1.4 | Matches reference methodology, fits context budget |
| 5 runs per condition | Georgousis §6.1 | Adequate for variance estimation |
| One sentence cheap talk (≤20 words) | Extension of Madmoun §4.1 (one word) | Richer signaling than one word; still cheap |
| Edge-restricted message routing | This work | Makes topology structurally meaningful for communication |
| No "leader/follower" labels in prompts | This work (departure from Sabani) | Avoids confounding centrality with role priming |
| Neutral framing by default | Lorè & Heydari (2024) | Framing swamps payoff effects; needs a neutral baseline |

## Status

- **Done:** star topology × 5 models × 7 scenarios × {PD, SH} — 380 runs.
  Results summarised in `cross_model_output/cross_model_report.md`.
- **Next:** cycle topology across the same grid (RQ2 causal claim), and the
  `framing_*_context` scenarios (framing without cheap talk).
- **Staged:** heterogeneous populations and adversarial roles (RQ3/RQ4) — see
  `docs/ARCHITECTURE_REVIEW.md` for what the engine still needs.
