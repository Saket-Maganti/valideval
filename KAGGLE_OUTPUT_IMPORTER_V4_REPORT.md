# Kaggle Output Importer V4 Report

Implemented command:

```bash
python3 -m valideval import-kaggle-outputs \
  --input-dir kaggle_outputs \
  --output-root data/external/kaggle_imported \
  --cache-root cache \
  --results-root results \
  --strict
```

Implemented behavior:

- Recursively discovers ZIP files under `kaggle_outputs/`.
- Hashes each ZIP with SHA256.
- Extracts into versioned import folders without overwriting old imports.
- Detects `gsm8k`, `bbh`, `truthfulqa`, and generic third-benchmark ZIPs.
- Strictly validates `predictions.jsonl` schema.
- Normalizes predictions using the existing wide-prediction importer.
- Builds `matrix.csv`.
- Copies current cache artifacts while backing up prior cache files if they differ.
- Runs panel validity.
- Writes per-import manifests and a no-ZIP blocked report.

Current repo state: no ZIPs exist under `kaggle_outputs/`, so the live run wrote `results/kaggle_import_v4/blocked_report.md` with `KAGGLE_IMPORT_BLOCKED_NO_ZIPS`.

Tests: `tests/test_kaggle_output_importer_v4.py`.

Final verdict: `KAGGLE_IMPORTER_V4_READY`
