# Cross-Model Lexical Fingerprint

Top 8 content words per (model, scenario, game). Stopwords and `round/neighbor` removed.

## Scenario: `baseline_cheap_talk`

### Game: PD

|   rank | Llama-3.1-8B-Instruct   | Qwen2.5-7B-Instruct   | Qwen3-4B    | gemma-2-2b-it   | gemma-2-9b-it   |
|-------:|:------------------------|:----------------------|:------------|:----------------|:----------------|
|      1 | cooperate               | rewards               | mutual      | beneficial      | continuing      |
|      2 | maintain                | keep                  | continue    | mutually        | cooperate       |
|      3 | cooperating             | cooperating           | benefit     | building        | strategy        |
|      4 | cooperation             | cooperate             | cooperating | strong          | seems           |
|      5 | payoffs                 | maximum               | long        | positive        | cooperating     |
|      6 | continue                | long                  | term        | continue        | continue        |
|      7 | cooperative             | together              | cooperation | outcome         | beneficial      |
|      8 | beneficial              | term                  | maximize    | long            | keep            |

### Game: SH

|   rank | Llama-3.1-8B-Instruct   | Qwen2.5-7B-Instruct   | Qwen3-4B    | gemma-2-2b-it   | gemma-2-9b-it   |
|-------:|:------------------------|:----------------------|:------------|:----------------|:----------------|
|      1 | stag                    | rewards               | mutual      | strategy        | stag            |
|      2 | cooperate               | stag                  | stag        | outcome         | playing         |
|      3 | choose                  | together              | choosing    | seeking         | continue        |
|      4 | maintain                | keep                  | benefit     | strategies      | stick           |
|      5 | cooperative             | highest               | cooperation | game            | propose         |
|      6 | choosing                | maximum               | continue    | beneficial      | continued       |
|      7 | payoffs                 | continue              | payoff      | long            | well            |
|      8 | continue                | cooperating           | higher      | mutually        | keep            |

## Scenario: `counterfactual`

### Game: PD

|   rank | Llama-3.1-8B-Instruct   | Qwen2.5-7B-Instruct   | Qwen3-4B   | gemma-2-2b-it   | gemma-2-9b-it   |
|-------:|:------------------------|:----------------------|:-----------|:----------------|:----------------|
|      1 | cooperate               | cooperate             | defect     | defect          | cooperate       |
|      2 | payoff                  | again                 | trust      | higher          | streak          |
|      3 | cumulative              | earn                  | points     | payoff          | mutual          |
|      4 | increase                | streak                | gain       | likely          | defect          |
|      5 | reinforcing             | score                 | cooperate  | cooperate       | benefit         |
|      6 | setting                 | defect                | breaking   | score           | continue        |
|      7 | total                   | points                | sustained  | able            | positive        |
|      8 | cooperative             | gain                  | lose       | cooperating     | pattern         |

### Game: SH

|   rank | Llama-3.1-8B-Instruct   | Qwen2.5-7B-Instruct   | Qwen3-4B   | gemma-2-2b-it   | gemma-2-9b-it   |
|-------:|:------------------------|:----------------------|:-----------|:----------------|:----------------|
|      1 | choose                  | stag                  | hare       | hare            | hare            |
|      2 | stag                    | earn                  | chooses    | higher          | stag            |
|      3 | increase                | again                 | choose     | likely          | choose          |
|      4 | streak                  | chose                 | stag       | payoff          | streak          |
|      5 | payoffs                 | points                | lose       | stag            | continue        |
|      6 | cooperative             | choose                | gain       | choose          | chose           |
|      7 | payoff                  | before                | one        | score           | payoff          |
|      8 | cumulative              | continue              | keep       | defect          | played          |

## Scenario: `no_sense`

### Game: PD

|   rank | Llama-3.1-8B-Instruct   | Qwen2.5-7B-Instruct   | Qwen3-4B   | gemma-2-2b-it   | gemma-2-9b-it   |
|-------:|:------------------------|:----------------------|:-----------|:----------------|:----------------|
|      1 | birds                   | birds                 | birds      | birds           | birds           |
|      2 | fly                     | fly                   | fly        | fly             | fly             |
|      3 | earth                   | earth                 | earth      | earth           | earth           |
|      4 | time                    | time                  | time       | time            | time            |
|      5 | flies                   | flies                 | flies      | flies           | flies           |
|      6 | sunny                   | sunny                 | sunny      | like            | sunny           |
|      7 | day                     | day                   | day        | pizza           | day             |
|      8 | music                   | music                 | music      | sunny           | music           |

### Game: SH

|   rank | Llama-3.1-8B-Instruct   | Qwen2.5-7B-Instruct   | Qwen3-4B   | gemma-2-2b-it   | gemma-2-9b-it   |
|-------:|:------------------------|:----------------------|:-----------|:----------------|:----------------|
|      1 | birds                   | birds                 | birds      | birds           | birds           |
|      2 | fly                     | fly                   | fly        | fly             | fly             |
|      3 | earth                   | earth                 | earth      | earth           | earth           |
|      4 | time                    | time                  | time       | like            | time            |
|      5 | flies                   | flies                 | flies      | pizza           | flies           |
|      6 | sunny                   | sunny                 | sunny      | coffee          | sunny           |
|      7 | day                     | day                   | day        | morning         | day             |
|      8 | music                   | music                 | music      | time            | music           |

## Scenario: `framing_business`

### Game: PD

|   rank | Llama-3.1-8B-Instruct   | Qwen2.5-7B-Instruct   | Qwen3-4B    | gemma-2-2b-it   | gemma-2-9b-it   |
|-------:|:------------------------|:----------------------|:------------|:----------------|:----------------|
|      1 | contract                | returns               | partnership | investment      | investment      |
|      2 | returns                 | investment            | returns     | risk            | returns         |
|      3 | investment              | contract              | stable      | partnership     | continue        |
|      4 | risk                    | partnership           | cooperation | clear           | contract        |
|      5 | partnership             | ensures               | risk        | returns         | partnership     |
|      6 | mutual                  | risk                  | investment  | believe         | strategy        |
|      7 | joint                   | risks                 | mutual      | mutually        | continued       |
|      8 | commitment              | minimized             | ensure      | beneficial      | cooperative     |

### Game: SH

|   rank | Llama-3.1-8B-Instruct   | Qwen2.5-7B-Instruct   | Qwen3-4B    | gemma-2-2b-it   | gemma-2-9b-it   |
|-------:|:------------------------|:----------------------|:------------|:----------------|:----------------|
|      1 | contract                | returns               | returns     | investment      | investment      |
|      2 | investment              | partnership           | stag        | risk            | stag            |
|      3 | risk                    | stag                  | risk        | partnership     | returns         |
|      4 | returns                 | contract              | partnership | clear           | strategy        |
|      5 | partnership             | risk                  | investment  | returns         | partnership     |
|      6 | strategy                | investment            | through     | mutually        | consistent      |
|      7 | commitment              | high                  | ensure      | beneficial      | given           |
|      8 | joint                   | hunts                 | minimize    | long            | continued       |

## Scenario: `framing_competitive`

### Game: PD

|   rank | Llama-3.1-8B-Instruct   | Qwen2.5-7B-Instruct   | Qwen3-4B   | gemma-2-2b-it   | gemma-2-9b-it   |
|-------:|:------------------------|:----------------------|:-----------|:----------------|:----------------|
|      1 | edge                    | win                   | defect     | who             | win             |
|      2 | take                    | big                   | edge       | see             | expect          |
|      3 | compete                 | rivals                | advantage  | win             | competition     |
|      4 | win                     | edge                  | win        | ready           | advantage       |
|      5 | rival                   | defect                | secure     | truly           | contest         |
|      6 | fiercely                | compete               | rivals     | edge            | don             |
|      7 | cooperate               | stay                  | outcompete | prove           | compete         |
|      8 | don                     | fiercely              | maximum    | dominate        | edge            |

### Game: SH

|   rank | Llama-3.1-8B-Instruct   | Qwen2.5-7B-Instruct   | Qwen3-4B   | gemma-2-2b-it   | gemma-2-9b-it   |
|-------:|:------------------------|:----------------------|:-----------|:----------------|:----------------|
|      1 | take                    | win                   | edge       | who             | win             |
|      2 | edge                    | big                   | win        | see             | rival           |
|      3 | win                     | stay                  | stag       | ready           | don             |
|      4 | rival                   | stag                  | advantage  | win             | advantage       |
|      5 | compete                 | ahead                 | rivals     | edge            | edge            |
|      6 | time                    | edge                  | choose     | claim           | won             |
|      7 | outcompete              | rivals                | secure     | dominate        | compete         |
|      8 | who                     | compete               | fiercely   | victory         | competition     |

## Scenario: `framing_team`

### Game: PD

|   rank | Llama-3.1-8B-Instruct   | Qwen2.5-7B-Instruct   | Qwen3-4B    | gemma-2-2b-it   | gemma-2-9b-it   |
|-------:|:------------------------|:----------------------|:------------|:----------------|:----------------|
|      1 | together                | team                  | team        | together        | keep            |
|      2 | shared                  | together              | shared      | team            | together        |
|      3 | team                    | shared                | other       | shared          | team            |
|      4 | goal                    | goal                  | support     | achieve         | shared          |
|      5 | achieve                 | other                 | goal        | goal            | other           |
|      6 | work                    | achieve               | keep        | work            | goal            |
|      7 | maximizing              | support               | cooperating | other           | supporting      |
|      8 | score                   | reach                 | together    | support         | crushing        |

### Game: SH

|   rank | Llama-3.1-8B-Instruct   | Qwen2.5-7B-Instruct   | Qwen3-4B   | gemma-2-2b-it   | gemma-2-9b-it   |
|-------:|:------------------------|:----------------------|:-----------|:----------------|:----------------|
|      1 | together                | together              | shared     | together        | keep            |
|      2 | shared                  | shared                | team       | team            | team            |
|      3 | team                    | goal                  | stag       | shared          | stag            |
|      4 | work                    | team                  | maximum    | achieve         | together        |
|      5 | goal                    | other                 | together   | goal            | other           |
|      6 | achieve                 | achieve               | choose     | work            | supporting      |
|      7 | maximizing              | support               | keep       | other           | shared          |
|      8 | score                   | work                  | support    | success         | goal            |

