# MMLU-Redux Subject-Normalized Validation Report

All findings here are preliminary and protocol-scoped. No raw MMLU question text or answer-choice text is included. MMLU-Redux alignment remains structural (`subject_numeric_index`, confidence 0.85), not direct-id or hash-confirmed alignment.

## 1. Executive Summary

Subject-normalized issue-specific validation was implemented to reduce subject-difficulty confounding in the MMLU-Redux validation protocol. The previous narrow `label_error + correct_answer_rarely_selected` signal weakened materially after subject normalization.

In the Redux-subject-filtered universe, raw `correct_answer_rarely_selected` for `label_error` had AUROC 0.600, AUPRC 0.022, and P@10 0.100. The subject-normalized version, `correct_answer_rarely_selected_subject_z`, had AUROC 0.515, AUPRC 0.011, and P@10 0.000. This suggests the earlier signal was likely influenced by subject-level difficulty or subject composition.

A later focused 1000-iteration label-error subject-matched null found limited top-k review-queue hints, including raw `correct_answer_rarely_selected` above null at P@25 and some subject-z top-k cells above null. AUROC/AUPRC and recall remain weak, so this is not strong external validation.

This does not support a generic MMLU error-detection claim.

## 2. Why Subject Normalization Was Needed

Global item difficulty can rank items from generally hard subjects above items from easier subjects. That can make a label-error diagnostic look stronger even if it is mostly detecting subject difficulty.

Subject normalization asks a narrower question: within each MMLU subject, are Redux issue items ranked as more suspicious than non-Redux items from the same subject?

## 3. Data and Alignment

Inputs:

- Matrix: `cache/mmlu/wide/matrix.csv`
- Predictions: `cache/mmlu/wide/predictions.jsonl`
- Ground truth: `data/ground_truth/mmlu_redux_issues.helm_aligned.jsonl`
- Mapping: `configs/validation/mmlu_redux_issue_mapping.yaml`

Panel and alignment status:

- Matrix shape: 39 models x 14,042 items
- Missing cells: 0
- Panel validity: passed
- Redux labels aligned: 370 / 370
- Alignment method: `subject_numeric_index`
- Alignment confidence: 0.85

The alignment is sufficient for this protocol-scoped check, but it is still a limitation.

## 4. Diagnostics Tested

Subject-normalized scores were added for:

- `correct_answer_rarely_selected_subject_z`
- `high_disagreement_subject_z`
- `option_selection_anomaly_subject_z`
- `negative_discrimination_subject_z`
- `low_discrimination_subject_z`
- `extreme_difficulty_subject_z`

Each score is computed as a within-subject z-score from the raw diagnostic. Zero-variance subjects are handled safely with normalized score 0.0. Score direction is preserved: higher remains more suspicious.

## 5. Raw vs Subject-Normalized Results

Primary subject-normalized output:

- `results/mmlu/redux_issue_specific_validation_subject_normalized/issue_type_metrics.json`
- `results/mmlu/redux_issue_specific_validation_subject_normalized/raw_vs_subject_normalized_comparison.md`
- `results/mmlu/redux_issue_specific_validation_subject_normalized/subject_normalized_item_scores.jsonl`
- `results/mmlu/redux_issue_specific_validation_subject_normalized/top_items_sanitized.csv`

`label_error` comparison in the Redux-subject-filtered universe:

| Diagnostic | AUROC | AUPRC | P@10 | P@25 | P@50 | Recall@10 | Recall@25 | Recall@50 | Enrich@10 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `correct_answer_rarely_selected` | 0.600 | 0.022 | 0.100 | 0.120 | 0.060 | 0.009 | 0.028 | 0.028 | 11.841 |
| `correct_answer_rarely_selected_subject_z` | 0.515 | 0.011 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| `high_disagreement` | 0.539 | 0.012 | 0.000 | 0.000 | 0.020 | 0.000 | 0.000 | 0.009 | 0.000 |
| `high_disagreement_subject_z` | 0.522 | 0.010 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| `option_selection_anomaly` | 0.582 | 0.015 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| `option_selection_anomaly_subject_z` | 0.525 | 0.010 | 0.000 | 0.000 | 0.040 | 0.000 | 0.000 | 0.019 | 0.000 |

Interpretation: the previous label-error signal weakened after subject normalization. The strongest previous signal does not survive as a strong within-subject ranking result.

## 6. Label-Error Focused Results

Focused output:

- `results/mmlu/redux_label_error_subject_normalized/issue_type_metrics.json`
- `results/mmlu/redux_label_error_subject_normalized/raw_vs_subject_normalized_comparison.md`
- `results/mmlu/redux_label_error_subject_normalized/subject_normalized_item_scores.jsonl`

This run restricts to `label_error` and the requested diagnostics. Because `--restrict-to-ground-truth-subjects` is applied after issue-type filtering, the evaluation universe is the set of subjects containing label-error labels: 6,500 scored items.

| Diagnostic | AUROC | AUPRC | P@10 | P@25 | P@50 | Recall@10 | Recall@25 | Recall@50 | Enrich@10 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `correct_answer_rarely_selected` | 0.569 | 0.033 | 0.200 | 0.120 | 0.060 | 0.019 | 0.028 | 0.028 | 12.264 |
| `correct_answer_rarely_selected_subject_z` | 0.518 | 0.022 | 0.000 | 0.120 | 0.080 | 0.000 | 0.028 | 0.038 | 0.000 |
| `high_disagreement` | 0.511 | 0.023 | 0.000 | 0.040 | 0.040 | 0.000 | 0.009 | 0.019 | 0.000 |
| `high_disagreement_subject_z` | 0.525 | 0.021 | 0.000 | 0.080 | 0.040 | 0.000 | 0.019 | 0.019 | 0.000 |
| `option_selection_anomaly` | 0.552 | 0.025 | 0.000 | 0.000 | 0.060 | 0.000 | 0.000 | 0.028 | 0.000 |
| `option_selection_anomaly_subject_z` | 0.524 | 0.023 | 0.200 | 0.080 | 0.040 | 0.019 | 0.019 | 0.019 | 12.264 |

The focused run does not rescue the previous signal. Some top-k cells remain nonzero, but AUROC/AUPRC are weak and unstable. These are review-queue hints at most.

## 7. Subject-Matched Null Baseline

Output:

- `results/mmlu/redux_issue_specific_validation_subject_normalized/subject_matched_null.json`
- `results/mmlu/redux_issue_specific_validation_subject_normalized/subject_matched_null.md`

The initial null used 100 iterations as a smoke null to limit compute. A focused 1000-iteration label-error null was then run in:

- `results/mmlu/redux_label_error_subject_matched_null_confirmatory/subject_matched_null.json`
- `results/mmlu/redux_label_error_subject_matched_null_confirmatory/null_comparison.md`
- `MMLU_REDUX_LABEL_ERROR_NULL_CONFIRMATION_REPORT.md`

Both nulls preserve the same number of positives per subject and sample non-issue items within the same subjects.

Selected `label_error` rows:

| Diagnostic | K | Observed P@K | Null mean P@K | Observed / null mean |
|---|---:|---:|---:|---:|
| `correct_answer_rarely_selected` | 10 | 0.100 | 0.032 | 3.125 |
| `correct_answer_rarely_selected` | 25 | 0.120 | 0.018 | 6.522 |
| `correct_answer_rarely_selected` | 50 | 0.060 | 0.011 | 5.357 |
| `correct_answer_rarely_selected_subject_z` | 10 | 0.000 | 0.000 | n/a |
| `correct_answer_rarely_selected_subject_z` | 25 | 0.000 | 0.000 | 0.000 |
| `correct_answer_rarely_selected_subject_z` | 50 | 0.000 | 0.001 | 0.000 |

The focused null supports the same caution with more detail: raw difficulty has top-k enrichment against a subject-matched random baseline, and some subject-normalized diagnostics have isolated top-k enrichment. However, AUROC/AUPRC remain weak and recall remains low.

## 8. Evidence Status

Subject-normalized validation was implemented and run. It reduces confidence in the previous narrow label-error signal because the strongest raw diagnostic weakens after within-subject normalization.

The current evidence status is therefore: broad Redux validation is weak, most issue-specific validation is weak, and the previous label-error signal appears subject-confounded or at least not robust under within-subject normalization. The focused 1000-iteration null adds limited review-queue hints but does not change the evidence status to success.

## 9. What Can Be Claimed

- Subject-normalized validation was implemented to reduce subject-difficulty confounding.
- The previous `label_error + correct_answer_rarely_selected` signal weakened after subject normalization.
- A focused 1000-iteration subject-matched null found limited top-k review-queue hints for label-error diagnostics.
- This remains preliminary under structural MMLU-Redux alignment.
- Outputs are sanitized and contain item ids, subjects, scores, and diagnostics only.

## 10. What Cannot Be Claimed

- Do not claim generic MMLU error-detection success.
- Do not claim MMLU is valid or invalid globally.
- Do not claim subject normalization proves or disproves label errors.
- Do not claim this is paper-grade external validation.
- Do not claim the MMLU-Redux alignment is direct-id or hash-confirmed.
- Do not expose raw MMLU question text or answer-choice text.

## 11. Remaining Limitations

- Alignment confidence is 0.85 and structural only.
- Subject-normalized top-k metrics are unstable for sparse issue types.
- The broad subject-matched null used 100 iterations as a smoke null; the focused label-error null used 1000 iterations.
- The 39-model panel may not expose all issue types.
- Prompt-sensitivity and extraction-sensitivity diagnostics remain blocked by missing authorized inputs.

## 12. Next Steps

1. Treat the previous label-error result as a limitation, not a success claim.
2. Confirm a private subset of MMLU-Redux alignment with direct ids or hashes if allowed.
3. Consider subject-stratified reporting as the default for any MMLU-Redux claim.
4. Prioritize direct/hash-confirmed alignment before any stronger external-validation claim.
