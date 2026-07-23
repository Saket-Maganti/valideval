# MMLU-Redux Direct Alignment Validation Report

## 1. Executive Summary

The direct/hash MMLU-Redux alignment attempt is blocked for the current files. The schema report found zero direct item-id matches, no stable metadata match path, and no hash match path. The alignment command can still align 370 labels structurally by subject and source row index, but that is not direct/hash confirmation.

MMLU-Redux therefore remains weak/negative under the current structural alignment. No MMLU error-detection claim is allowed.

## 2. Inputs

- Predictions: `cache/mmlu/wide/predictions.jsonl`
- Redux labels: `data/ground_truth/mmlu_redux_issues.normalized.jsonl`
- Existing structural validation artifacts: `results/mmlu/redux_validation/`

## 3. Alignment Method

Attempted direct/hash alignment using existing sanitized fields. The implemented alignment fallback produced structural matches only.

## 4. Direct/Hash Match Counts

- Direct item-id matches: 0
- Direct item-id match possible: `False`
- Stable metadata match possible: `False`
- Hash match possible: `False`
- Subject/index match possible: `True`

Artifacts:

- `results/mmlu/redux_direct_alignment/schema_report.json`
- `results/mmlu/redux_direct_alignment/schema_report.md`

## 5. Structural Alignment Comparison

The alignment run wrote 370 aligned rows, all by `subject_numeric_index`.

- `subject_numeric_index`: 370
- Direct/hash/stable metadata matches: 0
- Alignment confidence used by structural fallback: 0.85

Artifacts:

- `results/mmlu/redux_direct_alignment/alignment.jsonl`
- `results/mmlu/redux_direct_alignment/alignment_report.json`

## 6. Metrics

Direct/hash validation metrics were not recomputed because direct/hash alignment is blocked. Existing structural validation remains the only available MMLU-Redux evidence and remains weak/negative.

Existing structural summary remains:

- AUROC approximately 0.539
- AUPRC approximately 0.0289
- Precision@10: 0.0

## 7. Subject-Normalized Results

Subject-normalized structural artifacts remain prior evidence only. They do not convert the current files into direct/hash alignment.

## 8. Subject-Matched Null

Existing subject-matched null artifacts remain prior structural-alignment evidence only.

## 9. Issue-Specific Results

Existing issue-specific reports remain preliminary and protocol-scoped. They do not establish direct/hash identity.

## 10. Baselines

No direct/hash-backed baseline comparison was run. Existing structural baselines remain weak/negative.

## 11. Claims Allowed

- The current sanitized files support structural subject/index alignment.
- Direct/hash alignment is not confirmed.
- MMLU-Redux remains a weak/negative stress test under current artifacts.

## 12. Claims Blocked

- MMLU error detection success.
- Direct item identity confirmation.
- Hash-confirmed MMLU-Redux validation.
- Any claim that MMLU is valid or invalid.

## 13. Limitations

The current Redux label file exposes stable source row ids, not HELM instance ids. The wide HELM prediction file exposes item ids but not raw text or stable hashes sufficient to match Redux rows directly.

## 14. Final Verdict

`DIRECT_ALIGNMENT_BLOCKED`
