# MMLU Evidence Gate Report

## 1. Executive Summary

Real HELM MMLU prediction data now exists for a 39-model public-artifact panel. The expanded matrix is complete and passes panel validity: 39 models, 14,042 items, 0 missing cells, and ability spread 0.5802.

Quick proxy IRT has now run on the 39-model wide matrix. It is proxy-only: no Rasch/1PL optimizer, no Bayesian IRT, and no full parametric 2PL. MMLU-Redux labels remain aligned to HELM item ids at 370/370 labels using sanitized subject + source row index matching. Validation of both the earlier baseline matrix flag and the new proxy-IRT flags remains weak, so the allowed claim is limited to protocol-scoped weak-signal reporting.

Issue-type-specific MMLU-Redux validation has also been implemented. It initially found one narrow raw enrichment for `label_error` with `correct_answer_rarely_selected`, but subject-normalized validation weakened that signal. A focused 1000-iteration label-error subject-matched null found limited top-k review-queue hints but weak AUROC/AUPRC and low recall. Broad, issue-specific, subject-normalized, and null-confirmation evidence do not authorize a generic MMLU error-detection claim. The publication-facing summary is `paper/appendices/mmlu_redux_evidence_appendix.md`.

No model inference, paid APIs, mock files, or raw MMLU question text were used.

## 2. Inputs

- Real normalized wide predictions: `data/external/mmlu/prediction_details_wide.jsonl`
- Imported predictions: `cache/mmlu/wide/predictions.jsonl`
- Matrix: `cache/mmlu/wide/matrix.csv`
- Normalized Redux labels: `data/ground_truth/mmlu_redux_issues.normalized.jsonl`
- HELM-aligned Redux labels: `data/ground_truth/mmlu_redux_issues.helm_aligned.jsonl`
- Matrix shape: 39 models x 14,042 items
- Missing cells: 0
- Redux labels: 370 issue-label rows across 49 subjects

No raw MMLU question text is included in this report.

## 3. Panel Validity

Command:

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

Result:

- Status: `pass`
- Models: 39
- Items: 14,042
- Ability spread: 0.5802
- Accuracy std: 0.1209
- Missing fraction: 0.0000
- Near-chance fraction: 0.0256
- Blockers: none

Decision: model-count and ability-spread gates are cleared. IRT is eligible by panel validity, and quick proxy IRT has now been run separately.

## 4. Redux Label Schema

Schema report files:

- `results/mmlu/redux_alignment/schema_report.md`
- `results/mmlu/redux_alignment/schema_report.json`

Findings:

- Redux item id format: `mmlu_redux2_{subject}_{zero_padded_source_row_index}`
- HELM prediction item id format: `mmlu_{subject}_id{helm_instance_number}`
- Direct item id matches: 0
- Subject overlap: 49 subjects
- Subject + numeric index alignment possible: yes
- Stable metadata alignment possible: no
- Hash alignment possible: no

## 5. Redux-to-HELM Alignment

Command:

```bash
python3 -m valideval align-mmlu-redux \
  --predictions cache/mmlu/wide/predictions.jsonl \
  --redux data/ground_truth/mmlu_redux_issues.normalized.jsonl \
  --output data/ground_truth/mmlu_redux_issues.helm_aligned.jsonl \
  --report results/mmlu/redux_alignment/alignment_report.md
```

Runtime:

```text
real 4.55
user 4.14
sys 0.34
```

Result:

- Status: `ok`
- Total Redux labels: 370
- Output rows: 370
- Aligned labels: 370
- Unaligned labels: 0
- Aligned fraction: 1.000
- Alignment method counts:
  - `subject_numeric_index`: 370
- Confidence distribution:
  - `0.85`: 370

Important limitation: alignment depends on the assumption that MMLU-Redux source row order matches HELM MMLU test item order within each subject. This is sanitized structural alignment, not direct-id, stable-metadata, or hash-confirmed alignment.

## 6. Validation Run Status

Because panel validity passed, MMLU-Redux validation was rerun:

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

Pipeline status: `ok`

## 7. Results, If Authorized

These are authorized only as protocol-scoped external-validation numbers, not as a global MMLU validity claim and not as evidence of successful MMLU error detection.

Quick proxy IRT command:

```bash
python3 -m valideval fit-irt \
  --matrix cache/mmlu/wide/matrix.csv \
  --model proxy \
  --output results/mmlu/irt \
  --strict
```

Proxy IRT status:

- Status: `ok`
- Output: `results/mmlu/irt`
- Proxy-only: yes
- Full parametric 2PL: not run
- Negative discrimination items: 1,037
- Near-zero discrimination items: 1,342
- Extreme difficulty items: 2,676

Proxy-IRT flag export:

- Output: `results/mmlu/flags.jsonl`
- Unique flagged items: 4,106
- Diagnostic rows: 9,161
- Separate groups: negative discrimination, low discrimination, extreme difficulty, combined flags

MMLU-Redux validation by proxy-IRT group:

| Diagnostic | AUROC | AUPRC | Precision@10 | Precision@25 | Precision@50 |
|---|---:|---:|---:|---:|---:|
| combined_flags | 0.495 | 0.030 | 0.000 | 0.000 | 0.020 |
| extreme_difficulty | 0.496 | 0.028 | 0.000 | 0.000 | 0.020 |
| low_discrimination | 0.538 | 0.032 | 0.000 | 0.000 | 0.020 |
| negative_discrimination | 0.493 | 0.041 | 0.000 | 0.000 | 0.020 |

Subject-filtered validation did not materially change the conclusion. Combined flags subject-filtered AUROC is 0.498, AUPRC is 0.035, Precision@10 is 0.000, and Precision@25 is 0.000.

Earlier baseline matrix-derived flag:

- Flags: 14,042
- Ground-truth issue items: 370
- Diagnostic: `matrix_item_anomaly`
- AUROC: 0.539
- AUPRC: 0.029
- Precision@10: 0.000
- Recall@10: 0.000
- Enrichment over random: 0.000

Interpretation: both the baseline `matrix_item_anomaly` flag and the proxy-IRT flags show weak association with the currently aligned MMLU-Redux labels under this protocol.

Issue-type-specific validation:

```bash
python3 -m valideval mmlu-redux-issue-validation \
  --predictions cache/mmlu/wide/predictions.jsonl \
  --matrix cache/mmlu/wide/matrix.csv \
  --ground-truth data/ground_truth/mmlu_redux_issues.helm_aligned.jsonl \
  --mapping configs/validation/mmlu_redux_issue_mapping.yaml \
  --output results/mmlu/redux_issue_specific_validation
```

Outputs:

- `results/mmlu/redux_issue_type_analysis/issue_taxonomy.md`
- `configs/validation/mmlu_redux_issue_mapping.yaml`
- `results/mmlu/redux_issue_specific_validation/issue_type_metrics.json`
- `results/mmlu/redux_issue_specific_validation_subject_filtered/issue_type_metrics.json`
- `results/mmlu/redux_issue_specific_validation_high_severity/issue_type_metrics.json`
- `MMLU_REDUX_ISSUE_SPECIFIC_VALIDATION_REPORT.md`

Issue-specific interpretation: most issue-type/diagnostic pairs remain weak. Raw `label_error` with `correct_answer_rarely_selected` showed preliminary enrichment under structural alignment, but the stricter subject-normalized version weakened to AUROC 0.515, AUPRC 0.011, and Precision@10 0.000 in the Redux-subject-filtered universe.

Subject-normalized validation:

```bash
python3 -m valideval mmlu-redux-issue-validation \
  --predictions cache/mmlu/wide/predictions.jsonl \
  --matrix cache/mmlu/wide/matrix.csv \
  --ground-truth data/ground_truth/mmlu_redux_issues.helm_aligned.jsonl \
  --mapping configs/validation/mmlu_redux_issue_mapping.yaml \
  --output results/mmlu/redux_issue_specific_validation_subject_normalized \
  --restrict-to-ground-truth-subjects \
  --subject-normalize \
  --subject-matched-null 100 \
  --min-positive-count 20
```

Subject-normalized outputs:

- `results/mmlu/redux_issue_specific_validation_subject_normalized/issue_type_metrics.json`
- `results/mmlu/redux_issue_specific_validation_subject_normalized/raw_vs_subject_normalized_comparison.md`
- `results/mmlu/redux_issue_specific_validation_subject_normalized/subject_matched_null.md`
- `MMLU_REDUX_SUBJECT_NORMALIZED_VALIDATION_REPORT.md`

Focused label-error null confirmation:

```bash
python3 -m valideval mmlu-redux-issue-validation \
  --predictions cache/mmlu/wide/predictions.jsonl \
  --matrix cache/mmlu/wide/matrix.csv \
  --ground-truth data/ground_truth/mmlu_redux_issues.helm_aligned.jsonl \
  --mapping configs/validation/mmlu_redux_issue_mapping.yaml \
  --output results/mmlu/redux_label_error_subject_matched_null_confirmatory \
  --restrict-to-ground-truth-subjects \
  --issue-type label_error \
  --diagnostics correct_answer_rarely_selected,correct_answer_rarely_selected_subject_z,high_disagreement,high_disagreement_subject_z,option_selection_anomaly,option_selection_anomaly_subject_z \
  --subject-normalize \
  --subject-matched-null 1000 \
  --min-positive-count 20
```

Focused null outputs:

- `results/mmlu/redux_label_error_subject_matched_null_confirmatory/null_comparison.md`
- `results/mmlu/redux_label_error_subject_matched_null_confirmatory/subject_matched_null.md`
- `MMLU_REDUX_LABEL_ERROR_NULL_CONFIRMATION_REPORT.md`
- `paper/appendices/mmlu_redux_evidence_appendix.md`
- `paper/appendices/mmlu_redux_reviewer_summary.md`

## 8. What Can Be Claimed

- Real public HELM MMLU predictions were acquired for 39 selected public-artifact models.
- The active wide matrix is complete: 39 models x 14,042 items, 0 missing cells.
- Panel validity passed under the current gate.
- Quick proxy IRT ran successfully and wrote `results/mmlu/irt`.
- Proxy-IRT flags were exported with sanitized diagnostic provenance.
- MMLU-Redux labels were structurally aligned to HELM item ids at 370/370 labels using subject + source row index.
- MMLU-Redux validation ran successfully against the aligned labels.
- The current baseline matrix-derived flag has weak measured association with aligned Redux labels: AUROC 0.539, AUPRC 0.029.
- The current proxy-IRT flags also have weak measured association with aligned Redux labels: combined AUROC 0.495, AUPRC 0.030, Precision@10 0.000.
- Issue-specific validation ran using local matrix-derived diagnostics and sanitized outputs only.
- Subject-normalized validation ran using local matrix-derived diagnostics and sanitized outputs only.
- The previous raw `label_error` signal weakened after subject normalization, suggesting possible subject-difficulty confounding.
- Focused label-error subject-matched null confirmation ran with 1000 iterations and supports only limited review-queue hints.
- MMLU-Redux can be described as a negative/weak external-validation stress test.

## 9. What Cannot Be Claimed

- Do not claim MMLU is valid or invalid.
- Do not claim general MMLU error detection.
- Do not claim the Redux alignment is direct-id, stable-metadata, or hash-confirmed.
- Do not call proxy IRT full psychometric IRT or full 2PL.
- Do not call the weak proxy-IRT validation numbers a success.
- Do not call the narrow `label_error` issue-specific result generic MMLU error detection.
- Do not claim the raw `label_error` result survived subject normalization.
- Do not claim the focused null confirms label-error detection.
- Do not describe MMLU-Redux as positive validation evidence in the paper.
- Do not treat one baseline diagnostic as a complete validity profile.

## 10. Remaining Blockers

- Full psychometric IRT / full 2PL has not been run.
- Redux alignment is structural and should be upgraded to direct-id or hash-confirmed alignment if possible.
- Stronger issue-type-specific diagnostics and alignment confirmation are needed before making any detection-performance claim.
- Subject-normalized validation weakens the narrow raw label-error signal; the focused null supports only review-queue-scoped hints.
- Stronger positive evidence must come from synthetic cross-flaw validation, held-out synthetic generators, or future direct/hash-confirmed external ground truth.
- Public HELM artifacts include some non-A-D raw prediction strings; matrix correctness uses HELM `exact_match` correctness.

## 11. Next Data Needed

- A direct MMLU-Redux-to-MMLU item id map, or stable question/choice hashes on both sides.
- Optional additional public model artifacts if a broader than 39-model panel is desired.
- Direct/hash-confirmed alignment and any authorized prompt/extraction-sensitivity inputs before stronger external-validation claims.

## 12. Next Commands

The next best command is to inspect the focused null comparison:

```bash
sed -n '1,120p' results/mmlu/redux_label_error_subject_matched_null_confirmatory/null_comparison.md
```
