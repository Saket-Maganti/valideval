# Appendix: MMLU-Redux External Validation Stress Test

All evidence in this appendix is preliminary and protocol-scoped. No raw MMLU question text or answer-choice text is included. The MMLU-Redux labels are structurally aligned to HELM MMLU item ids using `subject_numeric_index` with confidence 0.85; they are not direct-id or hash-confirmed alignments.

## A.1 Purpose

This appendix summarizes the MMLU-Redux external-validation stress test for ValidEval. The goal was not to support a detection-success claim. The goal was to test whether matrix-derived diagnostics could recover independently documented MMLU-Redux issue labels under a public HELM MMLU panel.

The result is a negative/weak external-validation case. Broad validation was weak, issue-type-specific validation was mostly weak, subject-normalized validation weakened the earlier label-error signal, and a focused subject-matched null found only limited review-queue hints.

## A.2 Data Sources

- HELM MMLU v1.13.0 public prediction details.
- Imported predictions: `cache/mmlu/wide/predictions.jsonl`.
- Response matrix: `cache/mmlu/wide/matrix.csv`.
- HELM-aligned MMLU-Redux labels: `data/ground_truth/mmlu_redux_issues.helm_aligned.jsonl`.
- Main result directories:
  - `results/mmlu/redux_validation_by_group/`
  - `results/mmlu/redux_issue_specific_validation/`
  - `results/mmlu/redux_issue_specific_validation_subject_normalized/`
  - `results/mmlu/redux_label_error_subject_matched_null_confirmatory/`

## A.3 Wide HELM MMLU Panel

The active HELM MMLU response matrix contains:

- 39 models.
- 14,042 items.
- 0 missing cells.

The panel-validity gate passed. Quick proxy IRT was run after the panel gate passed. This was proxy-only, not full psychometric IRT and not a full 2PL fit.

## A.4 MMLU-Redux Alignment

MMLU-Redux labels were structurally aligned to HELM item ids:

- Aligned labels: 370 / 370.
- Alignment method: `subject_numeric_index`.
- Confidence: 0.85.
- Direct-id/hash confirmation: not available.

This alignment is sufficient for a protocol-scoped stress test, but it remains an important limitation. Some mismatches are still plausible.

## A.5 Broad Validation Attempt

Broad validation treated all aligned MMLU-Redux labels as one target. Proxy-IRT flag groups did not strongly recover Redux labels.

Representative full-universe grouped result:

| Diagnostic | AUROC | AUPRC | P@10 | P@25 | P@50 | Interpretation |
|---|---:|---:|---:|---:|---:|---|
| `combined_flags` | 0.495 | 0.030 | 0.000 | 0.000 | 0.020 | weak / near-random |
| `low_discrimination` | 0.538 | 0.032 | 0.000 | 0.000 | 0.020 | weak |
| `negative_discrimination` | 0.493 | 0.041 | 0.000 | 0.000 | 0.020 | weak |

This does not support an MMLU error-detection claim.

## A.6 Issue-Type-Specific Validation

MMLU-Redux labels were separated by issue type:

- `ambiguous_question`: 132
- `label_error`: 106
- `multiple_correct`: 39
- `answer_error`: 36
- `expert_flag`: 32
- `ambiguous_options`: 25

Most issue-type-specific surfaces remained weak. The strongest narrow raw signal was `label_error + correct_answer_rarely_selected`.

Representative raw label-error result:

| Diagnostic | AUROC | AUPRC | P@10 | P@25 | P@50 | Interpretation |
|---|---:|---:|---:|---:|---:|---|
| `correct_answer_rarely_selected` | 0.604 | 0.023 | 0.100 | 0.120 | 0.060 | narrow review-queue signal |
| `option_selection_anomaly` | 0.585 | 0.013 | 0.000 | 0.000 | 0.000 | weak |
| `negative_discrimination` | 0.555 | 0.011 | 0.000 | 0.000 | 0.000 | weak |

This was not sufficient for a detection-success claim.

## A.7 Subject-Normalized Validation

Subject-normalized scoring was added to reduce subject-difficulty confounding. The strongest prior raw label-error signal weakened after within-subject normalization.

Redux-subject-filtered label-error comparison:

| Diagnostic | AUROC | AUPRC | P@10 | P@25 | P@50 | Interpretation |
|---|---:|---:|---:|---:|---:|---|
| `correct_answer_rarely_selected` | 0.600 | 0.022 | 0.100 | 0.120 | 0.060 | raw top-k signal |
| `correct_answer_rarely_selected_subject_z` | 0.515 | 0.011 | 0.000 | 0.000 | 0.000 | weak after normalization |
| `high_disagreement_subject_z` | 0.522 | 0.010 | 0.000 | 0.000 | 0.000 | weak |
| `option_selection_anomaly_subject_z` | 0.525 | 0.010 | 0.000 | 0.000 | 0.040 | weak |

This suggests the earlier raw signal was partly subject-difficulty or subject-composition driven.

## A.8 Subject-Matched Null Confirmation

A focused 1000-iteration subject-matched null was run for `label_error` diagnostics only. It preserved the number of positives per subject and sampled non-issue items from the same subjects.

Focused label-error null results:

| Diagnostic | AUROC | AUPRC | P@10 | Null mean P@10 | P@25 | Null mean P@25 | Interpretation |
|---|---:|---:|---:|---:|---:|---:|---|
| `correct_answer_rarely_selected` | 0.569 | 0.033 | 0.200 | 0.036 | 0.120 | 0.022 | raw top-k above null |
| `correct_answer_rarely_selected_subject_z` | 0.518 | 0.022 | 0.000 | 0.006 | 0.120 | 0.007 | isolated P@25 signal |
| `high_disagreement_subject_z` | 0.525 | 0.021 | 0.000 | 0.005 | 0.080 | 0.005 | isolated P@25 signal |
| `option_selection_anomaly_subject_z` | 0.524 | 0.023 | 0.200 | 0.005 | 0.080 | 0.007 | top-k hint, weak ranking metrics |

Empirical p-values were not computed because the current null artifact stores summary statistics rather than per-iteration draws.

## A.9 Summary of Results

| Validation surface | Best observed signal | Result | Claim allowed? |
|---|---|---|---|
| Broad proxy-IRT flags | `combined_flags` AUROC 0.495, AUPRC 0.030 | Weak / near-random | No detection claim |
| Issue-specific `label_error` | Raw `correct_answer_rarely_selected` P@10 0.100, P@25 0.120 | Narrow review-queue signal | Review-queue only |
| Subject-normalized `label_error` | `correct_answer_rarely_selected_subject_z` AUROC 0.515, AUPRC 0.011, P@10 0.000 | Weak | No detection claim |
| Subject-matched null | Raw score above null at top-k; some subject-z top-k hints | Possible review utility, weak ranking metrics | Preliminary only |

## A.10 Paper-Facing Interpretation

The MMLU-Redux stress test is best interpreted as a weak or negative external-validation result. ValidEval can run the validation surfaces and keep evidence sanitized, but the current matrix-derived diagnostics do not strongly recover structurally aligned MMLU-Redux issue labels.

The narrow raw label-error signal may still help form a review queue, but weak AUROC/AUPRC, low recall, subject-normalization behavior, and structural alignment uncertainty prevent a detection-success claim.

This stress test is intentionally reported as a negative/weak external-validation result. Its purpose is not to claim successful MMLU error detection, but to show that ValidEval's evidence gates can prevent unsupported diagnostic claims. The result motivates the central argument that benchmark-validity diagnostics must themselves be validated against the specific threat they are intended to detect.

## A.11 What This Supports

- ValidEval can align public HELM MMLU predictions with structurally aligned MMLU-Redux issue labels.
- ValidEval can run broad, issue-specific, subject-normalized, and subject-matched-null validation surfaces without exposing raw item text.
- In this case, broad and subject-normalized matrix-derived diagnostics do not strongly recover MMLU-Redux labels.
- A narrow raw label-error review-queue signal appears at some top-k cutoffs, but weak AUROC/AUPRC and subject-normalized results prevent a detection-success claim.
- ValidEval's evidence gate can reject weak external validation instead of converting it into a success narrative.

## A.12 What This Does Not Support

- A detection-success claim for MMLU errors.
- A claim that MMLU-Redux labels have been validated by ValidEval.
- A global claim that MMLU is valid or invalid.
- An external-validation-success claim for proxy-IRT flags as MMLU-error detectors.
- The structurally aligned MMLU-Redux labels are direct-id or hash-confirmed.
- Proxy IRT is full psychometric IRT.

## A.13 Limitations

- MMLU-Redux alignment is structural with confidence 0.85.
- The HELM panel has 39 models; this may be insufficient for some item-level signals.
- MMLU-Redux issue labels are sparse for several issue types.
- The focused null does not retain empirical p-values.
- Subject-normalized top-k results are unstable and low-recall.
- No raw MMLU question text or answer-choice text is included or inspected in the public evidence artifacts.

## A.14 Reproduction Commands

These commands reproduce the existing validation surfaces from local artifacts. They should not be interpreted as model inference or new data acquisition.

Broad proxy-IRT flag validation:

```bash
python3 -m valideval validate-flags-against-ground-truth \
  --benchmark mmlu \
  --flags results/mmlu/flags.jsonl \
  --ground-truth data/ground_truth/mmlu_redux_issues.helm_aligned.jsonl \
  --output results/mmlu/redux_validation_by_group \
  --group-by diagnostic
```

Issue-specific validation:

```bash
python3 -m valideval mmlu-redux-issue-validation \
  --predictions cache/mmlu/wide/predictions.jsonl \
  --matrix cache/mmlu/wide/matrix.csv \
  --ground-truth data/ground_truth/mmlu_redux_issues.helm_aligned.jsonl \
  --mapping configs/validation/mmlu_redux_issue_mapping.yaml \
  --output results/mmlu/redux_issue_specific_validation
```

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

Focused label-error subject-matched null:

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

## Claim Status

Allowed:

- ValidEval can align public HELM MMLU predictions with structurally aligned MMLU-Redux issue labels.
- ValidEval can run broad, issue-specific, subject-normalized, and subject-matched-null validation surfaces without exposing raw item text.
- In this case, broad and subject-normalized matrix-derived diagnostics do not strongly recover MMLU-Redux labels.
- A narrow raw label-error review-queue signal appears at some top-k cutoffs, but weak AUROC/AUPRC and subject-normalized results prevent a detection-success claim.

Not allowed:

- A detection-success claim for MMLU errors.
- A claim that MMLU-Redux labels have been validated by ValidEval.
- A claim that MMLU is globally invalid.
- An external-validation-success claim for proxy-IRT flags as MMLU-error detectors.
