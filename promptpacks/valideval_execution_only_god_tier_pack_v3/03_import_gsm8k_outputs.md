# Prompt 03 — Import GSM8K Outputs

## Objective

Import actual GSM8K Kaggle/Colab outputs. Stop if outputs do not exist.

## Search

```bash
find kaggle_outputs data/external . -maxdepth 5 -type f \( -name "*.zip" -o -name "*gsm8k*.jsonl" -o -name "*gsm8k*.csv" \) | sort
```

## If no outputs

Create:

```text
GSM8K_IMPORT_BLOCKED_NO_OUTPUTS.md
```

Final verdict:

```text
GSM8K_IMPORT_BLOCKED_NO_OUTPUTS
```

## Import process

1. Hash every candidate ZIP.
2. Extract into `data/external/kaggle_imported/gsm8k/<run_id>/`.
3. Validate schema.
4. Normalize predictions.
5. Build matrix.
6. Run panel validity.
7. Write manifest.

## Commands

Use existing commands if available; otherwise implement minimal importer.

```bash
mkdir -p data/external/kaggle_imported/gsm8k cache/gsm8k/wide results/gsm8k/panel_validity
python3 scripts/v2_top_tier_local.py kaggle-import || true
python3 -m valideval panel-validity --matrix cache/gsm8k/wide/matrix.csv --output results/gsm8k/panel_validity --strict
```

## Required outputs

```text
cache/gsm8k/wide/predictions.jsonl
cache/gsm8k/wide/matrix.csv
results/gsm8k/panel_validity/panel_validity.json
GSM8K_IMPORT_AND_VALIDATION_REPORT.md
```

## Final verdict

```text
GSM8K_PANEL_VALIDITY_PASS
GSM8K_PANEL_VALIDITY_PARTIAL
GSM8K_IMPORT_SCHEMA_FAILED
GSM8K_IMPORT_BLOCKED_NO_OUTPUTS
```
