# Prompt 03 — MMLU-Redux Alignment Rescue or Formal Block

## Objective

Try one more rigorous attempt to obtain direct/hash-backed MMLU-Redux alignment. If impossible, formalize the block so reviewers cannot attack ambiguity.

## Tasks

1. Locate all MMLU item metadata and Redux labels.
2. Search for shared item IDs, question hashes, subject/index pairs, raw text hashes if locally allowed.
3. Do not print raw question text in reports.
4. Write a direct/hash alignment attempt artifact.
5. If direct/hash fails, create a formal blocker with exact missing fields.

## Commands

Search:

```bash
find data cache results -iname "*mmlu*" -o -iname "*redux*"
rg "question_id|item_id|hash|subject|index|redux|mmlu-redux|subject_numeric_index" data cache results src paper *.md
```

Implement/run:

```bash
python3 -m valideval mmlu-redux-direct-alignment-rescue   --predictions cache/mmlu/wide/predictions.jsonl   --source data/external/mmlu/prediction_details_wide.jsonl   --output results/mmlu/redux_alignment_rescue   --execute
```

## Outputs

```text
results/mmlu/redux_alignment_rescue/alignment_attempts.json
results/mmlu/redux_alignment_rescue/missing_fields.json
results/mmlu/redux_alignment_rescue/sanitized_alignment_summary.md
```

## Report

Create:

```text
MMLU_REDUX_ALIGNMENT_RESCUE_OR_FORMAL_BLOCK_REPORT.md
```

Final verdict:

```text
DIRECT_HASH_ALIGNMENT_RECOVERED
DIRECT_HASH_ALIGNMENT_FORMALLY_BLOCKED
ALIGNMENT_RESCUE_NEEDS_FIXES
```

## If recovered

Run validation again and update claims narrowly.

## If blocked

State:

- structural alignment remains the only available route,
- no direct/hash claim is allowed,
- MMLU-Redux remains weak/negative stress test.

## Verification

```bash
ruff check .
python3 -m pytest -q
```
