# Prompt 08 — Cross-Benchmark Stability and Transfer

## Objective

Once MMLU + at least one second benchmark exist, analyze whether ValidEval findings transfer.

## Inputs

```text
cache/mmlu/wide/matrix.csv
cache/gsm8k/wide/matrix.csv
cache/<third>/wide/matrix.csv
results/mmlu/
results/gsm8k/
results/<third>/
```

## Analyses

1. Model ranking correlation across benchmarks.
2. Ability estimate correlation.
3. Diagnostics correlation across benchmarks.
4. Item difficulty distribution comparison.
5. Rank instability comparison.
6. Diagnostic-disagreement rate comparison.
7. Benchmark construct difference summary.
8. Cross-benchmark materiality table.

## Outputs

```text
results/cross_benchmark/stability.json
results/cross_benchmark/ranking_correlations.csv
results/cross_benchmark/diagnostic_transfer.csv
paper/figures/cross_benchmark_rank_correlation.pdf
paper/figures/cross_benchmark_diagnostic_transfer.pdf
paper/tables/cross_benchmark_summary.csv
```

## Report

```text
CROSS_BENCHMARK_STABILITY_AND_TRANSFER_REPORT.md
```

Final verdict:

```text
CROSS_BENCHMARK_EVIDENCE_STRONG
CROSS_BENCHMARK_EVIDENCE_PARTIAL
CROSS_BENCHMARK_BLOCKED_NEED_SECOND_BENCHMARK
```
