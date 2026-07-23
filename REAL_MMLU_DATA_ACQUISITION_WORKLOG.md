# Real MMLU Data Acquisition Worklog

Timestamp UTC: 2026-06-12T09:39:55Z

## Scope

Build the real MMLU per-instance prediction-detail evidence path using
lm-evaluation-harness outputs, then import those outputs into ValidEval wide
prediction and matrix caches.

This worklog is evidence bookkeeping only. It does not treat mock, fixture, or
example files as real benchmark evidence.

## Git State

The checkout has no committed baseline in the local `.git` repository. `git
status --short` reports the repository contents as untracked.

## Available Mock Or Example Files

These files exist and must not be used as real MMLU evidence:

- `examples/mmlu_subset.jsonl`
- `examples/mmlu_redux_mock.jsonl`
- `examples/mmlu_redux_mock.csv`
- `examples/wide_predictions_mock.jsonl`
- `examples/wide_predictions_mock.csv`

## Missing Real Files At Start

- `data/external/mmlu/lm_eval_outputs/`: missing at start.
- `cache/mmlu/wide/predictions.jsonl`: missing at start.
- `cache/mmlu/wide/matrix.csv`: missing at start.
- `data/ground_truth/mmlu_redux_issues.normalized.jsonl`: missing at start.

## Available CLI Commands

Observed `python3 -m valideval --help` includes:

- `import-published-details`
- `matrix-from-wide-predictions`
- `import-ground-truth`
- `mmlu-redux-validation`

Observed `python3 -m valideval import-published-details --help` supports:

- `--format auto`
- `--format helm_json`
- `--format helm_jsonl`
- `--format leaderboard_csv`
- `--format leaderboard_jsonl`
- `--format lm_eval_dir`
- `--format lm_eval_jsonl`

Observed `python3 -m valideval matrix-from-wide-predictions --help` supports:

- `--predictions`
- `--output`
- `--report`
- `--disallow-missing`

## Python, Device, And Disk

- Python: `Python 3.11.9`
- pip: `pip 26.0.1`
- torch: `2.11.0`
- CUDA available: `false`
- CUDA device count: `0`
- MPS available: `true`
- Current filesystem availability: about `30Gi` free on `/System/Volumes/Data`

## lm-evaluation-harness Status

At Stage 1 start:

- `which lm_eval`: not found
- `python3 -m lm_eval --help`: `No module named lm_eval`

Next action: install `lm-eval` in the current Python environment. If install
fails, create `LM_EVAL_INSTALL_BLOCKED.md` and stop without using mock files.

## Stage Completion Update

Timestamp UTC: 2026-06-12T10:04:24Z

- Installed `lm-eval 0.4.12`.
- Installed missing Hugging Face runtime dependency `accelerate 1.14.0`.
- Ran real lm-eval smoke on `Qwen/Qwen2.5-0.5B-Instruct`,
  `mmlu_high_school_biology`, `--limit 25`, MPS, `batch_size=1`.
- Ran real limited multi-model pilot on `mmlu_high_school_biology`,
  `--limit 500`, MPS, `batch_size=1`.
- Imported real lm-eval sample outputs into
  `cache/mmlu/wide/predictions.jsonl`.
- Built `cache/mmlu/wide/matrix.csv`.
- Verified final normalized predictions contain `930` rows, `3` models, `310`
  items, and no fixture/mock marker strings.

Evidence scope: limited MMLU high-school-biology pilot only. Full all-subject
MMLU is not claimed.
