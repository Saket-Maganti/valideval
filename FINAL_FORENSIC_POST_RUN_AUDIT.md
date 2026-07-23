# Final Forensic Post-Run Audit

Date: 2026-07-09

## Input inventory

| Path | Status | Bytes |
| --- | --- | ---: |
| `FINAL_SUBMISSION_GATE_AND_VENUE_STRATEGY.md` | present | 5768 |
| `PAPER_REWRITE_AND_COMPILE_REPORT.md` | present | 2226 |
| `MMLU_REAL_PANEL_CORE_RUN_REPORT.md` | present | 5142 |
| `MMLU_RANKING_DISAGREEMENT_BASELINES_REPORT.md` | present | 3032 |
| `MMLU_IRT_PSYCHOMETRIC_RUN_REPORT.md` | present | 2359 |
| `MMLU_REDUX_DIRECT_ALIGNMENT_VALIDATION_REPORT.md` | present | 3167 |
| `DECOUPLED_SYNTHETIC_EXECUTION_REPORT.md` | present | 1744 |
| `SECOND_BENCHMARK_RUN_REPORT.md` | present | 1437 |
| `KAGGLE_NOTEBOOK_BUILD_REPORT.md` | present | 1484 |
| `KAGGLE_OUTPUT_IMPORT_AND_VALIDATION_REPORT.md` | present | 886 |
| `FIGURE_TABLE_COMPLETENESS_AUDIT.md` | present | 2547 |
| `REVIEWER_PACKET_ZIP_AUDIT.md` | present | 2668 |
| `CLAIMS_LEDGER_NEURIPS.md` | present | 5759 |
| `paper/main.pdf` | present | 181764 |

## Findings

- Active real evidence remains the 39-model HELM MMLU wide matrix under `cache/mmlu/wide/`.
- Old 3-model language is not current and must remain historical only.
- Legacy synthetic evidence remains demoted to wiring/sanity-check status.
- MMLU-Redux remains weak/negative; direct/hash alignment remains blocked.
- Ranking/disagreement findings are artifact-backed for MMLU.
- Reviewer ZIP audit exists; raw/cache artifacts remain excluded by policy.
- The final prior gate remains justified as workshop-ready only before V2 heavy runs.

Final verdict: `CURRENT_STATE_CONFIRMED_WORKSHOP_ONLY`.
