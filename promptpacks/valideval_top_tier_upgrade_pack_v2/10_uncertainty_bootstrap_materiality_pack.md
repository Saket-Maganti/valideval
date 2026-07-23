# Prompt 10 — Uncertainty, Bootstrap, and Materiality Pack

## Objective

Make all ranking and diagnostic claims statistically cautious.

## Analyses

1. bootstrap CI for model accuracy,
2. bootstrap CI for subject rank range,
3. bootstrap CI for diagnostic-weighted rank deltas,
4. item-resampling uncertainty,
5. subject-stratified bootstrap,
6. materiality thresholds,
7. sensitivity to threshold choices,
8. multiple-comparison caution.

## Command

```bash
python3 -m valideval bootstrap-materiality   --matrix cache/mmlu/wide/matrix.csv   --diagnostics results/mmlu/irt   --output results/mmlu/bootstrap_materiality   --bootstrap 2000   --execute
```

## Outputs

```text
results/mmlu/bootstrap_materiality/accuracy_ci.csv
results/mmlu/bootstrap_materiality/rank_range_ci.csv
results/mmlu/bootstrap_materiality/materiality_threshold_sensitivity.csv
paper/figures/bootstrap_rank_uncertainty.pdf
paper/tables/materiality_threshold_sensitivity.csv
```

## Report

```text
BOOTSTRAP_MATERIALITY_REPORT.md
```

Final verdict:

```text
UNCERTAINTY_MATERIALITY_COMPLETE
UNCERTAINTY_MATERIALITY_PARTIAL
UNCERTAINTY_MATERIALITY_BLOCKED
```
