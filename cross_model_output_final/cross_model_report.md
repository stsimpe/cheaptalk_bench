# Cross-Model Cheap-Talk Analysis

**Total runs analysed:** 1420

**Models:** ['Llama-3.1-8B-Instruct', 'Qwen2.5-7B-Instruct', 'Qwen3-4B', 'gemma-2-2b-it', 'gemma-2-9b-it']

**Scenarios:** ['baseline_cheap_talk', 'counterfactual', 'framing_business', 'framing_business_context', 'framing_competitive', 'framing_competitive_context', 'framing_team', 'framing_team_context', 'no_comm', 'no_sense', 'silence']

**Games:** ['pd', 'sh']

---

## Mean cooperation rate by (scenario × model × game)

| cell                                    |   ('Llama-3.1-8B-Instruct', 'pd') |   ('Llama-3.1-8B-Instruct', 'sh') |   ('Qwen2.5-7B-Instruct', 'pd') |   ('Qwen2.5-7B-Instruct', 'sh') |   ('Qwen3-4B', 'pd') |   ('Qwen3-4B', 'sh') |   ('gemma-2-2b-it', 'pd') |   ('gemma-2-2b-it', 'sh') |   ('gemma-2-9b-it', 'pd') |   ('gemma-2-9b-it', 'sh') |
|:----------------------------------------|----------------------------------:|----------------------------------:|--------------------------------:|--------------------------------:|---------------------:|---------------------:|--------------------------:|--------------------------:|--------------------------:|--------------------------:|
| baseline_cheap_talk                     |                             0.991 |                             0.916 |                           0.962 |                           1     |                1     |                1     |                     0.977 |                     0.338 |                     1     |                     0.944 |
| counterfactual                          |                             0.994 |                             0.962 |                           0.972 |                           1     |                1     |                1     |                     0.048 |                     0.378 |                     0.984 |                     0.627 |
| framing_business                        |                             0.781 |                             0.786 |                           0.975 |                           1     |                1     |                1     |                     0.643 |                     0.565 |                     1     |                     0.994 |
| framing_business_context[cheap_talk]    |                             0.978 |                             0.928 |                           1     |                           1     |                1     |                1     |                     0.99  |                     0.581 |                     1     |                     1     |
| framing_business_context[no_comm]       |                             0.52  |                             0.731 |                           0.662 |                           0.997 |                0.177 |                0.99  |                     0.566 |                     0.738 |                     0.066 |                     0.984 |
| framing_competitive                     |                             0.319 |                             0.556 |                           0.119 |                           0.972 |                0.019 |                1     |                     0.034 |                     0.156 |                     0.006 |                     0.608 |
| framing_competitive_context[cheap_talk] |                             0.981 |                             0.972 |                           0.944 |                           1     |                1     |                1     |                     0.794 |                     0.25  |                     1     |                     0.902 |
| framing_competitive_context[no_comm]    |                             0.452 |                             0.553 |                           0.138 |                           0.862 |                0.088 |                0.887 |                     0.3   |                     0.455 |                     0.009 |                     0.969 |
| framing_team                            |                             0.68  |                             0.691 |                           0.997 |                           1     |                1     |                1     |                     0.973 |                     0.279 |                     1     |                     1     |
| framing_team_context[cheap_talk]        |                             0.994 |                             0.869 |                           0.997 |                           1     |                1     |                1     |                     0.99  |                     0.464 |                     1     |                     0.997 |
| framing_team_context[no_comm]           |                             0.883 |                             0.687 |                           0.938 |                           1     |                0.91  |                1     |                     0.988 |                     0.906 |                     0.641 |                     0.991 |
| no_comm                                 |                             0.568 |                             0.703 |                           0.109 |                           0.909 |                0.047 |                0.955 |                     0.178 |                     0.583 |                     0.278 |                     0.997 |
| no_sense                                |                             0.627 |                             0.741 |                           0.169 |                           0.931 |                0.95  |                0.991 |                     0.142 |                     0.461 |                     0.228 |                     0.922 |
| silence                                 |                             0.736 |                             0.649 |                           0.394 |                           0.988 |                0.873 |                0.991 |                     0.075 |                     0.633 |                     0.559 |                     0.981 |

## Cheap-talk Δ in cooperation (cheap_talk_x − no_comm)

| cell                                    |   ('Llama-3.1-8B-Instruct', 'pd') |   ('Llama-3.1-8B-Instruct', 'sh') |   ('Qwen2.5-7B-Instruct', 'pd') |   ('Qwen2.5-7B-Instruct', 'sh') |   ('Qwen3-4B', 'pd') |   ('Qwen3-4B', 'sh') |   ('gemma-2-2b-it', 'pd') |   ('gemma-2-2b-it', 'sh') |   ('gemma-2-9b-it', 'pd') |   ('gemma-2-9b-it', 'sh') |
|:----------------------------------------|----------------------------------:|----------------------------------:|--------------------------------:|--------------------------------:|---------------------:|---------------------:|--------------------------:|--------------------------:|--------------------------:|--------------------------:|
| baseline_cheap_talk                     |                             0.422 |                             0.213 |                           0.853 |                           0.091 |                0.953 |                0.045 |                     0.799 |                    -0.245 |                     0.722 |                    -0.053 |
| counterfactual                          |                             0.426 |                             0.26  |                           0.862 |                           0.091 |                0.953 |                0.045 |                    -0.131 |                    -0.205 |                     0.706 |                    -0.37  |
| framing_business                        |                             0.213 |                             0.084 |                           0.866 |                           0.091 |                0.953 |                0.045 |                     0.465 |                    -0.018 |                     0.722 |                    -0.003 |
| framing_business_context[cheap_talk]    |                             0.41  |                             0.226 |                           0.891 |                           0.091 |                0.953 |                0.045 |                     0.812 |                    -0.002 |                     0.722 |                     0.003 |
| framing_business_context[no_comm]       |                            -0.048 |                             0.028 |                           0.553 |                           0.087 |                0.13  |                0.035 |                     0.388 |                     0.155 |                    -0.213 |                    -0.012 |
| framing_competitive                     |                            -0.249 |                            -0.146 |                           0.009 |                           0.062 |               -0.028 |                0.045 |                    -0.144 |                    -0.427 |                    -0.272 |                    -0.389 |
| framing_competitive_context[cheap_talk] |                             0.413 |                             0.269 |                           0.834 |                           0.091 |                0.953 |                0.045 |                     0.616 |                    -0.333 |                     0.722 |                    -0.095 |
| framing_competitive_context[no_comm]    |                            -0.117 |                            -0.149 |                           0.028 |                          -0.047 |                0.041 |               -0.068 |                     0.122 |                    -0.128 |                    -0.269 |                    -0.028 |
| framing_team                            |                             0.112 |                            -0.012 |                           0.888 |                           0.091 |                0.953 |                0.045 |                     0.795 |                    -0.304 |                     0.722 |                     0.003 |
| framing_team_context[cheap_talk]        |                             0.426 |                             0.166 |                           0.888 |                           0.091 |                0.953 |                0.045 |                     0.812 |                    -0.119 |                     0.722 |                     0     |
| framing_team_context[no_comm]           |                             0.315 |                            -0.016 |                           0.828 |                           0.091 |                0.863 |                0.045 |                     0.809 |                     0.323 |                     0.362 |                    -0.006 |
| no_sense                                |                             0.058 |                             0.038 |                           0.059 |                           0.022 |                0.903 |                0.036 |                    -0.036 |                    -0.122 |                    -0.05  |                    -0.075 |
| silence                                 |                             0.167 |                            -0.053 |                           0.284 |                           0.078 |                0.826 |                0.036 |                    -0.103 |                     0.05  |                     0.281 |                    -0.016 |

## Hub minus leaf cooperation (within-star asymmetry)

| cell                                    |   ('Llama-3.1-8B-Instruct', 'pd') |   ('Llama-3.1-8B-Instruct', 'sh') |   ('Qwen2.5-7B-Instruct', 'pd') |   ('Qwen2.5-7B-Instruct', 'sh') |   ('Qwen3-4B', 'pd') |   ('Qwen3-4B', 'sh') |   ('gemma-2-2b-it', 'pd') |   ('gemma-2-2b-it', 'sh') |   ('gemma-2-9b-it', 'pd') |   ('gemma-2-9b-it', 'sh') |
|:----------------------------------------|----------------------------------:|----------------------------------:|--------------------------------:|--------------------------------:|---------------------:|---------------------:|--------------------------:|--------------------------:|--------------------------:|--------------------------:|
| baseline_cheap_talk                     |                             0.021 |                            -0.038 |                           0     |                           0     |                0     |                0     |                    -0.006 |                    -0.17  |                     0     |                     0.002 |
| counterfactual                          |                            -0.005 |                             0.029 |                           0.196 |                           0.008 |                0.004 |                0     |                    -0.048 |                     0.081 |                     0.175 |                     0.258 |
| framing_business                        |                             0.025 |                             0.075 |                          -0.008 |                           0     |                0     |                0     |                    -0.228 |                    -0.038 |                     0     |                     0.062 |
| framing_business_context[cheap_talk]    |                             0     |                             0.017 |                           0     |                           0     |                0     |                0     |                    -0.141 |                    -0.024 |                     0     |                     0.004 |
| framing_business_context[no_comm]       |                             0.033 |                            -0.082 |                          -0.017 |                           0     |               -0.034 |               -0.027 |                    -0.095 |                     0.071 |                    -0.029 |                     0     |
| framing_competitive                     |                             0.099 |                             0.066 |                          -0.004 |                           0.012 |               -0.008 |               -0.012 |                    -0.081 |                    -0.236 |                    -0.008 |                     0.006 |
| framing_competitive_context[cheap_talk] |                             0.021 |                             0.025 |                           0.017 |                           0     |                0     |                0     |                    -0.059 |                    -0.217 |                     0     |                     0.021 |
| framing_competitive_context[no_comm]    |                             0.007 |                             0.117 |                          -0.004 |                          -0.008 |               -0.028 |                0.022 |                    -0     |                    -0.042 |                    -0.021 |                    -0.008 |
| framing_team                            |                            -0     |                             0.021 |                           0.033 |                           0     |                0     |                0     |                     0.002 |                    -0.066 |                     0     |                     0.004 |
| framing_team_context[cheap_talk]        |                             0     |                             0.059 |                           0     |                           0     |                0     |                0     |                     0.001 |                    -0.235 |                     0     |                     0     |
| framing_team_context[no_comm]           |                             0.137 |                            -0.06  |                           0     |                           0     |               -0.012 |               -0.03  |                     0.033 |                     0.064 |                     0     |                    -0.004 |
| no_comm                                 |                             0.001 |                             0.005 |                          -0.029 |                           0.008 |                0.024 |               -0.005 |                     0.084 |                     0.229 |                     0.002 |                    -0.006 |
| no_sense                                |                             0.071 |                             0.098 |                          -0.088 |                          -0.012 |                0.088 |                0     |                    -0.035 |                    -0.063 |                     0.062 |                     0.187 |
| silence                                 |                             0.045 |                             0.058 |                          -0.037 |                           0.004 |               -0.033 |               -0.017 |                    -0.011 |                    -0.427 |                    -0.005 |                     0.008 |

## Hub exploitation rate (PD cheap-talk only)

| cell                                    |   ('Llama-3.1-8B-Instruct', 'pd') |   ('Qwen2.5-7B-Instruct', 'pd') |   ('Qwen3-4B', 'pd') |   ('gemma-2-2b-it', 'pd') |   ('gemma-2-9b-it', 'pd') |
|:----------------------------------------|----------------------------------:|--------------------------------:|---------------------:|--------------------------:|--------------------------:|
| baseline_cheap_talk                     |                             0     |                           0     |                    0 |                     0     |                     0     |
| counterfactual                          |                             0.051 |                           0.088 |                    0 |                     0.303 |                     0.075 |
| framing_business                        |                             0.138 |                           0     |                    0 |                     0.182 |                     0     |
| framing_business_context[cheap_talk]    |                             0.012 |                           0     |                    0 |                     0.025 |                     0     |
| framing_competitive                     |                             0.09  |                           0.062 |                    0 |                     0     |                     0.262 |
| framing_competitive_context[cheap_talk] |                             0.038 |                           0.088 |                    0 |                     0.025 |                     0     |
| framing_team                            |                             0.325 |                           0     |                    0 |                     0     |                     0     |
| framing_team_context[cheap_talk]        |                             0     |                           0     |                    0 |                     0.012 |                     0     |
| no_sense                                |                             0     |                           0     |                    0 |                     0     |                     0     |

## Detailed coop_rate with 95% bootstrap CI

| model | topology | scenario | game | n | coop% (95% CI) |
|---|---|---|---|---|---|
| Llama-3.1-8B-Instruct | cycle | baseline_cheap_talk | pd | 5 | 99.1% [97.8%, 100.0%] |
| Llama-3.1-8B-Instruct | cycle | counterfactual | pd | 5 | 99.4% [98.8%, 100.0%] |
| Llama-3.1-8B-Instruct | cycle | framing_business | pd | 5 | 78.1% [63.4%, 91.2%] |
| Llama-3.1-8B-Instruct | cycle | framing_business_context | pd | 5 | 97.8% [93.4%, 100.0%] |
| Llama-3.1-8B-Instruct | cycle | framing_business_context | pd | 5 | 52.0% [40.9%, 65.6%] |
| Llama-3.1-8B-Instruct | cycle | framing_competitive | pd | 5 | 31.9% [26.5%, 39.9%] |
| Llama-3.1-8B-Instruct | cycle | framing_competitive_context | pd | 5 | 98.1% [96.2%, 99.7%] |
| Llama-3.1-8B-Instruct | cycle | framing_competitive_context | pd | 5 | 45.2% [39.6%, 51.6%] |
| Llama-3.1-8B-Instruct | cycle | framing_team | pd | 5 | 68.0% [52.4%, 82.8%] |
| Llama-3.1-8B-Instruct | cycle | framing_team_context | pd | 5 | 99.4% [98.1%, 100.0%] |
| Llama-3.1-8B-Instruct | cycle | framing_team_context | pd | 5 | 88.3% [77.1%, 98.3%] |
| Llama-3.1-8B-Instruct | cycle | no_comm | pd | 5 | 56.8% [44.6%, 72.2%] |
| Llama-3.1-8B-Instruct | cycle | no_sense | pd | 5 | 62.7% [46.2%, 78.6%] |
| Llama-3.1-8B-Instruct | cycle | silence | pd | 5 | 73.6% [49.4%, 97.7%] |
| Llama-3.1-8B-Instruct | cycle | baseline_cheap_talk | sh | 5 | 91.6% [84.4%, 96.6%] |
| Llama-3.1-8B-Instruct | cycle | counterfactual | sh | 5 | 96.2% [94.7%, 98.1%] |
| Llama-3.1-8B-Instruct | cycle | framing_business | sh | 5 | 78.6% [73.8%, 82.9%] |
| Llama-3.1-8B-Instruct | cycle | framing_business_context | sh | 5 | 92.8% [86.6%, 97.8%] |
| Llama-3.1-8B-Instruct | cycle | framing_business_context | sh | 5 | 73.1% [63.1%, 80.4%] |
| Llama-3.1-8B-Instruct | cycle | framing_competitive | sh | 5 | 55.6% [50.0%, 59.1%] |
| Llama-3.1-8B-Instruct | cycle | framing_competitive_context | sh | 5 | 97.2% [94.7%, 99.4%] |
| Llama-3.1-8B-Instruct | cycle | framing_competitive_context | sh | 5 | 55.3% [46.8%, 60.4%] |
| Llama-3.1-8B-Instruct | cycle | framing_team | sh | 5 | 69.1% [65.3%, 73.4%] |
| Llama-3.1-8B-Instruct | cycle | framing_team_context | sh | 5 | 86.9% [80.6%, 93.1%] |
| Llama-3.1-8B-Instruct | cycle | framing_team_context | sh | 5 | 68.7% [62.6%, 74.6%] |
| Llama-3.1-8B-Instruct | cycle | no_comm | sh | 5 | 70.3% [61.1%, 77.8%] |
| Llama-3.1-8B-Instruct | cycle | no_sense | sh | 5 | 74.1% [64.7%, 81.9%] |
| Llama-3.1-8B-Instruct | cycle | silence | sh | 5 | 64.9% [52.0%, 76.7%] |
| Llama-3.1-8B-Instruct | star | baseline_cheap_talk | pd | 5 | 98.4% [95.9%, 100.0%] |
| Llama-3.1-8B-Instruct | star | counterfactual | pd | 5 | 95.3% [91.5%, 98.4%] |
| Llama-3.1-8B-Instruct | star | framing_business | pd | 5 | 69.4% [49.7%, 89.1%] |
| Llama-3.1-8B-Instruct | star | framing_business_context | pd | 5 | 98.8% [96.2%, 100.0%] |
| Llama-3.1-8B-Instruct | star | framing_business_context | pd | 5 | 59.5% [47.1%, 73.7%] |
| Llama-3.1-8B-Instruct | star | framing_competitive | pd | 5 | 36.1% [29.4%, 42.7%] |
| Llama-3.1-8B-Instruct | star | framing_competitive_context | pd | 5 | 94.7% [89.7%, 99.7%] |
| Llama-3.1-8B-Instruct | star | framing_competitive_context | pd | 5 | 27.6% [18.2%, 37.7%] |
| Llama-3.1-8B-Instruct | star | framing_team | pd | 5 | 67.5% [42.2%, 85.3%] |
| Llama-3.1-8B-Instruct | star | framing_team_context | pd | 5 | 100.0% [100.0%, 100.0%] |
| Llama-3.1-8B-Instruct | star | framing_team_context | pd | 5 | 69.9% [52.2%, 89.4%] |
| Llama-3.1-8B-Instruct | star | no_comm | pd | 5 | 47.0% [26.1%, 67.8%] |
| Llama-3.1-8B-Instruct | star | no_sense | pd | 5 | 48.4% [31.6%, 67.5%] |
| Llama-3.1-8B-Instruct | star | silence | pd | 5 | 32.9% [29.3%, 36.6%] |
| Llama-3.1-8B-Instruct | star | baseline_cheap_talk | sh | 5 | 95.3% [87.5%, 99.7%] |
| Llama-3.1-8B-Instruct | star | counterfactual | sh | 5 | 96.5% [95.3%, 98.4%] |
| Llama-3.1-8B-Instruct | star | framing_business | sh | 5 | 61.9% [49.7%, 77.2%] |
| Llama-3.1-8B-Instruct | star | framing_business_context | sh | 5 | 95.0% [92.5%, 96.9%] |
| Llama-3.1-8B-Instruct | star | framing_business_context | sh | 5 | 63.7% [51.6%, 76.3%] |
| Llama-3.1-8B-Instruct | star | framing_competitive | sh | 5 | 52.5% [50.6%, 54.4%] |
| Llama-3.1-8B-Instruct | star | framing_competitive_context | sh | 5 | 93.1% [89.4%, 96.9%] |
| Llama-3.1-8B-Instruct | star | framing_competitive_context | sh | 5 | 60.5% [54.3%, 66.0%] |
| Llama-3.1-8B-Instruct | star | framing_team | sh | 5 | 63.4% [53.8%, 74.4%] |
| Llama-3.1-8B-Instruct | star | framing_team_context | sh | 5 | 89.3% [78.1%, 98.0%] |
| Llama-3.1-8B-Instruct | star | framing_team_context | sh | 5 | 70.1% [55.6%, 80.4%] |
| Llama-3.1-8B-Instruct | star | no_comm | sh | 5 | 65.2% [59.0%, 72.6%] |
| Llama-3.1-8B-Instruct | star | no_sense | sh | 5 | 70.2% [61.8%, 80.0%] |
| Llama-3.1-8B-Instruct | star | silence | sh | 5 | 84.3% [78.1%, 91.2%] |
| Qwen2.5-7B-Instruct | cycle | baseline_cheap_talk | pd | 5 | 96.2% [88.8%, 100.0%] |
| Qwen2.5-7B-Instruct | cycle | counterfactual | pd | 5 | 97.2% [92.2%, 100.0%] |
| Qwen2.5-7B-Instruct | cycle | framing_business | pd | 5 | 97.5% [92.5%, 100.0%] |
| Qwen2.5-7B-Instruct | cycle | framing_business_context | pd | 5 | 100.0% [100.0%, 100.0%] |
| Qwen2.5-7B-Instruct | cycle | framing_business_context | pd | 5 | 66.2% [31.2%, 100.0%] |
| Qwen2.5-7B-Instruct | cycle | framing_competitive | pd | 5 | 11.9% [5.0%, 20.6%] |
| Qwen2.5-7B-Instruct | cycle | framing_competitive_context | pd | 5 | 94.4% [83.1%, 100.0%] |
| Qwen2.5-7B-Instruct | cycle | framing_competitive_context | pd | 5 | 13.8% [12.5%, 15.6%] |
| Qwen2.5-7B-Instruct | cycle | framing_team | pd | 5 | 99.7% [99.1%, 100.0%] |
| Qwen2.5-7B-Instruct | cycle | framing_team_context | pd | 5 | 99.7% [99.1%, 100.0%] |
| Qwen2.5-7B-Instruct | cycle | framing_team_context | pd | 5 | 93.8% [81.2%, 100.0%] |
| Qwen2.5-7B-Instruct | cycle | no_comm | pd | 5 | 10.9% [7.8%, 14.1%] |
| Qwen2.5-7B-Instruct | cycle | no_sense | pd | 5 | 16.9% [11.2%, 23.4%] |
| Qwen2.5-7B-Instruct | cycle | silence | pd | 5 | 39.4% [35.9%, 42.8%] |
| Qwen2.5-7B-Instruct | cycle | baseline_cheap_talk | sh | 5 | 100.0% [100.0%, 100.0%] |
| Qwen2.5-7B-Instruct | cycle | counterfactual | sh | 5 | 100.0% [100.0%, 100.0%] |
| Qwen2.5-7B-Instruct | cycle | framing_business | sh | 5 | 100.0% [100.0%, 100.0%] |
| Qwen2.5-7B-Instruct | cycle | framing_business_context | sh | 5 | 100.0% [100.0%, 100.0%] |
| Qwen2.5-7B-Instruct | cycle | framing_business_context | sh | 5 | 99.7% [99.1%, 100.0%] |
| Qwen2.5-7B-Instruct | cycle | framing_competitive | sh | 5 | 97.2% [93.8%, 99.7%] |
| Qwen2.5-7B-Instruct | cycle | framing_competitive_context | sh | 5 | 100.0% [100.0%, 100.0%] |
| Qwen2.5-7B-Instruct | cycle | framing_competitive_context | sh | 5 | 86.2% [79.7%, 93.1%] |
| Qwen2.5-7B-Instruct | cycle | framing_team | sh | 5 | 100.0% [100.0%, 100.0%] |
| Qwen2.5-7B-Instruct | cycle | framing_team_context | sh | 5 | 100.0% [100.0%, 100.0%] |
| Qwen2.5-7B-Instruct | cycle | framing_team_context | sh | 5 | 100.0% [100.0%, 100.0%] |
| Qwen2.5-7B-Instruct | cycle | no_comm | sh | 5 | 90.9% [86.6%, 95.3%] |
| Qwen2.5-7B-Instruct | cycle | no_sense | sh | 5 | 93.1% [91.2%, 95.9%] |
| Qwen2.5-7B-Instruct | cycle | silence | sh | 5 | 98.8% [96.2%, 100.0%] |
| Qwen2.5-7B-Instruct | star | baseline_cheap_talk | pd | 5 | 100.0% [100.0%, 100.0%] |
| Qwen2.5-7B-Instruct | star | counterfactual | pd | 5 | 76.6% [65.6%, 86.6%] |
| Qwen2.5-7B-Instruct | star | framing_business | pd | 5 | 98.1% [96.6%, 99.7%] |
| Qwen2.5-7B-Instruct | star | framing_business_context | pd | 5 | 100.0% [100.0%, 100.0%] |
| Qwen2.5-7B-Instruct | star | framing_business_context | pd | 5 | 65.0% [26.9%, 100.0%] |
| Qwen2.5-7B-Instruct | star | framing_competitive | pd | 5 | 32.8% [4.7%, 61.3%] |
| Qwen2.5-7B-Instruct | star | framing_competitive_context | pd | 5 | 88.8% [75.0%, 100.0%] |
| Qwen2.5-7B-Instruct | star | framing_competitive_context | pd | 5 | 11.6% [9.4%, 13.8%] |
| Qwen2.5-7B-Instruct | star | framing_team | pd | 5 | 97.5% [95.9%, 99.1%] |
| Qwen2.5-7B-Instruct | star | framing_team_context | pd | 5 | 100.0% [100.0%, 100.0%] |
| Qwen2.5-7B-Instruct | star | framing_team_context | pd | 5 | 100.0% [100.0%, 100.0%] |
| Qwen2.5-7B-Instruct | star | no_comm | pd | 5 | 8.4% [5.9%, 11.6%] |
| Qwen2.5-7B-Instruct | star | no_sense | pd | 5 | 11.6% [6.9%, 16.2%] |
| Qwen2.5-7B-Instruct | star | silence | pd | 5 | 42.8% [20.3%, 70.4%] |
| Qwen2.5-7B-Instruct | star | baseline_cheap_talk | sh | 5 | 100.0% [100.0%, 100.0%] |
| Qwen2.5-7B-Instruct | star | counterfactual | sh | 5 | 99.4% [98.8%, 100.0%] |
| Qwen2.5-7B-Instruct | star | framing_business | sh | 5 | 100.0% [100.0%, 100.0%] |
| Qwen2.5-7B-Instruct | star | framing_business_context | sh | 5 | 100.0% [100.0%, 100.0%] |
| Qwen2.5-7B-Instruct | star | framing_business_context | sh | 5 | 98.8% [96.2%, 100.0%] |
| Qwen2.5-7B-Instruct | star | framing_competitive | sh | 5 | 99.1% [97.8%, 100.0%] |
| Qwen2.5-7B-Instruct | star | framing_competitive_context | sh | 5 | 100.0% [100.0%, 100.0%] |
| Qwen2.5-7B-Instruct | star | framing_competitive_context | sh | 5 | 84.4% [77.2%, 89.4%] |
| Qwen2.5-7B-Instruct | star | framing_team | sh | 5 | 100.0% [100.0%, 100.0%] |
| Qwen2.5-7B-Instruct | star | framing_team_context | sh | 5 | 100.0% [100.0%, 100.0%] |
| Qwen2.5-7B-Instruct | star | framing_team_context | sh | 5 | 100.0% [100.0%, 100.0%] |
| Qwen2.5-7B-Instruct | star | no_comm | sh | 5 | 93.1% [87.5%, 97.5%] |
| Qwen2.5-7B-Instruct | star | no_sense | sh | 5 | 98.4% [97.5%, 99.4%] |
| Qwen2.5-7B-Instruct | star | silence | sh | 5 | 99.7% [99.1%, 100.0%] |
| Qwen3-4B | cycle | baseline_cheap_talk | pd | 5 | 100.0% [100.0%, 100.0%] |
| Qwen3-4B | cycle | counterfactual | pd | 5 | 100.0% [100.0%, 100.0%] |
| Qwen3-4B | cycle | framing_business | pd | 5 | 100.0% [100.0%, 100.0%] |
| Qwen3-4B | cycle | framing_business_context | pd | 5 | 100.0% [100.0%, 100.0%] |
| Qwen3-4B | cycle | framing_business_context | pd | 5 | 17.7% [6.7%, 38.0%] |
| Qwen3-4B | cycle | framing_competitive | pd | 5 | 1.9% [0.3%, 4.1%] |
| Qwen3-4B | cycle | framing_competitive_context | pd | 5 | 100.0% [100.0%, 100.0%] |
| Qwen3-4B | cycle | framing_competitive_context | pd | 5 | 8.8% [5.6%, 12.1%] |
| Qwen3-4B | cycle | framing_team | pd | 5 | 100.0% [100.0%, 100.0%] |
| Qwen3-4B | cycle | framing_team_context | pd | 5 | 100.0% [100.0%, 100.0%] |
| Qwen3-4B | cycle | framing_team_context | pd | 5 | 91.0% [73.1%, 100.0%] |
| Qwen3-4B | cycle | no_comm | pd | 5 | 4.7% [1.9%, 7.5%] |
| Qwen3-4B | cycle | no_sense | pd | 5 | 95.0% [91.6%, 98.4%] |
| Qwen3-4B | cycle | silence | pd | 5 | 87.3% [61.9%, 100.0%] |
| Qwen3-4B | cycle | baseline_cheap_talk | sh | 5 | 100.0% [100.0%, 100.0%] |
| Qwen3-4B | cycle | counterfactual | sh | 5 | 100.0% [100.0%, 100.0%] |
| Qwen3-4B | cycle | framing_business | sh | 5 | 100.0% [100.0%, 100.0%] |
| Qwen3-4B | cycle | framing_business_context | sh | 5 | 100.0% [100.0%, 100.0%] |
| Qwen3-4B | cycle | framing_business_context | sh | 5 | 99.0% [97.7%, 100.0%] |
| Qwen3-4B | cycle | framing_competitive | sh | 5 | 100.0% [100.0%, 100.0%] |
| Qwen3-4B | cycle | framing_competitive_context | sh | 5 | 100.0% [100.0%, 100.0%] |
| Qwen3-4B | cycle | framing_competitive_context | sh | 5 | 88.7% [79.9%, 97.1%] |
| Qwen3-4B | cycle | framing_team | sh | 5 | 100.0% [100.0%, 100.0%] |
| Qwen3-4B | cycle | framing_team_context | sh | 5 | 100.0% [100.0%, 100.0%] |
| Qwen3-4B | cycle | framing_team_context | sh | 5 | 100.0% [100.0%, 100.0%] |
| Qwen3-4B | cycle | no_comm | sh | 5 | 95.5% [92.5%, 98.0%] |
| Qwen3-4B | cycle | no_sense | sh | 5 | 99.1% [97.2%, 100.0%] |
| Qwen3-4B | cycle | silence | sh | 5 | 99.1% [98.4%, 99.7%] |
| Qwen3-4B | star | baseline_cheap_talk | pd | 5 | 100.0% [100.0%, 100.0%] |
| Qwen3-4B | star | counterfactual | pd | 5 | 99.7% [99.1%, 100.0%] |
| Qwen3-4B | star | framing_business | pd | 5 | 100.0% [100.0%, 100.0%] |
| Qwen3-4B | star | framing_business_context | pd | 5 | 100.0% [100.0%, 100.0%] |
| Qwen3-4B | star | framing_business_context | pd | 5 | 25.0% [4.6%, 56.4%] |
| Qwen3-4B | star | framing_competitive | pd | 5 | 0.6% [0.0%, 1.9%] |
| Qwen3-4B | star | framing_competitive_context | pd | 5 | 100.0% [100.0%, 100.0%] |
| Qwen3-4B | star | framing_competitive_context | pd | 5 | 7.0% [3.4%, 10.8%] |
| Qwen3-4B | star | framing_team | pd | 5 | 100.0% [100.0%, 100.0%] |
| Qwen3-4B | star | framing_team_context | pd | 5 | 100.0% [100.0%, 100.0%] |
| Qwen3-4B | star | framing_team_context | pd | 5 | 96.3% [88.9%, 100.0%] |
| Qwen3-4B | star | no_comm | pd | 5 | 3.7% [1.0%, 6.4%] |
| Qwen3-4B | star | no_sense | pd | 5 | 92.2% [85.0%, 99.1%] |
| Qwen3-4B | star | silence | pd | 5 | 70.0% [40.0%, 100.0%] |
| Qwen3-4B | star | baseline_cheap_talk | sh | 5 | 100.0% [100.0%, 100.0%] |
| Qwen3-4B | star | counterfactual | sh | 5 | 100.0% [100.0%, 100.0%] |
| Qwen3-4B | star | framing_business | sh | 5 | 100.0% [100.0%, 100.0%] |
| Qwen3-4B | star | framing_business_context | sh | 5 | 100.0% [100.0%, 100.0%] |
| Qwen3-4B | star | framing_business_context | sh | 5 | 84.9% [63.9%, 98.3%] |
| Qwen3-4B | star | framing_competitive | sh | 5 | 98.4% [96.2%, 100.0%] |
| Qwen3-4B | star | framing_competitive_context | sh | 5 | 100.0% [100.0%, 100.0%] |
| Qwen3-4B | star | framing_competitive_context | sh | 5 | 81.3% [71.3%, 91.9%] |
| Qwen3-4B | star | framing_team | sh | 5 | 100.0% [100.0%, 100.0%] |
| Qwen3-4B | star | framing_team_context | sh | 5 | 100.0% [100.0%, 100.0%] |
| Qwen3-4B | star | framing_team_context | sh | 5 | 98.4% [97.1%, 99.7%] |
| Qwen3-4B | star | no_comm | sh | 5 | 95.5% [90.9%, 99.7%] |
| Qwen3-4B | star | no_sense | sh | 5 | 100.0% [100.0%, 100.0%] |
| Qwen3-4B | star | silence | sh | 5 | 98.8% [96.2%, 100.0%] |
| gemma-2-2b-it | cycle | baseline_cheap_talk | pd | 5 | 97.7% [96.1%, 99.0%] |
| gemma-2-2b-it | cycle | counterfactual | pd | 5 | 4.8% [2.5%, 7.3%] |
| gemma-2-2b-it | cycle | framing_business | pd | 5 | 64.3% [53.1%, 75.1%] |
| gemma-2-2b-it | cycle | framing_business_context | pd | 5 | 99.0% [97.6%, 100.0%] |
| gemma-2-2b-it | cycle | framing_business_context | pd | 5 | 56.6% [32.2%, 80.6%] |
| gemma-2-2b-it | cycle | framing_competitive | pd | 5 | 3.4% [0.3%, 7.1%] |
| gemma-2-2b-it | cycle | framing_competitive_context | pd | 5 | 79.4% [48.9%, 98.7%] |
| gemma-2-2b-it | cycle | framing_competitive_context | pd | 5 | 30.0% [11.2%, 57.5%] |
| gemma-2-2b-it | cycle | framing_team | pd | 5 | 97.3% [95.2%, 99.4%] |
| gemma-2-2b-it | cycle | framing_team_context | pd | 5 | 99.0% [98.4%, 99.7%] |
| gemma-2-2b-it | cycle | framing_team_context | pd | 5 | 98.8% [97.2%, 100.0%] |
| gemma-2-2b-it | cycle | no_comm | pd | 5 | 17.8% [11.2%, 25.3%] |
| gemma-2-2b-it | cycle | no_sense | pd | 5 | 14.2% [8.1%, 20.9%] |
| gemma-2-2b-it | cycle | silence | pd | 5 | 7.5% [1.5%, 16.2%] |
| gemma-2-2b-it | cycle | baseline_cheap_talk | sh | 5 | 33.8% [25.7%, 42.0%] |
| gemma-2-2b-it | cycle | counterfactual | sh | 5 | 37.8% [29.4%, 52.5%] |
| gemma-2-2b-it | cycle | framing_business | sh | 5 | 56.5% [48.2%, 65.9%] |
| gemma-2-2b-it | cycle | framing_business_context | sh | 5 | 58.1% [54.1%, 62.1%] |
| gemma-2-2b-it | cycle | framing_business_context | sh | 5 | 73.8% [68.1%, 80.6%] |
| gemma-2-2b-it | cycle | framing_competitive | sh | 5 | 15.6% [11.9%, 18.8%] |
| gemma-2-2b-it | cycle | framing_competitive_context | sh | 5 | 25.0% [16.9%, 33.9%] |
| gemma-2-2b-it | cycle | framing_competitive_context | sh | 5 | 45.5% [34.1%, 53.0%] |
| gemma-2-2b-it | cycle | framing_team | sh | 5 | 27.9% [19.0%, 36.9%] |
| gemma-2-2b-it | cycle | framing_team_context | sh | 5 | 46.4% [29.7%, 62.7%] |
| gemma-2-2b-it | cycle | framing_team_context | sh | 5 | 90.6% [88.8%, 92.5%] |
| gemma-2-2b-it | cycle | no_comm | sh | 5 | 58.3% [48.3%, 65.6%] |
| gemma-2-2b-it | cycle | no_sense | sh | 5 | 46.1% [41.0%, 52.9%] |
| gemma-2-2b-it | cycle | silence | sh | 5 | 63.3% [54.3%, 74.2%] |
| gemma-2-2b-it | star | baseline_cheap_talk | pd | 5 | 98.0% [93.9%, 100.0%] |
| gemma-2-2b-it | star | counterfactual | pd | 5 | 6.5% [2.9%, 11.2%] |
| gemma-2-2b-it | star | framing_business | pd | 5 | 63.8% [48.9%, 78.8%] |
| gemma-2-2b-it | star | framing_business_context | pd | 5 | 95.4% [88.2%, 100.0%] |
| gemma-2-2b-it | star | framing_business_context | pd | 5 | 36.1% [25.2%, 46.6%] |
| gemma-2-2b-it | star | framing_competitive | pd | 5 | 7.6% [3.0%, 12.3%] |
| gemma-2-2b-it | star | framing_competitive_context | pd | 5 | 81.6% [53.4%, 99.7%] |
| gemma-2-2b-it | star | framing_competitive_context | pd | 5 | 32.5% [11.2%, 65.6%] |
| gemma-2-2b-it | star | framing_team | pd | 5 | 98.6% [97.4%, 99.7%] |
| gemma-2-2b-it | star | framing_team_context | pd | 5 | 98.6% [97.6%, 99.7%] |
| gemma-2-2b-it | star | framing_team_context | pd | 5 | 97.5% [94.1%, 99.7%] |
| gemma-2-2b-it | star | no_comm | pd | 5 | 67.5% [34.7%, 92.2%] |
| gemma-2-2b-it | star | no_sense | pd | 5 | 26.1% [16.7%, 35.6%] |
| gemma-2-2b-it | star | silence | pd | 5 | 3.9% [1.1%, 8.4%] |
| gemma-2-2b-it | star | baseline_cheap_talk | sh | 5 | 22.6% [14.6%, 30.6%] |
| gemma-2-2b-it | star | counterfactual | sh | 5 | 44.4% [36.7%, 52.9%] |
| gemma-2-2b-it | star | framing_business | sh | 5 | 58.6% [45.0%, 71.1%] |
| gemma-2-2b-it | star | framing_business_context | sh | 5 | 70.9% [56.3%, 86.8%] |
| gemma-2-2b-it | star | framing_business_context | sh | 5 | 79.3% [73.1%, 84.4%] |
| gemma-2-2b-it | star | framing_competitive | sh | 5 | 22.7% [11.2%, 35.5%] |
| gemma-2-2b-it | star | framing_competitive_context | sh | 5 | 40.5% [26.1%, 51.6%] |
| gemma-2-2b-it | star | framing_competitive_context | sh | 5 | 56.9% [48.8%, 65.3%] |
| gemma-2-2b-it | star | framing_team | sh | 5 | 18.8% [13.9%, 23.6%] |
| gemma-2-2b-it | star | framing_team_context | sh | 5 | 73.0% [61.9%, 82.1%] |
| gemma-2-2b-it | star | framing_team_context | sh | 5 | 80.2% [69.6%, 86.6%] |
| gemma-2-2b-it | star | no_comm | sh | 5 | 64.8% [55.3%, 71.1%] |
| gemma-2-2b-it | star | no_sense | sh | 5 | 36.8% [25.0%, 49.0%] |
| gemma-2-2b-it | star | silence | sh | 5 | 59.0% [48.1%, 69.9%] |
| gemma-2-9b-it | cycle | baseline_cheap_talk | pd | 5 | 100.0% [100.0%, 100.0%] |
| gemma-2-9b-it | cycle | counterfactual | pd | 5 | 98.4% [97.2%, 99.7%] |
| gemma-2-9b-it | cycle | framing_business | pd | 5 | 100.0% [100.0%, 100.0%] |
| gemma-2-9b-it | cycle | framing_business_context | pd | 5 | 100.0% [100.0%, 100.0%] |
| gemma-2-9b-it | cycle | framing_business_context | pd | 5 | 6.6% [3.1%, 10.6%] |
| gemma-2-9b-it | cycle | framing_competitive | pd | 5 | 0.6% [0.0%, 1.9%] |
| gemma-2-9b-it | cycle | framing_competitive_context | pd | 5 | 100.0% [100.0%, 100.0%] |
| gemma-2-9b-it | cycle | framing_competitive_context | pd | 5 | 0.9% [0.0%, 2.2%] |
| gemma-2-9b-it | cycle | framing_team | pd | 5 | 100.0% [100.0%, 100.0%] |
| gemma-2-9b-it | cycle | framing_team_context | pd | 5 | 100.0% [100.0%, 100.0%] |
| gemma-2-9b-it | cycle | framing_team_context | pd | 5 | 64.1% [27.2%, 100.0%] |
| gemma-2-9b-it | cycle | no_comm | pd | 5 | 27.8% [8.8%, 63.8%] |
| gemma-2-9b-it | cycle | no_sense | pd | 5 | 22.8% [10.9%, 41.2%] |
| gemma-2-9b-it | cycle | silence | pd | 5 | 55.9% [21.2%, 90.6%] |
| gemma-2-9b-it | cycle | baseline_cheap_talk | sh | 5 | 94.4% [83.1%, 100.0%] |
| gemma-2-9b-it | cycle | counterfactual | sh | 5 | 62.7% [50.1%, 76.1%] |
| gemma-2-9b-it | cycle | framing_business | sh | 5 | 99.4% [98.8%, 100.0%] |
| gemma-2-9b-it | cycle | framing_business_context | sh | 5 | 100.0% [100.0%, 100.0%] |
| gemma-2-9b-it | cycle | framing_business_context | sh | 5 | 98.4% [96.2%, 100.0%] |
| gemma-2-9b-it | cycle | framing_competitive | sh | 5 | 60.8% [47.6%, 73.9%] |
| gemma-2-9b-it | cycle | framing_competitive_context | sh | 5 | 90.2% [71.1%, 100.0%] |
| gemma-2-9b-it | cycle | framing_competitive_context | sh | 5 | 96.9% [95.6%, 98.1%] |
| gemma-2-9b-it | cycle | framing_team | sh | 5 | 100.0% [100.0%, 100.0%] |
| gemma-2-9b-it | cycle | framing_team_context | sh | 5 | 99.7% [99.1%, 100.0%] |
| gemma-2-9b-it | cycle | framing_team_context | sh | 5 | 99.1% [97.8%, 100.0%] |
| gemma-2-9b-it | cycle | no_comm | sh | 5 | 99.7% [99.1%, 100.0%] |
| gemma-2-9b-it | cycle | no_sense | sh | 5 | 92.2% [81.2%, 99.7%] |
| gemma-2-9b-it | cycle | silence | sh | 5 | 98.1% [95.0%, 100.0%] |
| gemma-2-9b-it | star | baseline_cheap_talk | pd | 10 | 100.0% [100.0%, 100.0%] |
| gemma-2-9b-it | star | counterfactual | pd | 5 | 78.1% [67.5%, 86.2%] |
| gemma-2-9b-it | star | framing_business | pd | 5 | 100.0% [100.0%, 100.0%] |
| gemma-2-9b-it | star | framing_business_context | pd | 5 | 100.0% [100.0%, 100.0%] |
| gemma-2-9b-it | star | framing_business_context | pd | 5 | 9.7% [2.5%, 17.5%] |
| gemma-2-9b-it | star | framing_competitive | pd | 5 | 1.9% [0.9%, 2.8%] |
| gemma-2-9b-it | star | framing_competitive_context | pd | 5 | 100.0% [100.0%, 100.0%] |
| gemma-2-9b-it | star | framing_competitive_context | pd | 5 | 2.8% [1.2%, 4.4%] |
| gemma-2-9b-it | star | framing_team | pd | 5 | 100.0% [100.0%, 100.0%] |
| gemma-2-9b-it | star | framing_team_context | pd | 5 | 100.0% [100.0%, 100.0%] |
| gemma-2-9b-it | star | framing_team_context | pd | 5 | 100.0% [100.0%, 100.0%] |
| gemma-2-9b-it | star | no_comm | pd | 10 | 8.0% [5.0%, 10.9%] |
| gemma-2-9b-it | star | no_sense | pd | 5 | 9.1% [6.2%, 13.4%] |
| gemma-2-9b-it | star | silence | pd | 5 | 30.4% [10.0%, 65.3%] |
| gemma-2-9b-it | star | baseline_cheap_talk | sh | 10 | 99.8% [99.5%, 100.0%] |
| gemma-2-9b-it | star | counterfactual | sh | 5 | 72.6% [56.4%, 87.2%] |
| gemma-2-9b-it | star | framing_business | sh | 5 | 95.3% [87.8%, 100.0%] |
| gemma-2-9b-it | star | framing_business_context | sh | 5 | 99.7% [99.1%, 100.0%] |
| gemma-2-9b-it | star | framing_business_context | sh | 5 | 100.0% [100.0%, 100.0%] |
| gemma-2-9b-it | star | framing_competitive | sh | 5 | 60.8% [51.5%, 70.6%] |
| gemma-2-9b-it | star | framing_competitive_context | sh | 5 | 98.4% [97.2%, 99.7%] |
| gemma-2-9b-it | star | framing_competitive_context | sh | 5 | 59.4% [32.8%, 85.9%] |
| gemma-2-9b-it | star | framing_team | sh | 5 | 80.9% [42.8%, 100.0%] |
| gemma-2-9b-it | star | framing_team_context | sh | 5 | 100.0% [100.0%, 100.0%] |
| gemma-2-9b-it | star | framing_team_context | sh | 5 | 99.1% [97.2%, 100.0%] |
| gemma-2-9b-it | star | no_comm | sh | 10 | 93.0% [81.7%, 99.4%] |
| gemma-2-9b-it | star | no_sense | sh | 5 | 72.2% [47.2%, 90.0%] |
| gemma-2-9b-it | star | silence | sh | 5 | 99.4% [98.8%, 100.0%] |
