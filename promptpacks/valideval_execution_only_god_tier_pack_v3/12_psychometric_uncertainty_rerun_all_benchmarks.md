# Prompt 12 — Psychometric and Uncertainty Rerun Across All Available Benchmarks

## Objective

Rerun scalable psychometrics, bootstrap uncertainty, and materiality on every benchmark that has a valid matrix.

## Benchmarks

- MMLU always.
- GSM8K if imported.
- Third benchmark if imported.

## Outputs

```text
results/<benchmark>/scalable_irt_v3/
results/<benchmark>/bootstrap_materiality_v3/
results/<benchmark>/diagnostic_family_ablation_v3/
PSYCHOMETRIC_UNCERTAINTY_V3_REPORT.md
```

## Final verdict

```text
PSYCHOMETRIC_UNCERTAINTY_ALL_AVAILABLE_COMPLETE
PSYCHOMETRIC_UNCERTAINTY_MMLU_GSM8K_COMPLETE
PSYCHOMETRIC_UNCERTAINTY_MMLU_ONLY
PSYCHOMETRIC_UNCERTAINTY_BLOCKED
```
