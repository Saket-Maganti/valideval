# Real Wide Import Smoke Completed

Timestamp UTC: 2026-06-12T10:04:24Z

## Status

The smoke lm-eval output was converted into ValidEval wide predictions and a
wide matrix. This was a one-model limited smoke, not the final multi-model
matrix.

## Inputs

- Source directory: `data/external/mmlu/lm_eval_outputs/qwen2_5_0_5b_smoke`
- Source sample rows: `25`
- Source model: `Qwen/Qwen2.5-0.5B-Instruct`
- Source task: `mmlu_high_school_biology`

## Commands

```bash
python3 -m valideval import-published-details \
  --benchmark mmlu \
  --input data/external/mmlu/lm_eval_outputs/qwen2_5_0_5b_smoke \
  --format lm_eval \
  --output cache/mmlu/wide/predictions.jsonl \
  --mapping-report results/mmlu/import_mapping_report.md
```

```bash
python3 -m valideval matrix-from-wide-predictions \
  --predictions cache/mmlu/wide/predictions.jsonl \
  --output cache/mmlu/wide/matrix.csv \
  --report results/mmlu/wide_matrix_report.md
```

## Smoke Output Summary

- Wide prediction rows: `25`
- Models: `1`
- Items: `25`
- Missing matrix cells: `0`
- Import runtime: `0.37s`
- Matrix runtime: `0.35s`

## Why This Is Real Evidence

The source file is a real lm-evaluation-harness `--log_samples` output under
`data/external/mmlu/lm_eval_outputs/qwen2_5_0_5b_smoke`. The normalized rows
record `source="lm_eval:log_samples"` and preserve `source_file` provenance.
The importer discarded text-bearing fields (`doc`, `arguments`) by default.

This smoke did not use `examples/mmlu_subset.jsonl`, `examples/mmlu_redux_mock.jsonl`,
`examples/mmlu_redux_mock.csv`, or parser fixtures.
