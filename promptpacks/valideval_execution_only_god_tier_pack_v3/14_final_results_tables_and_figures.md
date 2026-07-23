# Prompt 14 — Final Results Tables and Figures

## Objective

Create paper-ready tables and figures from real artifacts only.

## Tables

- benchmark panel summary,
- MMLU rank sensitivity,
- GSM8K diagnostics if present,
- cross-benchmark summary if present,
- psychometric/uncertainty summary,
- human/external label status,
- claim gate table,
- artifact manifest table.

## Outputs

```text
paper/tables/main_results_table.tex
paper/tables/benchmark_panel_summary.tex
paper/tables/cross_benchmark_summary.tex
paper/tables/claim_gate_table.tex
MAIN_RESULTS_TABLES_AND_FIGURES_V3_REPORT.md
```

## Rules

- No invented cells.
- Use `Blocked` for missing evidence.
- Every numeric result must trace to a file.

## Final verdict

```text
MAIN_RESULTS_ASSETS_READY
MAIN_RESULTS_ASSETS_PARTIAL
MAIN_RESULTS_ASSETS_BLOCKED
```
