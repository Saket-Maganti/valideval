# Cross-Benchmark Runner V4 Report

Implemented command:

```bash
python3 -m valideval cross-benchmark-analysis \
  --benchmarks mmlu,gsm8k,bbh \
  --cache-root cache \
  --results-root results \
  --output results/cross_benchmark \
  --execute
```

Implemented behavior:

- Detects available cached matrices.
- Requires at least two benchmarks.
- Normalizes model IDs.
- Computes model overlap.
- Computes ranking correlations.
- Computes ability correlations with IRT ability files when available, otherwise matrix-accuracy proxy.
- Computes diagnostic-transfer, instability-transfer, and materiality-transfer summaries.
- Writes CSV tables and an SVG correlation figure.
- Writes paper table CSVs when `paper/tables/` exists.

Current repo state: only MMLU is available, so the live run wrote a blocked report.

Tests: `tests/test_cross_benchmark_runner_v4.py`.

Final verdict: `CROSS_BENCHMARK_RUNNER_BLOCKED_NEED_SECOND_MATRIX`
