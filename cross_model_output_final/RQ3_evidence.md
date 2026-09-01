# RQ3 evidence pack -- the two-channel dissociation

Generated from `cross_model_output_final/cross_model_master.csv` (1,420 runs).
Every cell n=5 unless stated. `msg` = framing_X (frame in the message
instruction, system prompt neutral, channel open). `prompt` = 
framing_X_context[no_comm] (frame in the system prompt, channel SHUT).
`both` = framing_X_context[cheap_talk] (frame in the system prompt,
channel open, messages unconstrained).

`msg` and `both` both have the channel open, so their contrast isolates
WHERE THE FRAME LIVES and nothing else. That is the dissociation.


## PD

### framing_business

| model | topo | msg | prompt | both | talk adds | msg runs | both runs | max_tok msg/ctx |
|---|---|---|---|---|---|---|---|---|
| Llama-3.1-8B-Instruct | star | 0.69 (sd 0.26) | 0.59 (sd 0.16) | 0.99 (sd 0.03) | +0.39 | [0.48, 0.48, 0.55, 0.97, 0.98] | [0.94, 1.0, 1.0, 1.0, 1.0] | 192/192 clean |
| Llama-3.1-8B-Instruct | cycle | 0.78 (sd 0.18) | 0.52 (sd 0.15) | 0.98 (sd 0.05) | +0.46 | [0.53, 0.7, 0.81, 0.86, 1.0] | [0.89, 1.0, 1.0, 1.0, 1.0] | 192/192 clean |
| Qwen2.5-7B-Instruct | star | 0.98 (sd 0.02) | 0.65 (sd 0.48) | 1.00 (sd 0.00) | +0.35 | [0.95, 0.97, 0.98, 1.0, 1.0] | [1.0, 1.0, 1.0, 1.0, 1.0] | 256/512 CONFOUNDED |
| Qwen2.5-7B-Instruct | cycle | 0.97 (sd 0.06) | 0.66 (sd 0.46) | 1.00 (sd 0.00) | +0.34 | [0.88, 1.0, 1.0, 1.0, 1.0] | [1.0, 1.0, 1.0, 1.0, 1.0] | 256/512 CONFOUNDED |
| Qwen3-4B | star | 1.00 (sd 0.00) | 0.25 (sd 0.37) | 1.00 (sd 0.00) | +0.75 | [1.0, 1.0, 1.0, 1.0, 1.0] | [1.0, 1.0, 1.0, 1.0, 1.0] | 256/256 clean |
| Qwen3-4B | cycle | 1.00 (sd 0.00) | 0.18 (sd 0.22) | 1.00 (sd 0.00) | +0.82 | [1.0, 1.0, 1.0, 1.0, 1.0] | [1.0, 1.0, 1.0, 1.0, 1.0] | 256/256 clean |
| gemma-2-2b-it | star | 0.64 (sd 0.19) | 0.36 (sd 0.13) | 0.95 (sd 0.09) | +0.59 | [0.42, 0.44, 0.71, 0.76, 0.85] | [0.8, 0.97, 1.0, 1.0, 1.0] | 192/256 CONFOUNDED |
| gemma-2-2b-it | cycle | 0.64 (sd 0.15) | 0.57 (sd 0.30) | 0.99 (sd 0.02) | +0.42 | [0.48, 0.51, 0.69, 0.7, 0.83] | [0.97, 0.98, 1.0, 1.0, 1.0] | 192/256 CONFOUNDED |
| gemma-2-9b-it | star | 1.00 (sd 0.00) | 0.10 (sd 0.10) | 1.00 (sd 0.00) | +0.90 | [1.0, 1.0, 1.0, 1.0, 1.0] | [1.0, 1.0, 1.0, 1.0, 1.0] | 160/192/160 clean |
| gemma-2-9b-it | cycle | 1.00 (sd 0.00) | 0.07 (sd 0.05) | 1.00 (sd 0.00) | +0.93 | [1.0, 1.0, 1.0, 1.0, 1.0] | [1.0, 1.0, 1.0, 1.0, 1.0] | 160/192/160 clean |

### framing_team

| model | topo | msg | prompt | both | talk adds | msg runs | both runs | max_tok msg/ctx |
|---|---|---|---|---|---|---|---|---|
| Llama-3.1-8B-Instruct | star | 0.68 (sd 0.28) | 0.70 (sd 0.24) | 1.00 (sd 0.00) | +0.30 | [0.2, 0.64, 0.77, 0.86, 0.91] | [1.0, 1.0, 1.0, 1.0, 1.0] | 192/192 clean |
| Llama-3.1-8B-Instruct | cycle | 0.68 (sd 0.20) | 0.88 (sd 0.14) | 0.99 (sd 0.01) | +0.11 | [0.41, 0.59, 0.67, 0.81, 0.92] | [0.97, 1.0, 1.0, 1.0, 1.0] | 192/192 clean |
| Qwen2.5-7B-Instruct | star | 0.97 (sd 0.02) | 1.00 (sd 0.00) | 1.00 (sd 0.00) | +0.00 | [0.95, 0.95, 0.98, 0.98, 1.0] | [1.0, 1.0, 1.0, 1.0, 1.0] | 256/512 CONFOUNDED |
| Qwen2.5-7B-Instruct | cycle | 1.00 (sd 0.01) | 0.94 (sd 0.14) | 1.00 (sd 0.01) | +0.06 | [0.98, 1.0, 1.0, 1.0, 1.0] | [0.98, 1.0, 1.0, 1.0, 1.0] | 256/512 CONFOUNDED |
| Qwen3-4B | star | 1.00 (sd 0.00) | 0.96 (sd 0.08) | 1.00 (sd 0.00) | +0.04 | [1.0, 1.0, 1.0, 1.0, 1.0] | [1.0, 1.0, 1.0, 1.0, 1.0] | 256/256 clean |
| Qwen3-4B | cycle | 1.00 (sd 0.00) | 0.91 (sd 0.20) | 1.00 (sd 0.00) | +0.09 | [1.0, 1.0, 1.0, 1.0, 1.0] | [1.0, 1.0, 1.0, 1.0, 1.0] | 256/256 clean |
| gemma-2-2b-it | star | 0.99 (sd 0.02) | 0.97 (sd 0.04) | 0.99 (sd 0.01) | +0.01 | [0.96, 0.98, 0.98, 1.0, 1.0] | [0.97, 0.98, 0.98, 1.0, 1.0] | 192/256 CONFOUNDED |
| gemma-2-2b-it | cycle | 0.97 (sd 0.03) | 0.99 (sd 0.02) | 0.99 (sd 0.01) | +0.00 | [0.95, 0.95, 0.97, 1.0, 1.0] | [0.98, 0.98, 0.98, 1.0, 1.0] | 192/256 CONFOUNDED |
| gemma-2-9b-it | star | 1.00 (sd 0.00) | 1.00 (sd 0.00) | 1.00 (sd 0.00) | +0.00 | [1.0, 1.0, 1.0, 1.0, 1.0] | [1.0, 1.0, 1.0, 1.0, 1.0] | 160/192/160 clean |
| gemma-2-9b-it | cycle | 1.00 (sd 0.00) | 0.64 (sd 0.49) | 1.00 (sd 0.00) | +0.36 | [1.0, 1.0, 1.0, 1.0, 1.0] | [1.0, 1.0, 1.0, 1.0, 1.0] | 160/192/160 clean |

### framing_competitive

| model | topo | msg | prompt | both | talk adds | msg runs | both runs | max_tok msg/ctx |
|---|---|---|---|---|---|---|---|---|
| Llama-3.1-8B-Instruct | star | 0.36 (sd 0.09) | 0.28 (sd 0.12) | 0.95 (sd 0.07) | +0.67 | [0.27, 0.31, 0.31, 0.44, 0.47] | [0.88, 0.88, 0.98, 1.0, 1.0] | 192/192 clean |
| Llama-3.1-8B-Instruct | cycle | 0.32 (sd 0.09) | 0.45 (sd 0.08) | 0.98 (sd 0.02) | +0.53 | [0.25, 0.27, 0.29, 0.31, 0.48] | [0.95, 0.97, 0.98, 1.0, 1.0] | 192/192 clean |
| Qwen2.5-7B-Instruct | star | 0.33 (sd 0.39) | 0.12 (sd 0.03) | 0.89 (sd 0.16) | +0.77 | [0.03, 0.05, 0.06, 0.75, 0.75] | [0.66, 0.78, 1.0, 1.0, 1.0] | 256/512 CONFOUNDED |
| Qwen2.5-7B-Instruct | cycle | 0.12 (sd 0.10) | 0.14 (sd 0.02) | 0.94 (sd 0.13) | +0.81 | [0.03, 0.06, 0.06, 0.16, 0.28] | [0.72, 1.0, 1.0, 1.0, 1.0] | 256/512 CONFOUNDED |
| Qwen3-4B | star | 0.01 (sd 0.01) | 0.07 (sd 0.05) | 1.00 (sd 0.00) | +0.93 | [0.0, 0.0, 0.0, 0.0, 0.03] | [1.0, 1.0, 1.0, 1.0, 1.0] | 256/256 clean |
| Qwen3-4B | cycle | 0.02 (sd 0.03) | 0.09 (sd 0.04) | 1.00 (sd 0.00) | +0.91 | [0.0, 0.0, 0.02, 0.02, 0.06] | [1.0, 1.0, 1.0, 1.0, 1.0] | 256/256 clean |
| gemma-2-2b-it | star | 0.08 (sd 0.06) | 0.33 (sd 0.37) | 0.82 (sd 0.31) | +0.49 | [0.0, 0.07, 0.07, 0.08, 0.16] | [0.29, 0.81, 0.98, 1.0, 1.0] | 192/256 CONFOUNDED |
| gemma-2-2b-it | cycle | 0.03 (sd 0.04) | 0.30 (sd 0.32) | 0.79 (sd 0.33) | +0.49 | [0.0, 0.0, 0.02, 0.05, 0.1] | [0.21, 0.81, 0.97, 0.98, 1.0] | 192/256 CONFOUNDED |
| gemma-2-9b-it | star | 0.02 (sd 0.01) | 0.03 (sd 0.02) | 1.00 (sd 0.00) | +0.97 | [0.0, 0.02, 0.02, 0.03, 0.03] | [1.0, 1.0, 1.0, 1.0, 1.0] | 160/192/160 clean |
| gemma-2-9b-it | cycle | 0.01 (sd 0.01) | 0.01 (sd 0.01) | 1.00 (sd 0.00) | +0.99 | [0.0, 0.0, 0.0, 0.0, 0.03] | [1.0, 1.0, 1.0, 1.0, 1.0] | 160/192/160 clean |

## SH

### framing_business

| model | topo | msg | prompt | both | talk adds | msg runs | both runs | max_tok msg/ctx |
|---|---|---|---|---|---|---|---|---|
| Llama-3.1-8B-Instruct | star | 0.62 (sd 0.17) | 0.64 (sd 0.16) | 0.95 (sd 0.03) | +0.31 | [0.44, 0.52, 0.58, 0.67, 0.89] | [0.91, 0.94, 0.97, 0.97, 0.97] | 192/192 clean |
| Llama-3.1-8B-Instruct | cycle | 0.79 (sd 0.06) | 0.73 (sd 0.11) | 0.93 (sd 0.07) | +0.20 | [0.7, 0.76, 0.8, 0.81, 0.86] | [0.81, 0.92, 0.94, 0.97, 1.0] | 192/192 clean |
| Qwen2.5-7B-Instruct | star | 1.00 (sd 0.00) | 0.99 (sd 0.03) | 1.00 (sd 0.00) | +0.01 | [1.0, 1.0, 1.0, 1.0, 1.0] | [1.0, 1.0, 1.0, 1.0, 1.0] | 256/512 CONFOUNDED |
| Qwen2.5-7B-Instruct | cycle | 1.00 (sd 0.00) | 1.00 (sd 0.01) | 1.00 (sd 0.00) | +0.00 | [1.0, 1.0, 1.0, 1.0, 1.0] | [1.0, 1.0, 1.0, 1.0, 1.0] | 256/512 CONFOUNDED |
| Qwen3-4B | star | 1.00 (sd 0.00) | 0.85 (sd 0.24) | 1.00 (sd 0.00) | +0.15 | [1.0, 1.0, 1.0, 1.0, 1.0] | [1.0, 1.0, 1.0, 1.0, 1.0] | 256/256 clean |
| Qwen3-4B | cycle | 1.00 (sd 0.00) | 0.99 (sd 0.01) | 1.00 (sd 0.00) | +0.01 | [1.0, 1.0, 1.0, 1.0, 1.0] | [1.0, 1.0, 1.0, 1.0, 1.0] | 256/256 clean |
| gemma-2-2b-it | star | 0.59 (sd 0.17) | 0.79 (sd 0.07) | 0.71 (sd 0.20) | -0.08 | [0.37, 0.45, 0.67, 0.7, 0.74] | [0.48, 0.58, 0.69, 0.81, 0.98] | 192/256 CONFOUNDED |
| gemma-2-2b-it | cycle | 0.56 (sd 0.12) | 0.74 (sd 0.08) | 0.58 (sd 0.05) | -0.16 | [0.45, 0.48, 0.57, 0.58, 0.75] | [0.53, 0.54, 0.56, 0.63, 0.65] | 192/256 CONFOUNDED |
| gemma-2-9b-it | star | 0.95 (sd 0.08) | 1.00 (sd 0.00) | 1.00 (sd 0.01) | -0.00 | [0.81, 0.95, 1.0, 1.0, 1.0] | [0.98, 1.0, 1.0, 1.0, 1.0] | 160/192/160 clean |
| gemma-2-9b-it | cycle | 0.99 (sd 0.01) | 0.98 (sd 0.03) | 1.00 (sd 0.00) | +0.02 | [0.98, 0.98, 1.0, 1.0, 1.0] | [1.0, 1.0, 1.0, 1.0, 1.0] | 160/192/160 clean |

### framing_team

| model | topo | msg | prompt | both | talk adds | msg runs | both runs | max_tok msg/ctx |
|---|---|---|---|---|---|---|---|---|
| Llama-3.1-8B-Instruct | star | 0.63 (sd 0.13) | 0.70 (sd 0.16) | 0.89 (sd 0.13) | +0.19 | [0.48, 0.56, 0.62, 0.67, 0.83] | [0.67, 0.89, 0.9, 1.0, 1.0] | 192/192 clean |
| Llama-3.1-8B-Instruct | cycle | 0.69 (sd 0.05) | 0.69 (sd 0.08) | 0.87 (sd 0.08) | +0.18 | [0.62, 0.67, 0.69, 0.7, 0.77] | [0.78, 0.81, 0.84, 0.94, 0.97] | 192/192 clean |
| Qwen2.5-7B-Instruct | star | 1.00 (sd 0.00) | 1.00 (sd 0.00) | 1.00 (sd 0.00) | +0.00 | [1.0, 1.0, 1.0, 1.0, 1.0] | [1.0, 1.0, 1.0, 1.0, 1.0] | 256/512 CONFOUNDED |
| Qwen2.5-7B-Instruct | cycle | 1.00 (sd 0.00) | 1.00 (sd 0.00) | 1.00 (sd 0.00) | +0.00 | [1.0, 1.0, 1.0, 1.0, 1.0] | [1.0, 1.0, 1.0, 1.0, 1.0] | 256/512 CONFOUNDED |
| Qwen3-4B | star | 1.00 (sd 0.00) | 0.98 (sd 0.02) | 1.00 (sd 0.00) | +0.02 | [1.0, 1.0, 1.0, 1.0, 1.0] | [1.0, 1.0, 1.0, 1.0, 1.0] | 256/256 clean |
| Qwen3-4B | cycle | 1.00 (sd 0.00) | 1.00 (sd 0.00) | 1.00 (sd 0.00) | +0.00 | [1.0, 1.0, 1.0, 1.0, 1.0] | [1.0, 1.0, 1.0, 1.0, 1.0] | 256/256 clean |
| gemma-2-2b-it | star | 0.19 (sd 0.06) | 0.80 (sd 0.11) | 0.73 (sd 0.13) | -0.07 | [0.12, 0.14, 0.17, 0.24, 0.27] | [0.52, 0.73, 0.74, 0.81, 0.85] | 192/256 CONFOUNDED |
| gemma-2-2b-it | cycle | 0.28 (sd 0.12) | 0.91 (sd 0.02) | 0.46 (sd 0.23) | -0.44 | [0.12, 0.24, 0.26, 0.33, 0.45] | [0.14, 0.39, 0.43, 0.67, 0.69] | 192/256 CONFOUNDED |
| gemma-2-9b-it | star | 0.81 (sd 0.43) | 0.99 (sd 0.02) | 1.00 (sd 0.00) | +0.01 | [0.05, 1.0, 1.0, 1.0, 1.0] | [1.0, 1.0, 1.0, 1.0, 1.0] | 160/192/160 clean |
| gemma-2-9b-it | cycle | 1.00 (sd 0.00) | 0.99 (sd 0.01) | 1.00 (sd 0.01) | +0.01 | [1.0, 1.0, 1.0, 1.0, 1.0] | [0.98, 1.0, 1.0, 1.0, 1.0] | 160/192/160 clean |

### framing_competitive

| model | topo | msg | prompt | both | talk adds | msg runs | both runs | max_tok msg/ctx |
|---|---|---|---|---|---|---|---|---|
| Llama-3.1-8B-Instruct | star | 0.53 (sd 0.02) | 0.61 (sd 0.08) | 0.93 (sd 0.05) | +0.33 | [0.5, 0.51, 0.52, 0.55, 0.56] | [0.88, 0.89, 0.94, 0.97, 0.98] | 192/192 clean |
| Llama-3.1-8B-Instruct | cycle | 0.56 (sd 0.06) | 0.55 (sd 0.09) | 0.97 (sd 0.03) | +0.42 | [0.44, 0.57, 0.58, 0.59, 0.59] | [0.92, 0.97, 0.97, 1.0, 1.0] | 192/192 clean |
| Qwen2.5-7B-Instruct | star | 0.99 (sd 0.01) | 0.84 (sd 0.08) | 1.00 (sd 0.00) | +0.16 | [0.97, 0.98, 1.0, 1.0, 1.0] | [1.0, 1.0, 1.0, 1.0, 1.0] | 256/512 CONFOUNDED |
| Qwen2.5-7B-Instruct | cycle | 0.97 (sd 0.04) | 0.86 (sd 0.08) | 1.00 (sd 0.00) | +0.14 | [0.91, 0.97, 0.98, 1.0, 1.0] | [1.0, 1.0, 1.0, 1.0, 1.0] | 256/512 CONFOUNDED |
| Qwen3-4B | star | 0.98 (sd 0.03) | 0.81 (sd 0.14) | 1.00 (sd 0.00) | +0.19 | [0.94, 0.98, 1.0, 1.0, 1.0] | [1.0, 1.0, 1.0, 1.0, 1.0] | 256/256 clean |
| Qwen3-4B | cycle | 1.00 (sd 0.00) | 0.89 (sd 0.11) | 1.00 (sd 0.00) | +0.11 | [1.0, 1.0, 1.0, 1.0, 1.0] | [1.0, 1.0, 1.0, 1.0, 1.0] | 256/256 clean |
| gemma-2-2b-it | star | 0.23 (sd 0.16) | 0.57 (sd 0.11) | 0.40 (sd 0.16) | -0.16 | [0.05, 0.15, 0.18, 0.28, 0.47] | [0.16, 0.33, 0.49, 0.49, 0.55] | 192/256 CONFOUNDED |
| gemma-2-2b-it | cycle | 0.16 (sd 0.05) | 0.45 (sd 0.13) | 0.25 (sd 0.11) | -0.20 | [0.08, 0.16, 0.16, 0.19, 0.2] | [0.15, 0.15, 0.26, 0.3, 0.4] | 192/256 CONFOUNDED |
| gemma-2-9b-it | star | 0.61 (sd 0.13) | 0.59 (sd 0.35) | 0.98 (sd 0.02) | +0.39 | [0.46, 0.55, 0.56, 0.69, 0.78] | [0.97, 0.97, 0.98, 1.0, 1.0] | 160/192/160 clean |
| gemma-2-9b-it | cycle | 0.61 (sd 0.17) | 0.97 (sd 0.02) | 0.90 (sd 0.21) | -0.07 | [0.42, 0.48, 0.64, 0.64, 0.86] | [0.52, 0.98, 1.0, 1.0, 1.0] | 160/192/160 clean |


## Summary statistics for the prose

- PD, all 30 (model x topology x frame): opening the channel on top of a
  system-prompt frame raises cooperation in **28/30** cases.
- `both` lands in [0.79, 1.00] in all 30 -- never below 0.79.
- talk adds range [+0.00, +0.99].
- competitive frame in the MESSAGES, PD, all 10 model-topology pairs:
  [0.01, 0.36] -- vs [0.79, 1.00] for the same frame in the prompt.

- Confound-free models (same max_tokens on both compared cells):
  Qwen3-4B, gemma-2-9b-it, Llama-3.1-8B-Instruct. Lead with these three.
  Qwen2.5-7B (256 vs 512) and gemma-2-2b-it (192 vs 256) point the same way
  but must be reported as token-confounded.

- Topology invariance: see `figures/two_channel_dissociation_pd.png`; the
  star and cycle rows of every table above track each other.
