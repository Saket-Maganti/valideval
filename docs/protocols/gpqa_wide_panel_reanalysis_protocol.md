# GPQA Wide-Panel Reanalysis Protocol

Small local GPQA panels are protocol demonstrations only. A paper-facing GPQA reanalysis requires:

- at least 50 models or model snapshots
- full GPQA item coverage where permitted locally
- substantial ability spread beyond chance
- low missingness
- source-validity metadata for prediction details
- public artifacts that do not expose raw GPQA question text

Use `python3 -m valideval gpqa-wide-readiness --predictions cache/gpqa/wide/predictions.jsonl --matrix cache/gpqa/wide/matrix.csv`.
