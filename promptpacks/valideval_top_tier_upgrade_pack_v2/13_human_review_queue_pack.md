# Prompt 13 — Human Review Queue Pack

## Objective

Convert diagnostic flags into a reviewer-safe human audit queue.

This adds value even if automated detection remains weak.

## Tasks

1. Sample items from high-disagreement / low-discrimination / subject-unstable groups.
2. Sanitize raw text or use hashed IDs depending on dataset policy.
3. Create annotation instructions.
4. Create CSV/JSONL queue.
5. Create adjudication rubric.
6. Create import path for human labels.
7. Create a reviewer-facing report without raw restricted text.

## Outputs

```text
results/mmlu/human_review_queue/
HUMAN_REVIEW_QUEUE_REPORT.md
docs/annotation/MMLU_REVIEW_RUBRIC.md
templates/human_review_queue_template.csv
```

## Claim

Allowed: “ValidEval produces an audit queue for human review.”

Blocked: “human review confirms errors” unless labels are collected.

Final verdict:

```text
HUMAN_REVIEW_QUEUE_READY
HUMAN_REVIEW_QUEUE_BLOCKED
```
