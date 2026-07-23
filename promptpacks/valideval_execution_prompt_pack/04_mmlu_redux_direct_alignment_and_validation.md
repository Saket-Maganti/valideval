# Prompt 04 — MMLU-Redux Direct/Hash Alignment and Validation

## Objective

Strengthen or honestly block the MMLU-Redux external validation by attempting direct/hash-backed alignment instead of relying only on structural alignment.

## Rules

- Do not expose raw question text in reports.
- Use hashes/IDs wherever possible.
- Keep structural alignment separate from direct/hash alignment.
- Do not claim detection success unless metrics support it.

## Locate labels and IDs

```bash
find data cache results -iname "*redux*" -o -iname "*mmlu*" | sort
rg "mmlu-redux|redux|subject_numeric_index|hash|question_id|item_id" .
```

## Alignment command

Try existing command:

```bash
python3 -m valideval mmlu-redux-alignment   --predictions cache/mmlu/wide/predictions.jsonl   --output results/mmlu/redux_direct_alignment   --execute
```

If only preflight exists, implement minimal execution:

- load Redux labels,
- load MMLU item metadata,
- compute stable internal text hashes,
- write hashes/IDs/subject/index/issue type only,
- no raw text in outputs,
- report match counts and confidence levels.

## Validation command

Try:

```bash
python3 -m valideval mmlu-redux-validation   --matrix cache/mmlu/wide/matrix.csv   --alignment results/mmlu/redux_direct_alignment/alignment.jsonl   --output results/mmlu/redux_validation_direct   --execute
```

Required metrics:

- AUROC,
- AUPRC,
- precision@10/25/50,
- recall@10/25/50,
- subject-normalized variants,
- issue-specific breakdown,
- subject-matched null with saved per-iteration draws,
- baseline comparisons.

## Create report

```text
MMLU_REDUX_DIRECT_ALIGNMENT_VALIDATION_REPORT.md
```

Structure:

```markdown
# MMLU-Redux Direct Alignment Validation Report

## 1. Executive Summary
## 2. Inputs
## 3. Alignment Method
## 4. Direct/Hash Match Counts
## 5. Structural Alignment Comparison
## 6. Metrics
## 7. Subject-Normalized Results
## 8. Subject-Matched Null
## 9. Issue-Specific Results
## 10. Baselines
## 11. Claims Allowed
## 12. Claims Blocked
## 13. Limitations
## 14. Final Verdict
```

Final verdict:

```text
DIRECT_ALIGNMENT_VALIDATION_COMPLETE_WEAK_NEGATIVE
DIRECT_ALIGNMENT_VALIDATION_COMPLETE_POSITIVE_LIMITED
DIRECT_ALIGNMENT_BLOCKED
VALIDATION_NEEDS_FIXES
```

## Verification

```bash
ruff check .
python3 -m pytest -q
```
