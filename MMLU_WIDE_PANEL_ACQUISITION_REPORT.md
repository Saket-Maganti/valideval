# MMLU Wide Panel Acquisition Report

## 1. Executive Summary

Expanded real MMLU per-instance prediction details were acquired from public HELM MMLU `v1.13.0` artifacts without model inference. The new normalized wide file contains 39 complete selected models, each covering the same 14,042 MMLU items across 57 subjects.

The active cache was rebuilt from this file, and strict panel validity now passes. MMLU-Redux validation was rerun after the panel passed, but the resulting baseline diagnostic association is weak and should not be overclaimed.

No mock/example files, model inference, Ollama, paid APIs, or raw MMLU question text were used.

## 2. Starting State

- Previous normalized file: `data/external/mmlu/prediction_details.jsonl`
- Previous active imported predictions: `cache/mmlu/wide/predictions.jsonl`
- Previous active matrix: `cache/mmlu/wide/matrix.csv`
- Previous matrix shape: 3 models x 14,042 items
- Previous panel validity: blocked by `model_count_below_30` and `ability_spread_too_narrow`
- Redux alignment: 370/370 labels, `subject_numeric_index`, confidence 0.85

Backups before active-cache overwrite:

- `data/external/mmlu/backups/three_model_prediction_details_20260612T160228Z.jsonl`
- `cache/mmlu/wide/backups/three_model_predictions_20260612T160228Z.jsonl`
- `cache/mmlu/wide/backups/three_model_matrix_20260612T160228Z.csv`

## 3. Source Discovery

Discovery command:

```bash
python3 scripts/discover_helm_mmlu_runs.py \
  --output-json results/mmlu/helm_wide_acquisition/discovery_report.json \
  --output-md results/mmlu/helm_wide_acquisition/discovery_report.md
```

Runtime:

```text
real 56.72
user 0.39
sys 0.10
```

Discovery result:

- Source: HELM MMLU public benchmark output
- Source page: `https://crfm.stanford.edu/helm/mmlu/latest/`
- HELM release: `v1.13.0`
- Candidate models: 79
- Complete by release manifest: 79
- Partial by release manifest: 0
- Default selected public-artifact models: 39
- Excluded by default policy: 40
- Expected items per complete model: 14,042

The default selection excluded known closed or paid API provider prefixes when enough public-artifact models were available.

## 4. Compatibility Checks

Compatibility report:

- `results/mmlu/helm_wide_acquisition/compatibility_report.md`
- `results/mmlu/helm_wide_acquisition/compatibility_report.json`

Compatibility result:

- Status: `ok`
- Same HELM release: true
- Same 57 subjects: true
- Same item IDs: true
- Same gold labels: true
- Complete models: 39
- Partial selected models: 0
- Duplicate rows: 0
- Invalid gold labels: 0
- Empty prediction rows after normalization: 0
- Invalid prediction labels: 1,331

The invalid prediction-label count means some public HELM `predicted_text` values were not A-D. This does not block the correctness matrix because HELM `exact_match` correctness is present and gold labels are valid. Twelve blank prediction values were normalized to `UNMAPPED` before import.

## 5. Expanded Prediction File

Acquisition command:

```bash
python3 scripts/acquire_helm_mmlu_wide_panel.py
```

Runtime:

```text
real 1600.67
user 18.89
sys 2.12
```

Expanded file:

- Path: `data/external/mmlu/prediction_details_wide.jsonl`
- Models: 39
- Items per model: 14,042
- Subjects: 57
- Rows: 547,638
- Partial selected models: 0
- SHA-256: `38485dc89aa44f44cd5f8078df246d76aad3570ce15295559fa0a72d6f9379c6`
- Raw question text persisted: no

## 6. Import And Matrix Build

Import command:

```bash
python3 -m valideval import-published-details \
  --benchmark mmlu \
  --input data/external/mmlu/prediction_details_wide.jsonl \
  --format auto \
  --output cache/mmlu/wide/predictions.jsonl \
  --mapping-report results/mmlu/helm_wide_acquisition/import_mapping_report.md
```

Runtime:

```text
real 16.48
user 14.97
sys 0.86
```

Import result:

- Status: `ok`
- Rows read: 547,638
- Rows written: 547,638
- Models: 39
- Items: 14,042
- Duplicate rows: 0
- Missing fields: 0
- SHA-256: `06e88501819f9ad3d7d5121f55adeaf89314f09d2c771559d9a7bed0a420dd54`

Matrix command:

```bash
python3 -m valideval matrix-from-wide-predictions \
  --predictions cache/mmlu/wide/predictions.jsonl \
  --output cache/mmlu/wide/matrix.csv \
  --report results/mmlu/helm_wide_acquisition/wide_matrix_report.md
```

Runtime:

```text
real 10.01
user 9.18
sys 0.55
```

Matrix result:

- Matrix: `cache/mmlu/wide/matrix.csv`
- Shape: 39 model rows x 14,042 item columns
- Missing cells: 0
- SHA-256: `f85a0a44f3203de2863d86bf13b2c81d8e934ae4c07b826193b5e93a3fc86e74`

## 7. Panel Validity

Strict panel-validity command:

```bash
python3 -m valideval panel-validity \
  --matrix cache/mmlu/wide/matrix.csv \
  --output results/mmlu/panel_validity \
  --strict
```

Runtime:

```text
real 0.65
user 0.43
sys 0.06
```

Panel result:

- Status: `pass`
- Models: 39
- Items: 14,042
- Missing fraction: 0.0000
- Ability spread: 0.5802
- Accuracy std: 0.1209
- Near-chance model fraction: 0.0256
- Blockers: none
- IRT eligible by panel gate: yes

## 8. Redux Validation Status

Redux alignment was refreshed against the active 39-model prediction cache:

- Aligned labels: 370 / 370
- Method: `subject_numeric_index`
- Confidence: 0.85
- Runtime: 4.55s

Redux validation command:

```bash
python3 -m valideval mmlu-redux-validation \
  --predictions cache/mmlu/wide/predictions.jsonl \
  --matrix cache/mmlu/wide/matrix.csv \
  --ground-truth data/ground_truth/mmlu_redux_issues.helm_aligned.jsonl \
  --output results/mmlu/redux_validation
```

Runtime:

```text
real 1.38
user 1.24
sys 0.08
```

Status: `ok`

Baseline validation metrics for `matrix_item_anomaly`:

- AUROC: 0.539
- AUPRC: 0.029
- Precision@10: 0.000
- Recall@10: 0.000
- Enrichment over random: 0.000

These metrics show weak association for this baseline flag and should not be presented as a detection success.

## 9. IRT Status

Quick proxy IRT has now been run on the active wide matrix:

```bash
python3 -m valideval fit-irt \
  --matrix cache/mmlu/wide/matrix.csv \
  --model proxy \
  --output results/mmlu/irt \
  --strict
```

Status: `ok`

- Output: `results/mmlu/irt`
- Proxy-only: yes
- Full parametric 2PL: not run
- Negative discrimination items: 1,037
- Near-zero discrimination items: 1,342
- Extreme difficulty items: 2,676

Proxy-IRT flags were exported to:

```bash
python3 -m valideval export-flags \
  --benchmark mmlu \
  --matrix cache/mmlu/wide/matrix.csv \
  --irt results/mmlu/irt \
  --output results/mmlu/flags.jsonl
```

Grouped Redux validation remains weak. Combined proxy-IRT flags have AUROC 0.495, AUPRC 0.030, Precision@10 0.000, and Precision@25 0.000. See `MMLU_REDUX_WEAK_SIGNAL_DIAGNOSIS.md`.

## 10. What Can Be Claimed

- Real public HELM MMLU prediction details were expanded to a 39-model panel.
- The expanded panel is complete for the same 14,042 item ids across the selected models.
- The active wide matrix has 39 models, 14,042 items, and 0 missing cells.
- Strict panel validity passes under the current ValidEval gate.
- Quick proxy IRT ran successfully and wrote `results/mmlu/irt`.
- Proxy-IRT flags were exported with sanitized diagnostic provenance.
- MMLU-Redux alignment remains 370/370 using sanitized subject + numeric index alignment.
- MMLU-Redux validation now runs with `status: ok` on the passed panel.
- Both the baseline `matrix_item_anomaly` flag and the proxy-IRT flags have weak association with aligned Redux labels under this protocol.

## 11. What Cannot Be Claimed

- Do not claim MMLU is valid or invalid.
- Do not claim generic MMLU error-detection success.
- Do not claim Redux alignment is direct-id or hash-confirmed.
- Do not call proxy IRT full psychometric IRT or full 2PL.
- Do not treat `matrix_item_anomaly` as a complete validity profile.
- Do not treat weak AUROC/AUPRC or top-k numbers as a success claim.

## 12. Remaining Blockers

- Full psychometric IRT / full 2PL has not been run.
- Redux alignment should ideally be upgraded to direct-id or hash-confirmed alignment.
- Stronger issue-type-specific diagnostics are needed before detection-performance claims.
- Large raw/cache artifacts should not be committed without explicit approval.

## 13. Next Commands

The next best protocol-safe command is a narrowed, subject-filtered validation of one proxy-IRT group:

```bash
python3 -m valideval validate-flags-against-ground-truth \
  --benchmark mmlu \
  --flags results/mmlu/flags_negative_discrimination.jsonl \
  --ground-truth data/ground_truth/mmlu_redux_issues.helm_aligned.jsonl \
  --output results/mmlu/redux_validation_negative_discrimination_subject_filtered \
  --restrict-to-ground-truth-subjects
```
