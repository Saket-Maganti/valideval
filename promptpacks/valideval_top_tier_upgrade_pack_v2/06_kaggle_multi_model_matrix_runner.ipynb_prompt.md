# Prompt 06 — General Kaggle Multi-Model Matrix Runner Notebook

## Objective

Build a reusable Kaggle notebook for any lm-eval-compatible benchmark.

## Create

```text
kaggle_general/
kaggle_general/valideval_multi_model_matrix_runner.ipynb
kaggle_general/README.md
kaggle_general/model_panels/
kaggle_general/task_configs/
kaggle_general/IMPORT_OUTPUTS.md
```

## Features

- Select task by config.
- Select model panel by YAML.
- Shard tasks/models.
- Resume partial outputs.
- Normalize predictions to ValidEval schema.
- Build matrix.
- Write manifest.
- Zip results.
- No secrets.
- No paid APIs.
- Works with Kaggle T4/P100.
- Optional quantization path if available.

## Output schema

Each prediction row:

```json
{
  "benchmark": "gsm8k",
  "model_id": "model/name",
  "item_id": "stable_id",
  "subject": "optional",
  "prediction": "sanitized",
  "gold": "sanitized_or_hash",
  "correct": true,
  "metadata": {}
}
```

Do not expose restricted raw text in public reports.

## Verification

Validate notebook JSON and create `GENERAL_KAGGLE_NOTEBOOK_BUILD_REPORT.md`.

Final verdict:

```text
GENERAL_KAGGLE_RUNNER_READY
GENERAL_KAGGLE_RUNNER_NEEDS_FIXES
```
