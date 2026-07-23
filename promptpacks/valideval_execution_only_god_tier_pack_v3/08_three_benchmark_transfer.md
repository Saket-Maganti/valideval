# Prompt 08 — Three-Benchmark Transfer Execution

## Objective

If MMLU, GSM8K, and a third benchmark exist, run the full transfer study.

## Analyses

- model-rank stability across three benchmarks,
- diagnostic transfer matrix,
- benchmark construct separation,
- model family robustness,
- item difficulty distribution comparison,
- severe instability consistency,
- benchmark-specific failure modes.

## Outputs

```text
results/cross_benchmark/three_benchmark/
paper/figures/three_benchmark_rank_stability.pdf
paper/figures/three_benchmark_transfer_matrix.pdf
paper/tables/three_benchmark_summary.csv
THREE_BENCHMARK_TRANSFER_EXECUTION_REPORT.md
```

## Final verdict

```text
THREE_BENCHMARK_TRANSFER_STRONG
THREE_BENCHMARK_TRANSFER_MIXED
THREE_BENCHMARK_BLOCKED_NEED_THIRD_MATRIX
```
