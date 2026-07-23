# Prompt 07 — Kaggle Import, Validate, and Merge

## Objective

Import Kaggle outputs once the user provides ZIPs.

## Expected inputs

```text
kaggle_outputs/*.zip
```

## Steps

1. Hash each ZIP.
2. Extract into versioned import folder.
3. Validate predictions schema.
4. Build matrix.
5. Run panel validity.
6. If gate passes, run ranking/baselines.
7. Merge with existing artifact manifest.
8. Update paper tables only if successful.

## Create

```text
KAGGLE_IMPORT_VALIDATE_MERGE_REPORT.md
```

Final verdict:

```text
KAGGLE_IMPORT_COMPLETE_PANEL_READY
KAGGLE_IMPORT_COMPLETE_PANEL_BLOCKED
KAGGLE_IMPORT_BLOCKED_NO_ZIPS
KAGGLE_IMPORT_SCHEMA_FAILED
```

## Verification

```bash
ruff check .
python3 -m pytest -q
```
