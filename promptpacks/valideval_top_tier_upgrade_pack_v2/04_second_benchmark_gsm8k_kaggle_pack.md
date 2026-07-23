# Prompt 04 — GSM8K Second Benchmark Kaggle Execution Pack

## Objective

Add a second benchmark with deterministic scoring and high paper value: GSM8K.

This is the most important ceiling-raising prompt after MMLU.

## Why GSM8K

- deterministic answer extraction,
- well-known benchmark,
- reasoning construct differs from MMLU,
- lm-eval-harness support,
- easier than GPQA for extraction reliability,
- feasible on Kaggle with small/medium open models.

## Create package

```text
kaggle_gsm8k/
kaggle_gsm8k/valideval_gsm8k_panel_runner.ipynb
kaggle_gsm8k/README_GSM8K_KAGGLE.md
kaggle_gsm8k/gsm8k_models_small.yaml
kaggle_gsm8k/gsm8k_models_medium.yaml
kaggle_gsm8k/import_schema.json
kaggle_gsm8k/EXPECTED_OUTPUTS.md
```

## Notebook requirements

The notebook must:

1. Install lm-eval-harness or use repo-normalized runner.
2. Run GSM8K on selected open models.
3. Support resumable shards.
4. Export normalized predictions JSONL.
5. Export matrix CSV.
6. Export manifest JSON.
7. Zip outputs for local import.
8. Avoid API keys.
9. Avoid paid models.
10. Record model names, revision/hash where possible.

## Model panel

Start small but expandable:

- Qwen2.5-0.5B-Instruct
- Qwen2.5-1.5B-Instruct
- Qwen2.5-3B-Instruct
- TinyLlama-1.1B
- Phi-3 mini if available
- Gemma-2-2B if accessible
- Mistral-7B-Instruct quantized if feasible
- other small open models available on Kaggle

If fewer than 10 models are feasible, say so.

## Local import command placeholders

```bash
python3 -m valideval import-wide-predictions   --benchmark gsm8k   --input data/external/kaggle_imported/gsm8k/predictions.jsonl   --output cache/gsm8k/wide/predictions.jsonl   --strict

python3 -m valideval matrix-from-wide-predictions   --input cache/gsm8k/wide/predictions.jsonl   --output cache/gsm8k/wide/matrix.csv   --strict

python3 -m valideval panel-validity   --matrix cache/gsm8k/wide/matrix.csv   --output results/gsm8k/panel_validity   --strict
```

## Report

Create:

```text
GSM8K_KAGGLE_EXECUTION_PACK_REPORT.md
```

Final verdict:

```text
GSM8K_KAGGLE_PACK_READY
GSM8K_PACK_NEEDS_FIXES
GSM8K_PACK_BLOCKED
```

## Verification

```bash
python3 - <<'PY'
import json
from pathlib import Path
p = Path("kaggle_gsm8k/valideval_gsm8k_panel_runner.ipynb")
nb = json.loads(p.read_text())
assert nb["nbformat"] == 4
print("cells", len(nb["cells"]))
PY
ruff check .
python3 -m pytest -q
```
