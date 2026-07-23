# MMLU-Redux Issue-Specific Validation Report

All findings here are preliminary and protocol-scoped. No raw MMLU question text or answer choices are included. The MMLU-Redux alignment remains structural (`subject_numeric_index`, confidence 0.85), not direct-id or hash-confirmed alignment.

## 1. Executive Summary

Issue-type-specific validation was added so MMLU-Redux labels are no longer treated as one undifferentiated target. The new protocol maps each observed Redux issue type to diagnostics that are logically plausible for that issue type, then evaluates those mappings using only the existing 39-model HELM response matrix and local prediction records.

The broad conclusion remains cautious. Most issue-type/diagnostic pairs are weak against structurally aligned MMLU-Redux labels. One narrow pair, `label_error` evaluated with `correct_answer_rarely_selected`, showed preliminary enrichment before subject normalization. A later subject-normalized run weakened that signal. A focused 1000-iteration label-error subject-matched null found limited top-k review-queue hints, but AUROC/AUPRC and recall remain weak. This is not generic benchmark-error detection.

## 2. Why Broad Validation Was Weak

The broad proxy-IRT validation asked a single statistical flag set to recover all Redux issue labels. That target mixes label errors, answer errors, multiple-correct cases, ambiguous questions, ambiguous options, and expert flags. These are not all expected to have the same response-matrix signature.

The broad validation was also diluted by a 14,042-item universe with 370 aligned issue labels, structural rather than hash-confirmed alignment, and a 39-model panel that may not expose all item flaws. This protocol addresses the taxonomy mismatch, but it does not fix structural alignment uncertainty or the limited panel size.

## 3. Redux Issue Taxonomy

Taxonomy artifacts:

- `results/mmlu/redux_issue_type_analysis/issue_taxonomy.json`
- `results/mmlu/redux_issue_type_analysis/issue_taxonomy.md`

Aligned issue counts:

| Issue type | Count | Severity |
|---|---:|---|
| `ambiguous_question` | 132 | medium |
| `label_error` | 106 | high |
| `multiple_correct` | 39 | high |
| `answer_error` | 36 | high |
| `expert_flag` | 32 | medium |
| `ambiguous_options` | 25 | medium |

Severity counts:

| Severity | Count |
|---|---:|
| high | 181 |
| medium | 189 |

All six issue types meet the configured full-run minimum of 20 positives, but the 25 to 39 count categories remain sparse and should be treated as uncertainty-heavy.

## 4. Diagnostic-to-Issue Mapping

Mapping file:

- `configs/validation/mmlu_redux_issue_mapping.yaml`

The mapping uses only issue types observed in the aligned Redux labels:

| Issue type | Plausible diagnostics |
|---|---|
| `label_error` | `negative_discrimination`, `high_disagreement`, `correct_answer_rarely_selected`, `option_selection_anomaly` |
| `answer_error` | `negative_discrimination`, `high_disagreement`, `correct_answer_rarely_selected`, `option_selection_anomaly` |
| `multiple_correct` | `high_disagreement`, `bimodal_model_choices`, `option_selection_anomaly`, `low_discrimination` |
| `ambiguous_question` | `high_disagreement`, `low_discrimination`, `bimodal_model_choices`, `prompt_sensitivity` |
| `ambiguous_options` | `high_disagreement`, `bimodal_model_choices`, `option_selection_anomaly`, `prompt_sensitivity` |
| `expert_flag` | `high_disagreement`, `low_discrimination`, `option_selection_anomaly`, `extraction_sensitivity` |

`prompt_sensitivity` is blocked because no complete prompt-variant matrix is authorized. `extraction_sensitivity` is blocked because strict/lenient extraction metadata is not available in the current inputs.

## 5. Matrix-Derived Diagnostics

Implemented diagnostics use only `cache/mmlu/wide/matrix.csv` and `cache/mmlu/wide/predictions.jsonl`.

| Diagnostic | Source | Meaning |
|---|---|---|
| `high_disagreement` | predictions | Fraction of models not selecting the majority A/B/C/D option |
| `correct_answer_rarely_selected` | matrix | One minus item correctness rate across the panel |
| `negative_discrimination` | proxy IRT | Positive score for negative proxy discrimination |
| `low_discrimination` | proxy IRT | Near-zero proxy discrimination score |
| `extreme_difficulty` | matrix | Absolute distance from 50 percent correctness, scaled to [0, 1] |
| `option_selection_anomaly` | predictions | Average of normalized option entropy and one minus gold-option selection rate |
| `bimodal_model_choices` | predictions | Score for two distractor options attracting substantial model mass |

No raw prompt text, question text, or answer choice text is read for scoring or exported.

## 6. Issue-Specific Metrics

Full-universe output:

- `results/mmlu/redux_issue_specific_validation/issue_type_metrics.json`
- `results/mmlu/redux_issue_specific_validation/issue_type_metrics.md`
- `results/mmlu/redux_issue_specific_validation/diagnostic_by_issue_matrix.csv`
- `results/mmlu/redux_issue_specific_validation/top_items_sanitized.csv`

Selected full-universe metrics:

| Issue type | Diagnostic | Positives | AUROC | AUPRC | P@10 | P@25 | P@50 | Status |
|---|---|---:|---:|---:|---:|---:|---:|---|
| `label_error` | `correct_answer_rarely_selected` | 106 | 0.604 | 0.023 | 0.100 | 0.120 | 0.060 | ok |
| `label_error` | `option_selection_anomaly` | 106 | 0.585 | 0.013 | 0.000 | 0.000 | 0.000 | ok |
| `label_error` | `negative_discrimination` | 106 | 0.555 | 0.011 | 0.000 | 0.000 | 0.000 | ok |
| `label_error` | `high_disagreement` | 106 | 0.542 | 0.011 | 0.000 | 0.000 | 0.020 | ok |
| `answer_error` | `correct_answer_rarely_selected` | 36 | 0.530 | 0.004 | 0.000 | 0.000 | 0.000 | ok |
| `multiple_correct` | `low_discrimination` | 39 | 0.518 | 0.003 | 0.000 | 0.000 | 0.000 | ok |
| `ambiguous_options` | `bimodal_model_choices` | 25 | 0.490 | 0.005 | 0.000 | 0.040 | 0.020 | ok |
| `ambiguous_question` | `low_discrimination` | 132 | 0.482 | 0.009 | 0.000 | 0.000 | 0.020 | ok |
| `expert_flag` | `option_selection_anomaly` | 32 | 0.469 | 0.004 | 0.000 | 0.040 | 0.020 | ok |
| `multiple_correct` | `high_disagreement` | 39 | 0.446 | 0.003 | 0.000 | 0.040 | 0.020 | ok |

For `label_error` with `correct_answer_rarely_selected`, bootstrap intervals are AUROC [0.546, 0.653] and AUPRC [0.013, 0.039] with 200 bootstrap samples. Recall remains low: Recall@10 0.009, Recall@25 0.028, and Recall@50 0.028.

## 7. Subject-Filtered Metrics

Subject-filtered output:

- `results/mmlu/redux_issue_specific_validation_subject_filtered/issue_type_metrics.json`
- `results/mmlu/redux_issue_specific_validation_subject_filtered/diagnostic_by_issue_matrix.csv`
- `results/mmlu/redux_issue_specific_validation_subject_filtered/top_items_sanitized.csv`

The subject filter restricts evaluation to subjects represented in the aligned MMLU-Redux labels. It reduces the universe from 14,042 to 12,551 scored items.

Key subject-filtered result:

| Issue type | Diagnostic | Positives | AUROC | AUPRC | P@10 | P@25 | P@50 | Enrich@10 |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| `label_error` | `correct_answer_rarely_selected` | 106 | 0.600 | 0.022 | 0.100 | 0.120 | 0.060 | 11.841 |

Subject filtering does not materially change the interpretation. The same narrow label-error signal persists; most other issue-type/diagnostic pairs remain weak.

## 8. Severity-Filtered Metrics

High-severity output:

- `results/mmlu/redux_issue_specific_validation_high_severity/issue_type_metrics.json`
- `results/mmlu/redux_issue_specific_validation_high_severity/diagnostic_by_issue_matrix.csv`
- `results/mmlu/redux_issue_specific_validation_high_severity/top_items_sanitized.csv`

High-severity labels contain `label_error`, `answer_error`, and `multiple_correct`. The medium-only mapped types, `ambiguous_question`, `ambiguous_options`, and `expert_flag`, are absent after filtering and are recorded as mapping warnings.

Key high-severity result:

| Issue type | Diagnostic | Positives | AUROC | AUPRC | P@10 | P@25 | P@50 | Enrich@10 |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| `label_error` | `correct_answer_rarely_selected` | 106 | 0.604 | 0.023 | 0.100 | 0.120 | 0.060 | 13.247 |

The high-severity slice repeats the same narrow signal because `label_error` is a high-severity issue type in the aligned taxonomy.

## 9. What Worked, If Anything

For `label_error`, raw `correct_answer_rarely_selected` showed preliminary enrichment under structural alignment. This is logically plausible because label or answer-key errors can make the nominal gold option rarely selected or rarely correct across the panel.

Subject-normalized validation later weakened this signal: in the Redux-subject-filtered universe, `correct_answer_rarely_selected_subject_z` had AUROC 0.515, AUPRC 0.011, and Precision@10 0.000. This suggests the raw signal may be subject-difficulty confounded. It is not enough for a generic detection-success claim.

A focused 1000-iteration subject-matched null later showed that raw `correct_answer_rarely_selected` remains above the null at P@25, and some subject-z diagnostics have isolated top-k enrichment. These are review-queue hints only because AUROC/AUPRC remain weak and recall remains low.

## 10. What Did Not Work

Most issue-type/diagnostic pairs did not show strong validation against MMLU-Redux labels. In particular, ambiguous question and ambiguous option categories remain weak under the matrix-only diagnostics that are currently available.

`prompt_sensitivity` and `extraction_sensitivity` could not be evaluated from the current inputs. They remain blocked rather than approximated.

## 11. Underpowered Issue Types

No issue type is under the configured full-run threshold of 20 positives. Still, `ambiguous_options` (25), `expert_flag` (32), `answer_error` (36), and `multiple_correct` (39) are sparse enough that top-k precision and bootstrap intervals can be unstable.

When `--severity high --min-positive-count 10` is used, only high-severity issue types remain. Medium-only issue types are not silently discarded; they are recorded as absent after filtering.

## 12. Alignment Limitations

MMLU-Redux labels are aligned structurally:

- Method: `subject_numeric_index`
- Confidence: 0.85
- Aligned labels: 370 / 370

This supports a protocol-scoped validation run, but it does not prove item identity by direct id, stable metadata, raw-text hash, or answer-choice hash. Some label mismatches remain plausible.

## 13. What Can Be Claimed

- Issue-type-specific MMLU-Redux validation is implemented and runnable from local artifacts.
- Subject-normalized validation is implemented and reported in `MMLU_REDUX_SUBJECT_NORMALIZED_VALIDATION_REPORT.md`.
- Focused label-error null confirmation is reported in `MMLU_REDUX_LABEL_ERROR_NULL_CONFIRMATION_REPORT.md`.
- The taxonomy and validation outputs are sanitized and do not expose raw MMLU question text or answer choices.
- Broad and most issue-specific matrix-derived diagnostics remain weak against MMLU-Redux labels under structural alignment.
- For `label_error`, raw `correct_answer_rarely_selected` showed preliminary enrichment before subject normalization, but that signal weakened after within-subject normalization.

## 14. What Cannot Be Claimed

- Do not claim generic MMLU error-detection success.
- Do not claim MMLU is valid or invalid globally.
- Do not claim issue-specific validation proves benchmark-error detection.
- Do not claim the raw label-error signal survived subject normalization.
- Do not claim the focused subject-matched null establishes label-error detection.
- Do not claim the MMLU-Redux alignment is direct/hash-confirmed.
- Do not claim proxy IRT is full psychometric IRT or full 2PL.
- Do not claim prompt sensitivity or extraction sensitivity was evaluated.

## 15. Next Steps

1. Confirm at least a private subset of Redux alignment with direct ids or hashes if data handling rules allow.
2. Treat subject-normalized results as the stricter evidence surface for MMLU-Redux claims.
3. Evaluate prompt sensitivity only if complete prompt-variant matrices are authorized.
4. Evaluate extraction sensitivity only if strict/lenient extraction metadata is available.
5. Treat `label_error` enrichment as a preliminary review-queue signal, not a generic ValidEval success claim.
