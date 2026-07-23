# ValidEval V5 Repository Forensic Inventory

Generated: `2026-07-16T06:30:16.505835+00:00`
Repository: `/Users/saketmaganti/Projects/Valideval`

## Git boundary

- Branch: `master`
- Commit: `None`
- Unborn repository: `True`
- Tracked files: `0`
- Untracked files: `3733`
- Ignored files: `23040`
- Consequence: no historical diff or code revision can be reconstructed from this checkout.

## Inventory

- Files outside `.git`: `26807`
- Bytes outside `.git`: `2628820305`
- Archives: `16`
- Cache/compiled files: `6285`
- Broken symlinks: `0`
- Secret scan: `pass_with_release_exclusion` (values are never printed)

## Taxonomy counts

- `CACHE`: 6285
- `CONFIG`: 85
- `DERIVED_EVIDENCE`: 2011
- `HISTORICAL`: 81
- `NON_EVIDENCE_FIXTURE`: 151
- `NORMALIZED_INPUT`: 225
- `NOTEBOOK`: 31
- `PAPER`: 165
- `RAW_INPUT`: 55
- `RELEASE`: 81
- `REPORT`: 1283
- `RUNBOOK`: 3
- `SOURCE`: 252
- `TEST`: 88
- `UNKNOWN`: 16011

## Largest files

- `cache/mmlu/wide/predictions.jsonl`: 692918942 bytes
- `data/external/mmlu/prediction_details_wide.jsonl`: 615154346 bytes
- `cache/mmlu/wide/backups/three_model_predictions_20260612T160228Z.jsonl`: 51922802 bytes
- `data/external/mmlu/prediction_details.jsonl`: 46151540 bytes
- `data/external/mmlu/backups/three_model_prediction_details_20260612T160228Z.jsonl`: 46151540 bytes
- `.venv-v5/lib/python3.11/site-packages/0aca9ce3d91742c5b361__mypyc.cpython-311-darwin.so`: 39710080 bytes
- `results/mmlu/redux_issue_specific_validation_subject_normalized/subject_normalized_item_scores.jsonl`: 24823804 bytes
- `.venv-v5/bin/ruff`: 23685696 bytes
- `results/mmlu/rank_materiality_v5/rank_materiality_summary.json`: 19423360 bytes
- `results/mmlu/redux_issue_specific_validation_subject_normalized/subject_normalized_item_scores.csv`: 13979841 bytes
- `results/mmlu/redux_label_error_subject_normalized/subject_normalized_item_scores.jsonl`: 12924430 bytes
- `results/mmlu/redux_label_error_subject_matched_null_confirmatory/subject_normalized_item_scores.jsonl`: 12924430 bytes
- `results/mmlu/redux_validation_by_group/joined.jsonl`: 9966800 bytes
- `results/mmlu/redux_validation_high_severity/joined.jsonl`: 9958928 bytes
- `results/mmlu/redux_validation_issue_label_error/joined.jsonl`: 9955799 bytes
- `results/mmlu/redux_validation_issue_ambiguous_question/joined.jsonl`: 9955471 bytes
- `results/mmlu/redux_validation_issue_multiple_correct/joined.jsonl`: 9952419 bytes
- `results/mmlu/redux_validation_issue_ambiguous_options/joined.jsonl`: 9952183 bytes
- `results/mmlu/redux_validation_issue_expert_flag/joined.jsonl`: 9951703 bytes
- `results/mmlu/redux_validation_issue_answer_error/joined.jsonl`: 9951700 bytes

## Release boundary

The working tree is preserved. Source, evidence, and reviewer releases must be built from explicit allowlists; caches, raw benchmark data, prompt-pack history, nested archives, compiled files, and secrets are excluded by default.

Status: `VERIFIED_FROM_PRIMARY_ARTIFACT` for the recorded filesystem state.
