# MMLU-Redux Label-Error Subject-Matched Null Confirmation Report

All findings here are preliminary and protocol-scoped. No raw MMLU question text or answer-choice text is included. MMLU-Redux alignment remains structural (`subject_numeric_index`, confidence 0.85), not direct-id or hash-confirmed alignment.

## 1. Executive Summary

A focused 1000-iteration subject-matched null baseline was run for `label_error` diagnostics only. No broad validation was rerun.

The result is mixed but still cautious. Raw `correct_answer_rarely_selected` remains above the subject-matched null at P@25, and some subject-normalized diagnostics show top-k cells above null. However, AUROC and AUPRC remain weak, recall is low, and the original subject-normalized `correct_answer_rarely_selected_subject_z` diagnostic still has P@10 0.000.

Under a 39-model HELM MMLU panel and structurally aligned MMLU-Redux labels, the current matrix-derived label-error diagnostics do not provide strong external validation. At most, they provide preliminary review-queue hints.

## 2. Motivation

The earlier raw `label_error + correct_answer_rarely_selected` signal weakened after subject normalization, suggesting subject-difficulty confounding. This confirmation run tests whether the focused label-error diagnostics beat a subject-matched random baseline when positives are resampled within the same subject count profile.

## 3. Inputs

- Matrix: `cache/mmlu/wide/matrix.csv`
- Predictions: `cache/mmlu/wide/predictions.jsonl`
- Ground truth: `data/ground_truth/mmlu_redux_issues.helm_aligned.jsonl`
- Mapping: `configs/validation/mmlu_redux_issue_mapping.yaml`
- Output: `results/mmlu/redux_label_error_subject_matched_null_confirmatory/`

Run scope:

- Issue type: `label_error`
- Positives: 106
- Evaluation universe: 6,500 items in label-error-covered subjects
- Null iterations: 1000
- Alignment confidence: 0.85

## 4. Diagnostics Tested

- `correct_answer_rarely_selected`
- `correct_answer_rarely_selected_subject_z`
- `high_disagreement`
- `high_disagreement_subject_z`
- `option_selection_anomaly`
- `option_selection_anomaly_subject_z`

No new diagnostics were added.

## 5. Subject-Matched Null Setup

For each null iteration, the protocol keeps the same number of `label_error` positives per subject and samples non-issue items from those same subjects. The observed ranking is then compared with this subject-matched random label assignment.

Artifacts:

- `results/mmlu/redux_label_error_subject_matched_null_confirmatory/subject_matched_null.json`
- `results/mmlu/redux_label_error_subject_matched_null_confirmatory/subject_matched_null.md`
- `results/mmlu/redux_label_error_subject_matched_null_confirmatory/null_comparison.json`
- `results/mmlu/redux_label_error_subject_matched_null_confirmatory/null_comparison.md`

Empirical p-values were not computed because the null artifact stores summary statistics rather than per-iteration draws.

## 6. Observed vs Null Results

| Diagnostic | AUROC | AUPRC | P@10 | Null mean P@10 | Null 95% P@10 | P@25 | Null mean P@25 | Null 95% P@25 | R@10 | R@25 | R@50 | Decision |
|---|---:|---:|---:|---:|---|---:|---:|---|---:|---:|---:|---|
| `correct_answer_rarely_selected` | 0.569 | 0.033 | 0.200 | 0.036 | [0.000, 0.200] | 0.120 | 0.022 | [0.000, 0.080] | 0.019 | 0.028 | 0.028 | above null top-k |
| `correct_answer_rarely_selected_subject_z` | 0.518 | 0.022 | 0.000 | 0.006 | [0.000, 0.100] | 0.120 | 0.007 | [0.000, 0.040] | 0.000 | 0.028 | 0.038 | above null at P@25 |
| `high_disagreement` | 0.511 | 0.023 | 0.000 | 0.040 | [0.000, 0.200] | 0.040 | 0.033 | [0.000, 0.120] | 0.000 | 0.009 | 0.019 | mean only |
| `high_disagreement_subject_z` | 0.525 | 0.021 | 0.000 | 0.005 | [0.000, 0.100] | 0.080 | 0.005 | [0.000, 0.040] | 0.000 | 0.019 | 0.019 | above null at P@25 |
| `option_selection_anomaly` | 0.552 | 0.025 | 0.000 | 0.058 | [0.000, 0.200] | 0.000 | 0.037 | [0.000, 0.120] | 0.000 | 0.000 | 0.028 | not above null |
| `option_selection_anomaly_subject_z` | 0.524 | 0.023 | 0.200 | 0.005 | [0.000, 0.100] | 0.080 | 0.007 | [0.000, 0.040] | 0.019 | 0.019 | 0.019 | above null top-k |

## 7. Raw vs Subject-Normalized Interpretation

Raw `correct_answer_rarely_selected` still shows top-k enrichment against the subject-matched null, especially P@25. This may be useful as a review-queue heuristic.

The subject-normalized diagnostics do not produce strong ranking evidence. Some subject-z top-k cells exceed the null baseline, especially `option_selection_anomaly_subject_z` at P@10/P@25 and `correct_answer_rarely_selected_subject_z` at P@25. But AUROC remains around 0.52, AUPRC remains low, and recall remains low.

Decision: there is preliminary subject-normalized top-k evidence for a label-error review-queue signal, but this does not establish label-error detection and remains limited by structural alignment confidence.

## 8. Evidence Status

Broad validation is weak. Issue-specific validation is weak overall. Subject normalization weakened the original raw `correct_answer_rarely_selected` signal. The larger focused null confirms limited review-queue hints, not strong external validation.

## 9. What Can Be Claimed

- A focused 1000-iteration subject-matched null was run for `label_error` diagnostics only.
- Raw `correct_answer_rarely_selected` remains above the subject-matched null at some top-k cutoffs.
- Some subject-normalized diagnostics show preliminary top-k enrichment against the subject-matched null.
- Under this protocol, evidence remains preliminary and limited.

## 10. What Cannot Be Claimed

- Do not claim ValidEval detects MMLU label errors.
- Do not claim MMLU-Redux validation succeeded.
- Do not claim MMLU is valid or invalid globally.
- Do not claim this proves label errors.
- Do not claim this is paper-grade external validation.
- Do not claim the MMLU-Redux alignment is direct-id or hash-confirmed.

## 11. Remaining Limitations

- Alignment is structural with confidence 0.85.
- The panel has 39 models and may not expose all item flaws.
- Empirical p-values were not retained in the current null artifact.
- Top-k enrichment is sparse and recall is low.
- AUROC/AUPRC remain weak for subject-normalized diagnostics.

## 12. Next Steps

1. Treat current MMLU-Redux evidence as a negative/weak validation result.
2. Do not use these results as a generic detection-success claim.
3. If future work continues, prioritize direct/hash-confirmed alignment before further MMLU-Redux claims.
4. Keep any label-error output framed as a sanitized review queue, not validated detection.
