# Prompt 10 — Import Kaggle Outputs and Validate Matrix

Run this after Kaggle output ZIPs are available under `kaggle_outputs/`.

## Objective

Import Kaggle-generated outputs, validate schema, build matrix, run panel validity, and run downstream analysis only if the gate passes.

## Steps

### Inspect ZIPs

```bash
find kaggle_outputs -maxdepth 2 -type f | sort
```

### Create manifest

Create:

```text
KAGGLE_OUTPUT_IMPORT_MANIFEST.md
```

List ZIP path, size, SHA-256, task, expected models, expected rows.

### Extract safely

Extract into:

```text
data/external/kaggle_imported/<run_id>/
```

Do not overwrite prior imports.

### Validate/import

```bash
python3 -m valideval import-wide-predictions   --input data/external/kaggle_imported/<run_id>/predictions.jsonl   --output cache/<benchmark>/wide/predictions.jsonl   --strict

python3 -m valideval matrix-from-wide-predictions   --input cache/<benchmark>/wide/predictions.jsonl   --output cache/<benchmark>/wide/matrix.csv   --strict

python3 -m valideval panel-validity   --matrix cache/<benchmark>/wide/matrix.csv   --output results/<benchmark>/panel_validity   --strict
```

If gate passes:

```bash
python3 -m valideval real-panel-ranking-audit   --matrix cache/<benchmark>/wide/matrix.csv   --predictions cache/<benchmark>/wide/predictions.jsonl   --output results/<benchmark>/real_panel_ranking_audit   --execute
```

## Report

```text
KAGGLE_OUTPUT_IMPORT_AND_VALIDATION_REPORT.md
```

Final verdict:

```text
KAGGLE_IMPORT_VALID_PANEL_READY
KAGGLE_IMPORT_PANEL_BLOCKED
KAGGLE_IMPORT_SCHEMA_BLOCKED
```

## Verification

```bash
ruff check .
python3 -m pytest -q
```
