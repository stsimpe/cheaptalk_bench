#!/bin/bash
# Download model weights into $HF_HOME, on a login node (compute nodes have
# no Hub access).  Usage:
#     bash leonardo/download_models.sh Qwen/Qwen2.5-32B-Instruct Qwen/Qwen3-32B
# With no arguments it fetches the scale-up set.
#
# Login nodes kill a process after 10 minutes of CPU time. hf_transfer keeps
# the CPU cost of a 65 GB download well under that; if a download is cut
# anyway, run the same command again: the Hub client resumes, it does not
# start over.
set -e
source "$(dirname "$0")/env.sh"
unset HF_HUB_OFFLINE TRANSFORMERS_OFFLINE
export HF_HUB_ENABLE_HF_TRANSFER=1

MODELS=("$@")
[ ${#MODELS[@]} -gt 0 ] || MODELS=(
    Qwen/Qwen2.5-7B-Instruct
    Qwen/Qwen3-4B
    Qwen/Qwen2.5-32B-Instruct
    Qwen/Qwen3-32B
)
for m in "${MODELS[@]}"; do
    echo "=== $m"
    # Weights, config and tokenizer only: no .bin duplicates, no GGUF.
    huggingface-cli download "$m" \
        --include "*.json" "*.safetensors" "*.model" "*.txt" "*.tiktoken" \
        > /dev/null
    du -sh "$HF_HOME/hub/models--${m//\//--}"
done
