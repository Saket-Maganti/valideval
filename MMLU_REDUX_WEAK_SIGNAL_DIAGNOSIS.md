# MMLU-Redux Weak Signal Diagnosis

All findings in this document are preliminary and protocol-scoped. No raw MMLU question text or answer text is included.

## 1. Executive Summary

The 39-model HELM MMLU wide panel clears the panel-validity gate, and proxy-only IRT completed successfully. The resulting proxy-IRT flags do not show strong validation against the structurally aligned MMLU-Redux labels. Full-universe grouped validation remains near chance: combined proxy-IRT flags have AUROC 0.495, AUPRC 0.030, Precision@10 0.000, Precision@25 0.000, and Precision@50 0.020. Subject filtering does not materially improve the result.

This is not evidence that ValidEval detects MMLU-Redux issues. The safest interpretation is that the current proxy-IRT statistical flags and the current structurally aligned Redux labels have weak measured association under this protocol.

## 2. Current Inputs

- Wide normalized HELM MMLU file: `data/external/mmlu/prediction_details_wide.jsonl`
- Imported wide predictions: `cache/mmlu/wide/predictions.jsonl`
- Wide response matrix: `cache/mmlu/wide/matrix.csv`
- Matrix shape: 39 models x 14,042 items, with 0 missing cells
- Proxy IRT output: `results/mmlu/irt`
- Proxy-IRT flags: `results/mmlu/flags.jsonl`
- Aligned MMLU-Redux labels: `data/ground_truth/mmlu_redux_issues.helm_aligned.jsonl`

## 3. Panel Quality

Panel validity passed.

- Models: 39
- Items: 14,042
- Missing fraction: 0.000
- Ability spread: 0.5802
- Model accuracy std: 0.1209
- Blockers: none

This clears the protocol gate for item-level proxy-psychometric diagnostics. It does not turn proxy IRT into a full parametric IRT model.

## 4. IRT / Proxy IRT Outputs

The command was:

```bash
python3 -m valideval fit-irt \
  --matrix cache/mmlu/wide/matrix.csv \
  --model proxy \
  --output results/mmlu/irt \
  --strict
```

Status: `ok`

Estimation layers:

- Proxy: true
- Rasch/1PL: not run because `--model proxy` was requested
- 2PL proxy: not run because `--model proxy` was requested
- Full parametric 2PL: false / not run
- Convergence: proxy is closed-form/no-iteration; no Bayesian or full 2PL convergence claim applies

Proxy item difficulty distribution:

- n: 14,042
- mean: -1.419
- std: 2.640
- min / median / max: -9.210 / -1.355 / 9.210
- p10 / p25 / p75 / p90: -3.638 / -2.485 / 0.051 / 1.204

Proxy item discrimination distribution:

- n: 14,042
- mean: 0.306
- std: 0.239
- min / median / max: -0.770 / 0.331 / 0.852
- p10 / p25 / p75 / p90: 0.000 / 0.180 / 0.473 / 0.587

Flag-relevant counts:

- Negative discrimination items: 1,037
- Near-zero discrimination items: 1,342
- Extreme difficulty items: 2,676

Proxy model ability distribution:

- n: 39
- mean: 0.853
- std: 0.572
- min / median / max: -0.908 / 0.916 / 1.880
- p10 / p25 / p75 / p90: 0.177 / 0.492 / 1.233 / 1.478

## 5. Redux Alignment Limitation

MMLU-Redux alignment is complete but not direct/hash-confirmed.

- Redux labels aligned: 370 / 370
- Alignment method: `subject_numeric_index`
- Confidence: 0.85
- Limitation: structural alignment maps Redux subject row positions to HELM-style item ids. It does not prove text identity by direct item id, stable hash, or raw-text hash.

This means some label mismatches remain plausible even when the alignment procedure is internally consistent.

## 6. Ground-Truth Label Distribution

Aligned MMLU-Redux labels cover 370 items across 49 subjects.

Issue type distribution:

| Issue type | Count |
|---|---:|
| ambiguous_question | 132 |
| label_error | 106 |
| multiple_correct | 39 |
| answer_error | 36 |
| expert_flag | 32 |
| ambiguous_options | 25 |

Severity distribution:

| Severity | Count |
|---|---:|
| high | 181 |
| medium | 189 |

## 7. Flag Distribution

The command was:

```bash
python3 -m valideval export-flags \
  --benchmark mmlu \
  --matrix cache/mmlu/wide/matrix.csv \
  --irt results/mmlu/irt \
  --output results/mmlu/flags.jsonl
```

Export status: `ok`

| Diagnostic | Rows |
|---|---:|
| negative_discrimination | 1,037 |
| low_discrimination | 1,342 |
| extreme_difficulty | 2,676 |
| combined_flags | 4,106 |
| all diagnostic rows | 9,161 |

Separate files:

- `results/mmlu/flags_negative_discrimination.jsonl`
- `results/mmlu/flags_low_discrimination.jsonl`
- `results/mmlu/flags_extreme_difficulty.jsonl`
- `results/mmlu/flags_combined.jsonl`

The exported flags include item ids, subjects, diagnostics, scores, direction, source, and sanitized evidence only.

## 8. Metric Results by Diagnostic

Full-universe validation output: `results/mmlu/redux_validation_by_group/metrics.json`

| Diagnostic | AUROC | AUPRC | P@10 | P@25 | P@50 | R@10 | R@25 | R@50 | Enrich@10 | Enrich@50 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| combined_flags | 0.495 | 0.030 | 0.000 | 0.000 | 0.020 | 0.000 | 0.000 | 0.008 | 0.000 | 0.627 |
| extreme_difficulty | 0.496 | 0.028 | 0.000 | 0.000 | 0.020 | 0.000 | 0.000 | 0.012 | 0.000 | 0.622 |
| low_discrimination | 0.538 | 0.032 | 0.000 | 0.000 | 0.020 | 0.000 | 0.000 | 0.027 | 0.000 | 0.725 |
| negative_discrimination | 0.493 | 0.041 | 0.000 | 0.000 | 0.020 | 0.000 | 0.000 | 0.023 | 0.000 | 0.482 |

Subject-filtered validation output: `results/mmlu/redux_validation_subject_filtered/metrics.json`

| Diagnostic | AUROC | AUPRC | P@10 | P@25 | P@50 | R@10 | R@25 | R@50 | Enrich@10 | Enrich@50 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| combined_flags | 0.498 | 0.035 | 0.000 | 0.000 | 0.020 | 0.000 | 0.000 | 0.008 | 0.000 | 0.554 |
| extreme_difficulty | 0.496 | 0.035 | 0.000 | 0.000 | 0.020 | 0.000 | 0.000 | 0.012 | 0.000 | 0.544 |
| low_discrimination | 0.540 | 0.040 | 0.000 | 0.000 | 0.020 | 0.000 | 0.000 | 0.027 | 0.000 | 0.635 |
| negative_discrimination | 0.485 | 0.044 | 0.000 | 0.000 | 0.020 | 0.000 | 0.000 | 0.023 | 0.000 | 0.443 |

High-severity-only validation output: `results/mmlu/redux_validation_high_severity/metrics.json`

- Combined flags: AUROC 0.533, AUPRC 0.018, P@10 0.000, P@25 0.000, P@50 0.000.
- Negative discrimination: AUROC 0.591, AUPRC 0.030, P@10 0.000, P@25 0.000, P@50 0.020.

Issue-type slices were also run. Some sparse subsets show isolated AUROC elevations, for example low discrimination vs `answer_error` AUROC 0.676 and negative discrimination vs `multiple_correct` AUROC 0.672, but AUPRC remains very low and top-k precision is zero in almost all slices. These are exploratory weak signals, not detection-success results.

Bootstrap CIs are written in each `metrics.json`. The full-universe CIs are broad enough that the results should be treated as weak and unstable.

Issue-type-specific validation was then added in `MMLU_REDUX_ISSUE_SPECIFIC_VALIDATION_REPORT.md` and `results/mmlu/redux_issue_specific_validation/`. This protocol maps each observed Redux issue type to plausible matrix-derived diagnostics instead of treating all 370 labels as one target. The result remained cautious: most pairs were weak, while raw `label_error` with `correct_answer_rarely_selected` showed preliminary enrichment under structural alignment.

Subject-normalized validation was later added in `MMLU_REDUX_SUBJECT_NORMALIZED_VALIDATION_REPORT.md` and `results/mmlu/redux_issue_specific_validation_subject_normalized/`. The previous raw label-error signal weakened after within-subject normalization: `correct_answer_rarely_selected_subject_z` had AUROC 0.515, AUPRC 0.011, and Precision@10 0.000 in the Redux-subject-filtered universe. This suggests the previous signal may be subject-difficulty confounded.

A focused 1000-iteration subject-matched null was then run for `label_error` only in `results/mmlu/redux_label_error_subject_matched_null_confirmatory/`. It found limited top-k review-queue hints: raw `correct_answer_rarely_selected` remained above the null at P@25, and some subject-z diagnostics had isolated top-k enrichment. AUROC/AUPRC and recall remained weak, so this did not convert the result into detection-success evidence.

## 9. Possible Causes of Weak Signal

- Structural alignment may be wrong for some labels because the method is subject plus numeric index, not direct/hash-confirmed.
- MMLU-Redux labels focus on label errors, answer errors, ambiguous wording/options, multiple-correct cases, and expert flags. Broad proxy IRT flags statistical response anomalies; these are related only indirectly.
- A 39-model panel clears the current gate but may still be too small for high-confidence item-discrimination ranking across 14,042 items.
- HELM-selected models may not span enough distinct reasoning profiles to expose all item-level flaws.
- Subject difficulty and domain composition can dominate simple difficulty/discrimination proxies; the subject-normalized run weakened the prior raw label-error signal, and the focused null only supports limited review-queue hints.
- The current flag thresholds are review-oriented and broad: 4,106 unique items are flagged. This can dilute top-k precision.
- Score direction and tie behavior matter. Extreme-difficulty and combined rows create many score ties at 1.000, and the top combined rows did not hit Redux labels.
- Full-universe validation is diluted by evaluating against 14,042 items when Redux labels mark only 370 issue items.
- Subject filtering reduces the universe but does not fix the construct mismatch between statistical anomalies and Redux issue categories.

## 10. What Can Be Claimed

- The 39-model HELM MMLU wide panel passed the protocol panel-validity gate.
- Proxy-only IRT completed and produced item difficulty, item discrimination, and model ability proxy summaries.
- Proxy-IRT flags were exported with sanitized provenance and no raw MMLU text.
- Validation against structurally aligned MMLU-Redux labels is weak under the current protocol.
- The current evidence is consistent with a mismatch between statistical response anomaly flags and Redux-style item flaw labels.
- Issue-specific, subject-normalized, and focused label-error null validation are implemented. The current evidence remains weak and review-queue-scoped.

## 11. What Cannot Be Claimed

- Do not claim ValidEval detects MMLU-Redux errors.
- Do not claim MMLU is valid or invalid globally.
- Do not claim proxy IRT is full psychometric IRT or full 2PL.
- Do not claim the Redux alignment is text/hash-confirmed.
- Do not claim isolated AUROC values in sparse issue-type slices are detection success.
- Do not claim the raw issue-specific label-error result survived subject normalization.
- Do not claim the focused null confirms label-error detection.
- Do not expose or reproduce raw MMLU question text or answer text.

## 12. Next Fixes

1. Confirm a subset of Redux alignment by direct text/hash matching in a private, non-public artifact if licensing and data handling rules permit.
2. Use subject-normalized and subject-matched-null results as the stricter MMLU-Redux evidence surface.
3. Prioritize direct/hash-confirmed alignment before any stronger MMLU-Redux claim.
4. If reporting a review queue, label it as preliminary and subject to structural-alignment uncertainty.
5. Treat the current public evidence as a limitation section, not a success claim.
6. Keep the next IRT step proxy-safe unless a validated, quick full-IRT implementation is explicitly available.
7. Treat the current public evidence as a limitation section, not a success claim.
