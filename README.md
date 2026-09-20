# Cheap-Talk Benchmark: Content, Disposition and Network Structure

Benchmark for the thesis *The Role of Pre-Play Communication (Cheap Talk) in LLM
Societies* (Tsimperis, NTUA, sup. Voulodimos).

Four agents of the same model play a repeated 2×2 game on a network. Each edge
runs a pairwise instance of the game and each agent commits to **one** action per
round, applied across all of its edges. In the cheap-talk condition every round
has two phases: all agents send one free-form sentence along their edges, *then*
everyone chooses an action. Messages are costless and non-binding.

**State: the experimental programme is complete — 1,520 runs, all four research
questions answered.** No further GPU work is planned beyond the ablation noted
under *Known limitation* below.

## The research questions, and what the corpus says

| | question | answer |
|---|---|---|
| **RQ1** Direction | does cheap talk push toward cooperative or harmful equilibria? | **helpful**: 0 of 50 meaningful-content PD cells fall below their own silent anchor; talk works by stopping decay, not by building cooperation |
| **RQ2** Topology | does network structure modulate the effect? do hubs steer outcomes? | **weak directional tendency** (sign test p ≈ 0.19) and the hub mechanism is refuted (hub − leaf ∈ [−0.00, +0.05], r = 0.97) |
| **RQ3** Channel separation | does a social frame act on disposition, on messages, or both? | **two dissociable routes**: a team frame acts on disposition and makes talk redundant; a competitive frame acts on the messages, and an open channel overrides it in 30 of 30 combinations |
| **RQ4** Intervention | can the protocol or the network be changed to keep the benefit and lose the harm? | **negative on both levers**: rewiring changes nothing, and in-the-loop lexical filtering fails at 8–35% and at 62–100% blocking, because lies avoid the flagged vocabulary and hostility migrates |

Heterogeneous populations, which occupied the RQ3 slot in an earlier version of
this programme, were never run and are stated as future work.

## Design

Held fixed in every run ever recorded: **4 agents, 16 rounds, hidden horizon,
10-round memory window, T = 0.7, messages ≤ 20 words, seed 42.** The seed governs
run ordering, not sampling, so replicates are genuine independent samples.

- **Games** (`games.py`): Prisoner's Dilemma and Stag Hunt, payoffs taken
  verbatim from Georgousis (2025) for comparability.
- **Topologies** (`topology.py`): star and cycle were run; clique and line are
  implemented and untested.
- **Scenario ladder** (`message_policies.py`, `run_all_scenarios.py`): 11 labels
  and 14 cells per (model, topology, game), separating the channel from its
  content, and message-borne framing from prompt-borne framing.
- **Models**: Llama-3.1-8B, Qwen2.5-7B, Qwen3-4B, Gemma-2-2b, Gemma-2-9b, all
  4-bit on free Kaggle T4s.

Every additive knob defaults to the pre-existing behaviour, so any old run
reproduces byte-for-byte: `context_framing`, `message_filter`, `action_retries`,
`topology_aware_comm_prompt`.

## Layout

```
.                          the package is the repo root; modules import by name
├── config.py              ExperimentConfig / ModelConfig — every knob
├── games.py               payoff matrices
├── topology.py            star / clique / line / cycle
├── prompts.py             system and user templates
├── message_policies.py    what flows through the channel, incl. the RQ4 filter
├── agent.py               one agent: prompt, LLM call, JSON parsing
├── engine.py              the two-phase round loop; computes delivery
├── llm_client.py          4 API providers + local transformers
├── run_all_scenarios.py   runs many scenarios in one warm process
├── campaign.py            per-model plan, --dry-run, post-run verification
├── analysis.py            summarise_run / scenario_of — one run to one row
├── cross_model_analysis.py  JSONs -> master / aggregated / delta CSVs
├── cross_model_plots.py   the 21 figures, always per topology
├── harm_ledger.py         helpful-vs-harmful, each cell against its own anchor
├── message_corpus.py      every message joined to what its sender then did
├── filter_analysis.py     offline filter selectivity (which filter to run)
├── llm_judge.py           LLM-as-judge deception, with per-cell validation
├── deception_report.py    reports only the cells where the judge is validated
├── rq4_filter_plot.py     the RQ4 figure
├── verify_prompt_bug.py   the four log-only checks of the prompt bug
├── commfix_report.py      the ablation, judged against a noise floor
├── kaggle_*.ipynb         the four campaign notebooks (all call campaign.py)
├── cross_model_output_final/  the released CSVs behind every number
├── figures/               the released figures
├── notebooks/             proposals for the next stage: clique, mixed
│                          populations, a Bertrand pricing pilot
└── docs/                  Kaggle setup, and the May pilot's findings
```

## One command per claim

Every number in the thesis regenerates from the run files. `<ten>` is the ten
run folders: `{gemma-2-2b-it,gemma-2-9b-it,Llama-3.1-8B-Instruct,Qwen2.5-7B-Instruct,Qwen3-4B}_{star,cycle}`.

| claim | command |
|---|---|
| aggregate tables (280 cells) | `python cross_model_analysis.py --roots <ten> --out-dir cross_model_output_final` |
| all 21 figures | `python cross_model_plots.py --in-dir cross_model_output_final --out-dir figures --roots <ten>` |
| RQ1, the harm ledger | `python harm_ledger.py --in-dir cross_model_output_final` |
| RQ4, offline filter choice | `python message_corpus.py --roots <ten> --out-dir cross_model_output_final` then `python filter_analysis.py --in-dir cross_model_output_final` |
| RQ4, the figure | `python rq4_filter_plot.py --root <project root> --out figures/rq4_filter_outcome.png` |
| deception, judged | `python llm_judge.py label --roots <ten> --games pd` then `python deception_report.py --judge-labels <labels.csv>` |
| judge validation | `python llm_judge.py sample --roots <ten> --games pd --n 120` then `python llm_judge.py validate --human-labels <filled> --judge-labels <labels>` |
| the prompt-bug checks | `python verify_prompt_bug.py --roots <ten>` |

On Windows, prefix with `PYTHONIOENCODING=utf-8`.

## Notebooks

| notebook | what it runs |
|---|---|
| `kaggle_runner.ipynb` | the main campaigns (star grid, cycle grid, context framings) |
| `kaggle_judge.ipynb` | the deception judge over the PD corpus |
| `kaggle_rq4_f1.ipynb` | the RQ4 broad-filter cell, five models in one session |
| `kaggle_commfix_ablation.ipynb` | the corrected-prompt ablation (see below) |

All four call `campaign.py`, which prints its plan and refuses to start when the
plan does not match what was asked. Kaggle executes the cells in *your* workspace,
not the ones in this repo: after a notebook changes here, re-import it.

## Known limitation, being closed

Until 2026-09-20 the cheap-talk system prompt carried one routing sentence
written for the star, on every topology, so the 500 ring runs with an open
channel were told about a hub they did not have. Delivery is computed from the
topology and never reads the prompt: verified correct in all 64,640 agent-rounds.
`verify_prompt_bug.py` bounds the behavioural impact; the fix is opt-in
(`--topology-aware-comm-prompt`) so the existing corpus stays reproducible, and
`kaggle_commfix_ablation.ipynb` re-runs the four cells that carry RQ2.

## Install

```
pip install -r requirements.txt          # API providers + analysis
pip install -r requirements_local.txt    # add transformers + bitsandbytes
```

API keys come from the environment (`.env` locally, Kaggle Secrets on Kaggle);
gated models need `HF_TOKEN`.
