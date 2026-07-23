# MMLU-Redux Labels Missing

Timestamp UTC: 2026-06-12T10:04:24Z

Status: blocked.

The required MMLU-Redux label file is missing:

```text
data/ground_truth/mmlu_redux_issues.normalized.jsonl
```

Do not run or claim real MMLU-Redux validation until that file exists and is
verified as real external issue-label data rather than a mock fixture.

## Required Label File

The label file must be JSONL. Each row must identify a MMLU item and its
external issue/quality label in the schema accepted by:

```bash
python3 -m valideval import-ground-truth \
  --benchmark mmlu_redux \
  --input data/ground_truth/mmlu_redux_issues.normalized.jsonl \
  --output cache/mmlu/redux/issues.jsonl \
  --report results/mmlu/redux_label_import_report.md
```

Only after that import succeeds should the validation command run:

```bash
python3 -m valideval mmlu-redux-validation \
  --predictions cache/mmlu/wide/predictions.jsonl \
  --issues cache/mmlu/redux/issues.jsonl \
  --matrix cache/mmlu/wide/matrix.csv \
  --out-dir results/mmlu/redux_validation
```
