# Real MMLU Input Requirements

Runs 1 and 2 require real local lm-eval output. As of 2026-06-12, a limited
real MMLU high-school-biology pilot exists, but full all-subject MMLU does not.

## Required File Or Directory

Provide one of:

- a directory produced by `lm_eval --log_samples --output_path ...`
- a single lm-eval `samples_*.jsonl` file

Recommended local placement:

```text
data/external/mmlu/lm_eval_outputs/
```

The directory should contain sample JSONL files from real model evaluations, not fixtures. Typical
paths may look like:

```text
data/external/mmlu/lm_eval_outputs/<model_slug>/<lm_eval_model_dir>/samples_mmlu_high_school_biology_*.jsonl
data/external/mmlu/lm_eval_outputs/<model_slug>/<lm_eval_model_dir>/samples_mmlu_abstract_algebra_*.jsonl
```

## Required Per-Sample Fields

Each sample row must provide enough information to derive:

- `model_id`
- `item_id`
- `subset`
- `prediction`
- `gold`
- `correct`

Accepted lm-eval-style fields include:

- item: `doc_id`, `item_id`, `sample_id`, `id`, `idx`
- task/subset: `task`, `task_name`, or `samples_<task>.jsonl`
- prediction: lm-eval `filtered_resps`/`resps` choice scores, or direct `prediction`, `pred`
- gold: `target`, `gold`, `correct_answer`, `label`, or `doc.answer`
- correctness: `acc`, `exact_match`, `correct`, `metrics.acc`, `metrics.exact_match`

## Not Acceptable As Real Evidence

Do not use these as real evidence:

- `examples/mmlu_subset.jsonl`
- `examples/mmlu_redux_mock.jsonl`
- `examples/mmlu_redux_mock.csv`
- `examples/wide_predictions_mock.jsonl`
- `examples/wide_predictions_mock.csv`
- `tests/fixtures/lm_eval_samples/**`
- `results/neurips_small_runs/**`

These are parser/demo fixtures only.

## Minimum Verification Before Import

Before importing, verify:

```bash
find data/external/mmlu/lm_eval_outputs -type f -name '*.jsonl' | head
rg -n '"filtered_resps"|"resps"|"target"|"acc"|"exact_match"' data/external/mmlu/lm_eval_outputs
rg -n 'PARSER TEST ONLY|model_alpha|mock_mmlu_redux|item_001' data/external/mmlu/lm_eval_outputs
```

The final command should return no matches for fixture markers.
