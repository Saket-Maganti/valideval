# Prompt 04 — Run GSM8K Diagnostics

## Objective

Run ValidEval diagnostics on the imported GSM8K matrix.

## Preconditions

```text
cache/gsm8k/wide/matrix.csv
cache/gsm8k/wide/predictions.jsonl
results/gsm8k/panel_validity/panel_validity.json
```

If missing, stop with:

```text
GSM8K_DIAGNOSTICS_BLOCKED_NO_MATRIX
```

## Analyses

- ranking sensitivity,
- diagnostic disagreement,
- baselines,
- item difficulty/discrimination proxy,
- bootstrap uncertainty,
- materiality summary.

## Required outputs

```text
results/gsm8k/real_panel_ranking_audit/
results/gsm8k/diagnostic_disagreement/
results/gsm8k/baselines/
results/gsm8k/bootstrap_materiality/
GSM8K_REAL_PANEL_DIAGNOSTICS_REPORT.md
```

## Final verdict

```text
GSM8K_DIAGNOSTICS_COMPLETE
GSM8K_DIAGNOSTICS_PARTIAL
GSM8K_DIAGNOSTICS_BLOCKED
```
