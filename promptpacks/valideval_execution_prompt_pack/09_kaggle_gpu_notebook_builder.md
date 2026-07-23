# Prompt 09 — Kaggle GPU Notebook Builder

## Objective

Create a Kaggle GPU notebook package if local CPU/public artifacts cannot produce the needed panel.

This prompt creates notebooks and packaging; it does not run Kaggle locally.

## Create

```text
kaggle/
kaggle/valideval_lm_eval_panel_runner.ipynb
kaggle/README_KAGGLE_PANEL_RUN.md
kaggle/kaggle_requirements.txt
kaggle/panel_models_small.yaml
kaggle/panel_models_medium.yaml
kaggle/panel_tasks.yaml
kaggle/IMPORT_KAGGLE_OUTPUTS.md
scripts/package_kaggle_valideval.py
```

## Notebook requirements

The notebook must:

1. check environment/GPU,
2. install minimal dependencies,
3. define model/task config,
4. run lm-eval-harness or equivalent,
5. normalize predictions JSONL,
6. build matrix CSV,
7. write manifest JSON,
8. checkpoint/resume,
9. zip outputs,
10. explain import back into ValidEval.

## Suggested models

Use open feasible models:

- Qwen2.5-0.5B-Instruct,
- Qwen2.5-1.5B-Instruct,
- Qwen2.5-3B-Instruct,
- TinyLlama-1.1B,
- Phi-3 mini if feasible,
- Gemma open models if license-compatible,
- Mistral-7B quantized only if feasible.

Do not include API keys or paid models.

## Tasks

Support selected tasks:

- MMLU subset,
- chosen second benchmark,
- GPQA only if extraction is robust,
- GSM8K/TruthfulQA only if scoring is deterministic.

## Report

```text
KAGGLE_NOTEBOOK_BUILD_REPORT.md
```

Final verdict:

```text
KAGGLE_NOTEBOOK_READY_FOR_USER_RUN
KAGGLE_NOTEBOOK_NEEDS_FIXES
KAGGLE_NOTEBOOK_BLOCKED
```

## Verification

```bash
python3 - <<'PY'
import json
from pathlib import Path
p = Path("kaggle/valideval_lm_eval_panel_runner.ipynb")
nb = json.loads(p.read_text())
print("cells", len(nb.get("cells", [])))
assert nb.get("nbformat") == 4
PY

ruff check .
python3 -m pytest -q
```
