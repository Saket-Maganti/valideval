# Artifact Manifest for Paper

## Evidence Tables

- `paper/tables/evidence_state_summary.csv`
- `paper/tables/evidence_state_summary.tex`
- `paper/tables/panel_shapes.csv`
- `paper/tables/panel_shapes.tex`
- `paper/tables/mmlu_panel_validity.csv`
- `paper/tables/mmlu_panel_validity.tex`
- `paper/tables/mmlu_irt_summary.csv`
- `paper/tables/mmlu_irt_summary.tex`
- `paper/tables/mmlu_redux_validation.csv`
- `paper/tables/mmlu_redux_validation.tex`
- `paper/tables/ranking_disagreement.csv`
- `paper/tables/ranking_disagreement.tex`
- `paper/tables/baseline_comparison.csv`
- `paper/tables/baseline_comparison.tex`
- `paper/tables/second_benchmark_summary.csv`
- `paper/tables/second_benchmark_summary.tex`
- `paper/tables/claims_allowed_blocked.csv`
- `paper/tables/claims_allowed_blocked.tex`

## Figures

- `paper/figures/panel_ability_spread.pdf`
- `paper/figures/panel_ability_spread.png`
- `paper/figures/mmlu_item_difficulty_distribution.pdf`
- `paper/figures/mmlu_item_difficulty_distribution.png`
- `paper/figures/mmlu_discrimination_distribution.pdf`
- `paper/figures/mmlu_discrimination_distribution.png`
- `paper/figures/mmlu_redux_validation_pr_curve.pdf`
- `paper/figures/mmlu_redux_validation_pr_curve.png`
- `paper/figures/mmlu_ranking_instability.pdf`
- `paper/figures/mmlu_ranking_instability.png`
- `paper/figures/diagnostic_disagreement_heatmap.pdf`
- `paper/figures/diagnostic_disagreement_heatmap.png`
- `paper/figures/mmlu_diagnostic_disagreement.pdf`
- `paper/figures/mmlu_diagnostic_disagreement.png`
- `paper/figures/baseline_comparison.pdf`
- `paper/figures/baseline_comparison.png`
- `paper/figures/mmlu_baseline_comparison.pdf`
- `paper/figures/mmlu_baseline_comparison.png`
- `paper/figures/evidence_gate_flow.pdf`
- `paper/figures/evidence_gate_flow.png`

## Source Result Artifacts

- `results/mmlu/panel_validity/panel_validity.json`
- `results/mmlu/real_panel_ranking_audit/real_panel_ranking_audit.json`
- `results/mmlu/diagnostic_disagreement/diagnostic_disagreement_audit.json`
- `results/mmlu/subject_instability/subject_instability_audit.json`
- `results/mmlu/ranking_disagreement/ranking_disagreement_summary.json`
- `results/mmlu/real_panel_baselines/baseline_summary.json`
- `results/mmlu/irt_proxy/fit_summary.json`
- `results/mmlu/irt_rasch/fit_summary.json`
- `results/mmlu/irt_2pl/fit_summary.json`
- `results/mmlu/redux_direct_alignment/schema_report.json`
- `results/mmlu/redux_direct_alignment/alignment_report.json`
- `results/mmlu/redux_validation/metrics.json`

## Blocked / Result-Required Artifacts

- Decoupled synthetic validation: `DECOUPLED_SYNTHETIC_EXECUTION_REPORT.md`
- Second benchmark run: `SECOND_BENCHMARK_RUN_REPORT.md`
- Kaggle import: `KAGGLE_OUTPUT_IMPORT_AND_VALIDATION_REPORT.md`
- Full parametric 2PL: `RESULT_REQUIRED`
- Direct/hash MMLU-Redux validation metrics: `RESULT_REQUIRED`

## Evidence Boundary

These artifacts support a cautious real-panel paper story centered on the 39-model HELM MMLU wide matrix, proxy psychometric diagnostics, and subject-level ranking sensitivity. They do not support claims of MMLU error detection, MMLU validity/invalidity, direct/hash Redux validation, second-benchmark evidence, full 2PL, or NeurIPS readiness.
