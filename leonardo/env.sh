# Environment for every Leonardo job and download. Source it, do not run it:
#     source leonardo/env.sh
#
# Layout (one-time setup: leonardo/setup_env.sh):
#     $CT_BASE/cheaptalk_bench   this repo
#     $CT_BASE/venv              Python environment (torch, transformers, bitsandbytes)
#     $CT_BASE/results           run files, one tree per campaign
#     $CT_BASE/logs              Slurm logs
#     $SCRATCH/hf_cache          model weights. $SCRATCH has room (200 TB) but
#                                deletes files unused for 40 days: re-download
#                                after a long pause, never keep results there.
module load python/3.11.7 >/dev/null 2>&1

export CT_BASE="${CT_BASE:-$WORK/$USER}"
export HF_HOME="${HF_HOME:-$SCRATCH/hf_cache}"
source "$CT_BASE/venv/bin/activate"

export PYTHONUNBUFFERED=1
export TOKENIZERS_PARALLELISM=false
# Compute nodes read the weights from HF_HOME and never reach the Hub: a
# missing model then fails at once instead of hanging on the network.
# download_models.sh turns these off for itself.
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
