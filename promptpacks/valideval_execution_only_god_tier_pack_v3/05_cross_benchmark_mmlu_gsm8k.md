# Prompt 05 — Cross-Benchmark MMLU ↔ GSM8K Execution

## Objective

Create the first true cross-benchmark evidence surface.

## Inputs

```text
cache/mmlu/wide/matrix.csv
cache/gsm8k/wide/matrix.csv
results/mmlu/deep_diagnostic_value/
results/gsm8k/real_panel_ranking_audit/
```

If GSM8K matrix is missing, create `CROSS_BENCHMARK_BLOCKED_NO_GSM8K_MATRIX.md`.

## Analyses

1. Model ID overlap and mapping.
2. Accuracy correlation.
3. Ability/proxy ability correlation.
4. Rank correlation.
5. Rank instability comparison.
6. Diagnostic-family transfer.
7. Severe-instability transfer.
8. Benchmark-specific vs general instability.
9. Materiality transfer.
10. Top-k model stability.

## Outputs

```text
results/cross_benchmark/mmlu_gsm8k/model_overlap.csv
results/cross_benchmark/mmlu_gsm8k/ranking_correlations.csv
results/cross_benchmark/mmlu_gsm8k/diagnostic_transfer.csv
results/cross_benchmark/mmlu_gsm8k/materiality_transfer.csv
results/cross_benchmark/mmlu_gsm8k/summary.json
paper/figures/mmlu_gsm8k_rank_correlation.pdf
paper/figures/mmlu_gsm8k_instability_transfer.pdf
paper/tables/mmlu_gsm8k_cross_benchmark_summary.csv
CROSS_BENCHMARK_MMLU_GSM8K_EXECUTION_REPORT.md
```

## Final verdict

```text
CROSS_BENCHMARK_EVIDENCE_STRONG
CROSS_BENCHMARK_EVIDENCE_MIXED
CROSS_BENCHMARK_EVIDENCE_WEAK
CROSS_BENCHMARK_BLOCKED_NO_GSM8K_MATRIX
```
