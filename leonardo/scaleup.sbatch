#!/bin/bash
# Scale-up campaign: Qwen2.5 and Qwen3, small and 32B, PD on the star,
# 25 rounds, one model per A100 (an array task per model).
#
# Submit from $CT_BASE ($WORK/$USER), so the log lands in $CT_BASE/logs:
#     cd $WORK/$USER
#     sbatch cheaptalk_bench/leonardo/scaleup.sbatch                 # all four models
#     sbatch --array=2,3 cheaptalk_bench/leonardo/scaleup.sbatch     # only the 32B pair
#     N_RUNS=1 sbatch --array=2 --time=02:00:00 cheaptalk_bench/leonardo/scaleup.sbatch   # pilot
#
# Six cells per model, the ones that carry the thesis's findings:
#   session A, baseline: no_comm + baseline_cheap_talk           (RQ1, anchor)
#   session B: framing_team, framing_competitive                 (harm, deception)
#   session C, cheap_talk arm: framing_team_context,
#              framing_competitive_context                       (RQ3, deception)
#
# Held fixed against the 2,610-run corpus: 4-bit NF4, the prompts, memory 10,
# T=0.7, the hidden horizon. Changed on purpose: 25 rounds, and one token
# budget (512) for every model and cell, so the budget is not a confound
# here the way it was between the plain and context framings.
#
#SBATCH --job-name=ct_scaleup
#SBATCH --account=euhpc_d35_176
#SBATCH --partition=boost_usr_prod
#SBATCH --qos=normal
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=120G
#SBATCH --time=24:00:00
#SBATCH --array=0-3
#SBATCH --output=logs/%x_%A_%a.out

set -u
CT_BASE="${CT_BASE:-$WORK/$USER}"
source "$CT_BASE/cheaptalk_bench/leonardo/env.sh"
cd "$CT_BASE/cheaptalk_bench"

MODELS=(
    Qwen/Qwen2.5-7B-Instruct
    Qwen/Qwen3-4B
    Qwen/Qwen2.5-32B-Instruct
    Qwen/Qwen3-32B
)
MODEL=${MODELS[$SLURM_ARRAY_TASK_ID]}
N_RUNS=${N_RUNS:-5}
N_ROUNDS=${N_ROUNDS:-25}
OUT=${OUT:-$CT_BASE/results/scaleup_r${N_ROUNDS}}
mkdir -p "$OUT"

echo "job $SLURM_JOB_ID task $SLURM_ARRAY_TASK_ID on $(hostname): $MODEL"
echo "runs=$N_RUNS rounds=$N_ROUNDS out=$OUT"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
git log --oneline -1
python -c "import torch, transformers, bitsandbytes as b; print('torch', torch.__version__, '| transformers', transformers.__version__, '| bnb', b.__version__)"

COMMON=(--model "$MODEL" --topology star --games pd
        --n-runs "$N_RUNS" --n-rounds "$N_ROUNDS" --max-new-tokens 512
        --out-root "$OUT" --zip-mirror "")
FAILED=0
python campaign.py "${COMMON[@]}" --session A --scenarios baseline || FAILED=1
python campaign.py "${COMMON[@]}" --session B --scenarios framing_team framing_competitive || FAILED=1
python campaign.py "${COMMON[@]}" --session C \
    --scenarios framing_team_context framing_competitive_context \
    --conditions cheap_talk || FAILED=1

echo "done: $MODEL failed=$FAILED"
exit $FAILED
