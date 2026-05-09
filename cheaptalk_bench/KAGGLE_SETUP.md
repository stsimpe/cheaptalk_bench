# Running the cheap-talk benchmark on Kaggle (free 30 h/week T4 GPU)

## One-time setup

1. **GitHub**: push this repo to GitHub so Kaggle can clone it.
   ```bash
   cd cheaptalk_bench
   git init && git add . && git commit -m "cheaptalk benchmark"
   # create new repo at github.com/<you>/cheaptalk_bench (public is fine, .env is gitignored)
   git remote add origin https://github.com/<you>/cheaptalk_bench.git
   git push -u origin main
   ```

2. **Kaggle**:
   - Create a Kaggle account at https://kaggle.com
   - Go to https://www.kaggle.com/settings → **Phone verification**. This unlocks GPU.
   - (Optional, only for gated models) Add a Kaggle Secret named `HF_TOKEN`
     containing your HuggingFace token (from https://huggingface.co/settings/tokens).

3. **Model gating** (only matters for Llama/Gemma — Qwen is open):
   - Llama: visit https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct →
     "Agree and access repository" → wait up to 24h for Meta approval.
   - Gemma: visit each model page → click "Acknowledge license" (instant).

## Running a sweep

1. Open https://www.kaggle.com/code → **New Notebook** → upload `kaggle_runner.ipynb`.
2. Right panel → **Settings**: Accelerator = `GPU T4 x2`, Internet = `On`.
3. Cell 2: edit `GITHUB_REPO` to your repo URL.
4. Cell 4: pick which `MODEL` you want to run (one per session is cleanest).
5. Run cells 1–4 (smoke test). If smoke passes, run cell 4's full sweep.
6. Cell 5: zip and download from the Output panel.
7. Cell 6: optional on-Kaggle analysis.

## Estimated wall-time on T4 (per full sweep = 1,920 model calls)

| Model size      | Wall-time | 30 h/week budget covers |
|-----------------|-----------|-------------------------|
| 2–4B            | ~30 min   | 60 model sweeps/week    |
| 7–9B (8-bit)    | 1.5–2 h   | 15+ models/week         |
| 14B (4-bit)     | ~3 h      | 10 models/week          |
| 70B             | n/a       | does not fit on T4      |

## Recommended model rotation for the thesis

For a cross-model robustness statement at thesis quality, run these 4 across
2 weeks:

| Model                                 | Family   | Size  | Why |
|---------------------------------------|----------|-------|-----|
| Qwen/Qwen2.5-7B-Instruct              | Alibaba  | 7B    | open, baseline |
| meta-llama/Llama-3.1-8B-Instruct      | Meta     | 8B    | Sabani anchor   |
| google/gemma-2-9b-it                  | Google   | 9B    | 3rd family      |
| Qwen/Qwen2.5-3B-Instruct              | Alibaba  | 3B    | size effect    |

Save each model's outputs to `results/<model-short-name>/` so analysis groups
by model_id cleanly.
