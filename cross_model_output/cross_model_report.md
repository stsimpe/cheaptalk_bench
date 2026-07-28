# Cross-Model Cheap-Talk Analysis

**Total runs analysed:** 410

**Models:** ['Llama-3.1-8B-Instruct', 'Qwen2.5-7B-Instruct', 'Qwen3-4B', 'gemma-2-2b-it', 'gemma-2-9b-it']

**Scenarios:** ['baseline_cheap_talk', 'counterfactual', 'framing_business', 'framing_competitive', 'framing_team', 'no_comm', 'no_sense', 'silence']

**Games:** ['pd', 'sh']

---

## Mean cooperation rate by (scenario × model × game)

| scenario            |   ('Llama-3.1-8B-Instruct', 'pd') |   ('Llama-3.1-8B-Instruct', 'sh') |   ('Qwen2.5-7B-Instruct', 'pd') |   ('Qwen2.5-7B-Instruct', 'sh') |   ('Qwen3-4B', 'pd') |   ('Qwen3-4B', 'sh') |   ('gemma-2-2b-it', 'pd') |   ('gemma-2-2b-it', 'sh') |   ('gemma-2-9b-it', 'pd') |   ('gemma-2-9b-it', 'sh') |
|:--------------------|----------------------------------:|----------------------------------:|--------------------------------:|--------------------------------:|---------------------:|---------------------:|--------------------------:|--------------------------:|--------------------------:|--------------------------:|
| baseline_cheap_talk |                             0.984 |                             0.953 |                           1     |                           1     |                1     |                1     |                     0.98  |                     0.226 |                     1     |                     1     |
| counterfactual      |                             0.953 |                             0.965 |                           0.766 |                           0.994 |                1     |                0.995 |                     0.065 |                     0.444 |                     0.781 |                     0.726 |
| framing_business    |                             0.694 |                             0.619 |                           0.981 |                           1     |                1     |                1     |                     0.638 |                     0.586 |                     1     |                     0.953 |
| framing_competitive |                             0.361 |                             0.525 |                           0.328 |                           0.991 |                0.006 |                0.984 |                     0.076 |                     0.227 |                     0.019 |                     0.608 |
| framing_team        |                             0.675 |                             0.634 |                           0.975 |                           1     |                1     |                1     |                     0.986 |                     0.188 |                     1     |                     0.809 |
| no_comm             |                             0.47  |                             0.652 |                           0.084 |                           0.931 |                0.059 |                0.816 |                     0.675 |                     0.648 |                     0.066 |                     0.988 |
| no_sense            |                             0.484 |                             0.702 |                           0.116 |                           0.984 |                0.974 |                1     |                     0.261 |                     0.368 |                     0.091 |                     0.722 |
| silence             |                             0.329 |                             0.843 |                           0.428 |                           0.997 |                0.833 |                1     |                     0.039 |                     0.59  |                     0.304 |                     0.994 |

## Cheap-talk Δ in cooperation (cheap_talk_x − no_comm)

| scenario            |   ('Llama-3.1-8B-Instruct', 'pd') |   ('Llama-3.1-8B-Instruct', 'sh') |   ('Qwen2.5-7B-Instruct', 'pd') |   ('Qwen2.5-7B-Instruct', 'sh') |   ('Qwen3-4B', 'pd') |   ('Qwen3-4B', 'sh') |   ('gemma-2-2b-it', 'pd') |   ('gemma-2-2b-it', 'sh') |   ('gemma-2-9b-it', 'pd') |   ('gemma-2-9b-it', 'sh') |
|:--------------------|----------------------------------:|----------------------------------:|--------------------------------:|--------------------------------:|---------------------:|---------------------:|--------------------------:|--------------------------:|--------------------------:|--------------------------:|
| baseline_cheap_talk |                             0.515 |                             0.301 |                           0.916 |                           0.069 |                0.941 |                0.184 |                     0.305 |                    -0.422 |                     0.934 |                     0.012 |
| counterfactual      |                             0.483 |                             0.313 |                           0.681 |                           0.062 |                0.941 |                0.178 |                    -0.61  |                    -0.204 |                     0.716 |                    -0.261 |
| framing_business    |                             0.224 |                            -0.033 |                           0.897 |                           0.069 |                0.941 |                0.184 |                    -0.036 |                    -0.061 |                     0.934 |                    -0.034 |
| framing_competitive |                            -0.109 |                            -0.127 |                           0.244 |                           0.059 |               -0.052 |                0.168 |                    -0.599 |                    -0.421 |                    -0.047 |                    -0.38  |
| framing_team        |                             0.205 |                            -0.018 |                           0.891 |                           0.069 |                0.941 |                0.184 |                     0.311 |                    -0.46  |                     0.934 |                    -0.178 |
| no_sense            |                             0.015 |                             0.05  |                           0.031 |                           0.053 |                0.915 |                0.184 |                    -0.413 |                    -0.28  |                     0.025 |                    -0.266 |
| silence             |                            -0.141 |                             0.191 |                           0.344 |                           0.066 |                0.775 |                0.184 |                    -0.636 |                    -0.058 |                     0.238 |                     0.006 |

## Hub minus leaf cooperation (within-star asymmetry)

| scenario            |   ('Llama-3.1-8B-Instruct', 'pd') |   ('Llama-3.1-8B-Instruct', 'sh') |   ('Qwen2.5-7B-Instruct', 'pd') |   ('Qwen2.5-7B-Instruct', 'sh') |   ('Qwen3-4B', 'pd') |   ('Qwen3-4B', 'sh') |   ('gemma-2-2b-it', 'pd') |   ('gemma-2-2b-it', 'sh') |   ('gemma-2-9b-it', 'pd') |   ('gemma-2-9b-it', 'sh') |
|:--------------------|----------------------------------:|----------------------------------:|--------------------------------:|--------------------------------:|---------------------:|---------------------:|--------------------------:|--------------------------:|--------------------------:|--------------------------:|
| baseline_cheap_talk |                             0.021 |                            -0.038 |                           0     |                           0     |                0     |                0     |                    -0.006 |                    -0.17  |                     0     |                     0     |
| counterfactual      |                            -0.005 |                             0.029 |                           0.196 |                           0.008 |                0     |               -0.021 |                    -0.048 |                     0.081 |                     0.175 |                     0.258 |
| framing_business    |                             0.025 |                             0.075 |                          -0.008 |                           0     |                0     |                0     |                    -0.228 |                    -0.038 |                     0     |                     0.062 |
| framing_competitive |                             0.099 |                             0.066 |                          -0.004 |                           0.012 |               -0.008 |               -0.012 |                    -0.081 |                    -0.236 |                    -0.008 |                     0.006 |
| framing_team        |                            -0     |                             0.021 |                           0.033 |                           0     |                0     |                0     |                     0.002 |                    -0.066 |                     0     |                     0.004 |
| no_comm             |                             0.001 |                             0.005 |                          -0.029 |                           0.008 |                0.018 |                0.184 |                     0.084 |                     0.229 |                    -0.004 |                    -0.017 |
| no_sense            |                             0.071 |                             0.098 |                          -0.088 |                          -0.012 |                0.035 |                0     |                    -0.035 |                    -0.063 |                     0.062 |                     0.187 |
| silence             |                             0.045 |                             0.058 |                          -0.037 |                           0.004 |                0.028 |                0     |                    -0.011 |                    -0.427 |                    -0.005 |                     0.008 |

## Hub exploitation rate (PD cheap-talk only)

| scenario            |   ('Llama-3.1-8B-Instruct', 'pd') |   ('Qwen2.5-7B-Instruct', 'pd') |   ('Qwen3-4B', 'pd') |   ('gemma-2-2b-it', 'pd') |   ('gemma-2-9b-it', 'pd') |
|:--------------------|----------------------------------:|--------------------------------:|---------------------:|--------------------------:|--------------------------:|
| baseline_cheap_talk |                             0     |                           0     |                    0 |                     0     |                     0     |
| counterfactual      |                             0.051 |                           0.088 |                    0 |                     0.303 |                     0.075 |
| framing_business    |                             0.138 |                           0     |                    0 |                     0.182 |                     0     |
| framing_competitive |                             0.09  |                           0.062 |                    0 |                     0     |                     0.262 |
| framing_team        |                             0.325 |                           0     |                    0 |                     0     |                     0     |
| no_sense            |                             0     |                           0     |                    0 |                     0     |                     0     |

## Detailed coop_rate with 95% bootstrap CI

| model | scenario | game | n | coop% (95% CI) |
|---|---|---|---|---|
| Llama-3.1-8B-Instruct | baseline_cheap_talk | pd | 5 | 98.4% [95.9%, 100.0%] |
| Llama-3.1-8B-Instruct | counterfactual | pd | 5 | 95.3% [91.5%, 98.4%] |
| Llama-3.1-8B-Instruct | framing_business | pd | 5 | 69.4% [49.7%, 89.1%] |
| Llama-3.1-8B-Instruct | framing_competitive | pd | 5 | 36.1% [29.4%, 42.7%] |
| Llama-3.1-8B-Instruct | framing_team | pd | 5 | 67.5% [42.2%, 85.3%] |
| Llama-3.1-8B-Instruct | no_comm | pd | 5 | 47.0% [26.1%, 67.8%] |
| Llama-3.1-8B-Instruct | no_sense | pd | 5 | 48.4% [31.6%, 67.5%] |
| Llama-3.1-8B-Instruct | silence | pd | 5 | 32.9% [29.3%, 36.6%] |
| Llama-3.1-8B-Instruct | baseline_cheap_talk | sh | 5 | 95.3% [87.5%, 99.7%] |
| Llama-3.1-8B-Instruct | counterfactual | sh | 5 | 96.5% [95.3%, 98.4%] |
| Llama-3.1-8B-Instruct | framing_business | sh | 5 | 61.9% [49.7%, 77.2%] |
| Llama-3.1-8B-Instruct | framing_competitive | sh | 5 | 52.5% [50.6%, 54.4%] |
| Llama-3.1-8B-Instruct | framing_team | sh | 5 | 63.4% [53.8%, 74.4%] |
| Llama-3.1-8B-Instruct | no_comm | sh | 5 | 65.2% [59.0%, 72.6%] |
| Llama-3.1-8B-Instruct | no_sense | sh | 5 | 70.2% [61.8%, 80.0%] |
| Llama-3.1-8B-Instruct | silence | sh | 5 | 84.3% [78.1%, 91.2%] |
| Qwen2.5-7B-Instruct | baseline_cheap_talk | pd | 5 | 100.0% [100.0%, 100.0%] |
| Qwen2.5-7B-Instruct | counterfactual | pd | 5 | 76.6% [65.6%, 86.6%] |
| Qwen2.5-7B-Instruct | framing_business | pd | 5 | 98.1% [96.6%, 99.7%] |
| Qwen2.5-7B-Instruct | framing_competitive | pd | 5 | 32.8% [4.7%, 61.3%] |
| Qwen2.5-7B-Instruct | framing_team | pd | 5 | 97.5% [95.9%, 99.1%] |
| Qwen2.5-7B-Instruct | no_comm | pd | 5 | 8.4% [5.9%, 11.6%] |
| Qwen2.5-7B-Instruct | no_sense | pd | 5 | 11.6% [6.9%, 16.2%] |
| Qwen2.5-7B-Instruct | silence | pd | 5 | 42.8% [20.3%, 70.4%] |
| Qwen2.5-7B-Instruct | baseline_cheap_talk | sh | 5 | 100.0% [100.0%, 100.0%] |
| Qwen2.5-7B-Instruct | counterfactual | sh | 5 | 99.4% [98.8%, 100.0%] |
| Qwen2.5-7B-Instruct | framing_business | sh | 5 | 100.0% [100.0%, 100.0%] |
| Qwen2.5-7B-Instruct | framing_competitive | sh | 5 | 99.1% [97.8%, 100.0%] |
| Qwen2.5-7B-Instruct | framing_team | sh | 5 | 100.0% [100.0%, 100.0%] |
| Qwen2.5-7B-Instruct | no_comm | sh | 5 | 93.1% [87.5%, 97.5%] |
| Qwen2.5-7B-Instruct | no_sense | sh | 5 | 98.4% [97.5%, 99.4%] |
| Qwen2.5-7B-Instruct | silence | sh | 5 | 99.7% [99.1%, 100.0%] |
| Qwen3-4B | baseline_cheap_talk | pd | 3 | 100.0% [100.0%, 100.0%] |
| Qwen3-4B | counterfactual | pd | 3 | 100.0% [100.0%, 100.0%] |
| Qwen3-4B | framing_business | pd | 5 | 100.0% [100.0%, 100.0%] |
| Qwen3-4B | framing_competitive | pd | 5 | 0.6% [0.0%, 1.9%] |
| Qwen3-4B | framing_team | pd | 5 | 100.0% [100.0%, 100.0%] |
| Qwen3-4B | no_comm | pd | 3 | 5.9% [3.1%, 7.5%] |
| Qwen3-4B | no_sense | pd | 3 | 97.4% [96.9%, 98.4%] |
| Qwen3-4B | silence | pd | 3 | 83.3% [50.0%, 100.0%] |
| Qwen3-4B | baseline_cheap_talk | sh | 3 | 100.0% [100.0%, 100.0%] |
| Qwen3-4B | counterfactual | sh | 3 | 99.5% [98.4%, 100.0%] |
| Qwen3-4B | framing_business | sh | 5 | 100.0% [100.0%, 100.0%] |
| Qwen3-4B | framing_competitive | sh | 5 | 98.4% [96.2%, 100.0%] |
| Qwen3-4B | framing_team | sh | 5 | 100.0% [100.0%, 100.0%] |
| Qwen3-4B | no_comm | sh | 3 | 81.6% [61.2%, 100.0%] |
| Qwen3-4B | no_sense | sh | 3 | 100.0% [100.0%, 100.0%] |
| Qwen3-4B | silence | sh | 3 | 100.0% [100.0%, 100.0%] |
| gemma-2-2b-it | baseline_cheap_talk | pd | 5 | 98.0% [93.9%, 100.0%] |
| gemma-2-2b-it | counterfactual | pd | 5 | 6.5% [2.9%, 11.2%] |
| gemma-2-2b-it | framing_business | pd | 10 | 63.8% [53.0%, 74.5%] |
| gemma-2-2b-it | framing_competitive | pd | 10 | 7.6% [4.4%, 10.8%] |
| gemma-2-2b-it | framing_team | pd | 10 | 98.6% [97.7%, 99.3%] |
| gemma-2-2b-it | no_comm | pd | 5 | 67.5% [34.7%, 92.2%] |
| gemma-2-2b-it | no_sense | pd | 5 | 26.1% [16.7%, 35.6%] |
| gemma-2-2b-it | silence | pd | 5 | 3.9% [1.1%, 8.4%] |
| gemma-2-2b-it | baseline_cheap_talk | sh | 5 | 22.6% [14.6%, 30.6%] |
| gemma-2-2b-it | counterfactual | sh | 5 | 44.4% [36.7%, 52.9%] |
| gemma-2-2b-it | framing_business | sh | 10 | 58.6% [49.3%, 67.6%] |
| gemma-2-2b-it | framing_competitive | sh | 10 | 22.7% [14.5%, 31.8%] |
| gemma-2-2b-it | framing_team | sh | 10 | 18.8% [15.3%, 22.3%] |
| gemma-2-2b-it | no_comm | sh | 5 | 64.8% [55.3%, 71.1%] |
| gemma-2-2b-it | no_sense | sh | 5 | 36.8% [25.0%, 49.0%] |
| gemma-2-2b-it | silence | sh | 5 | 59.0% [48.1%, 69.9%] |
| gemma-2-9b-it | baseline_cheap_talk | pd | 5 | 100.0% [100.0%, 100.0%] |
| gemma-2-9b-it | counterfactual | pd | 5 | 78.1% [67.5%, 86.2%] |
| gemma-2-9b-it | framing_business | pd | 5 | 100.0% [100.0%, 100.0%] |
| gemma-2-9b-it | framing_competitive | pd | 5 | 1.9% [0.9%, 2.8%] |
| gemma-2-9b-it | framing_team | pd | 5 | 100.0% [100.0%, 100.0%] |
| gemma-2-9b-it | no_comm | pd | 5 | 6.6% [3.1%, 9.7%] |
| gemma-2-9b-it | no_sense | pd | 5 | 9.1% [6.2%, 13.4%] |
| gemma-2-9b-it | silence | pd | 5 | 30.4% [10.0%, 65.3%] |
| gemma-2-9b-it | baseline_cheap_talk | sh | 5 | 100.0% [100.0%, 100.0%] |
| gemma-2-9b-it | counterfactual | sh | 5 | 72.6% [56.4%, 87.2%] |
| gemma-2-9b-it | framing_business | sh | 5 | 95.3% [87.8%, 100.0%] |
| gemma-2-9b-it | framing_competitive | sh | 5 | 60.8% [51.5%, 70.6%] |
| gemma-2-9b-it | framing_team | sh | 5 | 80.9% [42.8%, 100.0%] |
| gemma-2-9b-it | no_comm | sh | 5 | 98.8% [96.9%, 100.0%] |
| gemma-2-9b-it | no_sense | sh | 5 | 72.2% [47.2%, 90.0%] |
| gemma-2-9b-it | silence | sh | 5 | 99.4% [98.8%, 100.0%] |
