#!/bin/bash
# One-time setup on a Leonardo login node: repo, venv and output folders.
#     bash setup_env.sh        (from anywhere; the repo is cloned if missing)
#
# cineca-ai ships transformers 4.38, too old for Qwen3 (needs >= 4.51), and
# no bitsandbytes, so the campaign uses its own venv. Versions are pinned so
# every run of the campaign records the same stack.
set -e
CT_BASE="${CT_BASE:-$WORK/$USER}"
mkdir -p "$CT_BASE/results" "$CT_BASE/logs"
cd "$CT_BASE"
[ -d cheaptalk_bench ] || git clone -q https://github.com/stsimpe/cheaptalk_bench.git

module load python/3.11.7
[ -d venv ] || python3 -m venv venv
source venv/bin/activate
pip install -q --upgrade pip
pip install -q torch==2.5.1 --index-url https://download.pytorch.org/whl/cu121
pip install -q "transformers==4.57.1" "accelerate>=1.0" "bitsandbytes>=0.45" \
    pandas scipy matplotlib python-dotenv openai "huggingface_hub[hf_transfer]"
python - <<'PY'
import torch, transformers, accelerate, bitsandbytes, huggingface_hub
print("torch", torch.__version__, "cuda", torch.version.cuda)
print("transformers", transformers.__version__, "| accelerate", accelerate.__version__,
      "| bitsandbytes", bitsandbytes.__version__, "| hub", huggingface_hub.__version__)
PY
echo "SETUP_OK  base=$CT_BASE"
