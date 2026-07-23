# Second Benchmark Run Report

## Executive Summary

Second-benchmark execution did not complete locally. GSM8K and TruthfulQA preflights are dry-run ready only; no data download, model inference, import, matrix creation, or panel-validity run was performed.

Final verdict: `SECOND_BENCHMARK_CPU_BLOCKED_USE_KAGGLE`

## Commands

- `python3 -m valideval benchmark-preflight --config configs/benchmarks/gsm8k_audit.yaml --output results/gsm8k/preflight.json --dry-run`
- `python3 -m valideval benchmark-preflight --config configs/benchmarks/truthfulqa_audit.yaml --output results/truthfulqa/preflight.json --dry-run`

## Results

- GSM8K preflight status: `dry_run_ready`
- TruthfulQA preflight status: `dry_run_ready`
- Download run: false
- Evaluation run: false
- Matrix created: false
- Panel-validity run: false

## GPQA Note

An attempted readiness invocation against an existing JSON artifact failed because the file is not a matrix CSV. No GPQA second-benchmark evidence is claimed.

## Claims Allowed

- GSM8K and TruthfulQA have scaffold/preflight configs.
- GSM8K is the recommended next execution target.
- Kaggle package is required for the next panel run unless a public wide artifact is supplied.

## Claims Blocked

- Second-benchmark evidence.
- Cross-benchmark generalization.
- Second-benchmark panel validity.
- Ranking/disagreement on a second benchmark.

## Final Verdict

`SECOND_BENCHMARK_CPU_BLOCKED_USE_KAGGLE`
