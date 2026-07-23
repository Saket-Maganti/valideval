# Second Benchmark Build Plan

## Summary

The no-run second benchmark scaffold uses GSM8K as the primary candidate and TruthfulQA as the
fallback candidate.

## Current state

`RESULT_REQUIRED`. No downloads, scoring, model generation, or benchmark evaluation were run.

## Files

- `src/valideval/benchmarks/gsm8k.py`
- `src/valideval/benchmarks/truthfulqa.py`
- `src/valideval/benchmarks/preflight.py`
- `configs/benchmarks/gsm8k_audit.yaml`
- `configs/benchmarks/truthfulqa_audit.yaml`
- `tests/test_second_benchmark_preflight.py`

## Command

```bash
python3 -m valideval benchmark-preflight --dry-run --config configs/benchmarks/gsm8k_audit.yaml
```

## Claim boundary

Do not claim second-benchmark evidence until a future approved run creates a matching artifact.
