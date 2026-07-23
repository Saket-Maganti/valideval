# Figure Table Completeness Audit

## Executive Summary

Paper assets were generated from existing artifacts only. The asset set is useful but not complete for a top-tier submission because direct/hash MMLU-Redux validation, decoupled synthetic validation, and second-benchmark evidence remain `RESULT_REQUIRED`.

Final verdict: `PAPER_ASSETS_PARTIAL_RESULT_REQUIRED`

## Required Tables

| Asset | CSV | LaTeX | Status |
|---|---|---|---|
| evidence_state_summary | `paper/tables/evidence_state_summary.csv` | `paper/tables/evidence_state_summary.tex` | ready |
| panel_shapes | `paper/tables/panel_shapes.csv` | `paper/tables/panel_shapes.tex` | ready |
| mmlu_panel_validity | `paper/tables/mmlu_panel_validity.csv` | `paper/tables/mmlu_panel_validity.tex` | ready |
| mmlu_irt_summary | `paper/tables/mmlu_irt_summary.csv` | `paper/tables/mmlu_irt_summary.tex` | ready, proxy-only |
| mmlu_redux_validation | `paper/tables/mmlu_redux_validation.csv` | `paper/tables/mmlu_redux_validation.tex` | partial; direct/hash rows are `[RESULT REQUIRED]` |
| ranking_disagreement | `paper/tables/ranking_disagreement.csv` | `paper/tables/ranking_disagreement.tex` | ready |
| baseline_comparison | `paper/tables/baseline_comparison.csv` | `paper/tables/baseline_comparison.tex` | ready |
| second_benchmark_summary | `paper/tables/second_benchmark_summary.csv` | `paper/tables/second_benchmark_summary.tex` | partial; evidence `RESULT_REQUIRED` |
| claims_allowed_blocked | `paper/tables/claims_allowed_blocked.csv` | `paper/tables/claims_allowed_blocked.tex` | ready |

## Required Figures

| Figure | PDF | PNG | Status |
|---|---|---|---|
| panel_ability_spread | yes | yes | ready |
| mmlu_item_difficulty_distribution | yes | yes | ready |
| mmlu_discrimination_distribution | yes | yes | ready |
| mmlu_redux_validation_pr_curve | yes | yes | status figure only; direct/hash curve `RESULT_REQUIRED` |
| mmlu_ranking_instability | yes | yes | ready |
| diagnostic_disagreement_heatmap | yes | yes | ready |
| baseline_comparison | yes | yes | ready |
| evidence_gate_flow | yes | yes | ready |

Additional prompt-06 figures:

- `paper/figures/mmlu_diagnostic_disagreement.pdf`
- `paper/figures/mmlu_diagnostic_disagreement.png`
- `paper/figures/mmlu_baseline_comparison.pdf`
- `paper/figures/mmlu_baseline_comparison.png`

## Missing / Blocked

- Direct/hash MMLU-Redux PR curve data.
- Decoupled synthetic validation result table.
- Second-benchmark panel/result tables.
- Full 2PL table.

## Final Verdict

`PAPER_ASSETS_PARTIAL_RESULT_REQUIRED`
