# MMLU Real-Panel Core Run Report

## 1. Executive Summary

The active real MMLU panel run completed on the reconciled 39-model HELM wide matrix. The panel-validity gate passed, and aggregate real-panel ranking, subject-instability, diagnostic-disagreement, and baseline artifacts were written.

This clears only the active MMLU panel-size blocker and makes real-panel ranking/disagreement analyses artifact-backed. It does not validate MMLU-Redux alignment, does not detect MMLU errors, and does not claim MMLU is valid or invalid.

## 2. Inputs

- Matrix: `cache/mmlu/wide/matrix.csv`
- Predictions: `cache/mmlu/wide/predictions.jsonl`
- Source HELM details: `data/external/mmlu/prediction_details_wide.jsonl`
- Reconciliation gate: `VALID_EVAL_EVIDENCE_RECONCILIATION_AUDIT.md`

## 3. Panel Shape

- Models: 39
- Scored items: 14,042
- Matrix CSV shape: 39 rows x 14,043 columns including `model_id`
- Missing fraction: 0.0
- Subjects inferred from item columns: 57

## 4. Panel Validity Gate

- Command: `python3 -m valideval panel-validity --matrix cache/mmlu/wide/matrix.csv --output results/mmlu/panel_validity --strict`
- Status: `pass`
- Ability spread: 0.5801880074063523
- Blockers: none

Artifacts:

- `results/mmlu/panel_validity/panel_validity.json`
- `results/mmlu/panel_validity/panel_validity.md`

## 5. Accuracy Ranking

The accuracy ranking artifact was written at `results/mmlu/real_panel_ranking_audit/accuracy_ranking.csv`.

Top accuracy models in this matrix:

| Rank | Model | Accuracy |
|---:|---|---:|
| 1 | `deepseek-ai/deepseek-v3` | 0.867611 |
| 2 | `meta/llama-3.1-405b-instruct-turbo` | 0.849024 |
| 3 | `qwen/qwen2.5-72b-instruct-turbo` | 0.833072 |
| 4 | `qwen/qwen2-72b-instruct` | 0.827446 |
| 5 | `meta/llama-3.2-90b-vision-instruct-turbo` | 0.810924 |

## 6. Subject Instability

Subject-level rank sensitivity was artifact-backed:

- Max subject rank range: 30
- Models with subject rank range >= 3: 39
- Main artifact: `results/mmlu/subject_instability/subject_instability.csv`

This is ranking-sensitivity evidence under the observed subject partitions. It is not a true-ranking claim.

## 7. Diagnostic Disagreement

The diagnostic-disagreement audit completed using existing proxy IRT item parameters available at execution time.

- Spearman accuracy vs diagnostic-weighted ranking: 0.9979757085020243
- Kendall accuracy vs diagnostic-weighted ranking: 0.9784075573549258
- Max absolute rank delta: 2
- Models with absolute rank delta >= 3: 0

This supports a cautious finding: subject partitions create larger rank sensitivity than the proxy diagnostic-weighted ranking in this run.

## 8. Baselines

The baseline audit completed with 1,000 random-item bootstrap and 1,000 subject-stratified bootstrap iterations.

- Random bootstrap mean Spearman vs full ranking: 0.9987360759536542
- Subject-stratified bootstrap mean Spearman vs full ranking: 0.9987457928704303
- Top-1 match rate: 1.0 for both resampling baselines
- 95th percentile max absolute rank delta: 3.0 for both resampling baselines

Artifacts:

- `results/mmlu/real_panel_baselines/baseline_summary.json`
- `results/mmlu/real_panel_baselines/baseline_comparison.csv`
- `results/mmlu/real_panel_baselines/baseline_iterations.csv`
- `results/mmlu/real_panel_baselines/real_panel_baseline_comparison.md`

## 9. What Can Be Claimed

- The active MMLU panel is the 39-model HELM wide matrix.
- The active MMLU panel-size blocker is cleared.
- Panel-validity passed under the implemented gate.
- Accuracy ranking, subject-instability, proxy diagnostic disagreement, and resampling baselines now have saved artifacts.
- Subject-level rank sensitivity exists under this matrix and protocol.

## 10. What Cannot Be Claimed

- Do not claim MMLU error detection.
- Do not claim MMLU is valid or invalid.
- Do not claim direct/hash MMLU-Redux alignment.
- Do not claim external validation success.
- Do not claim full 2PL or a true model ranking.

## 11. Result Artifacts

- `results/mmlu/real_panel_ranking_audit/real_panel_ranking_audit.json`
- `results/mmlu/real_panel_ranking_audit/real_panel_ranking_audit.md`
- `results/mmlu/real_panel_ranking_audit/accuracy_ranking.csv`
- `results/mmlu/diagnostic_disagreement/diagnostic_disagreement_audit.json`
- `results/mmlu/diagnostic_disagreement/diagnostic_disagreement_audit.md`
- `results/mmlu/diagnostic_disagreement/accuracy_vs_diagnostic_rank_shift.csv`
- `results/mmlu/diagnostic_disagreement/suspicious_subset_sensitivity.csv`
- `results/mmlu/subject_instability/subject_instability_audit.json`
- `results/mmlu/subject_instability/subject_instability_audit.md`
- `results/mmlu/subject_instability/subject_rankings.csv`
- `results/mmlu/subject_instability/subject_instability.csv`
- `results/mmlu/subject_instability/pairwise_subject_rank_flips.csv`
- `results/mmlu/real_panel_baselines/baseline_summary.json`

## 12. Failures / Limitations

- MMLU-Redux remains weak/negative and not direct/hash aligned.
- Diagnostic weighting is proxy-based, not external validation.
- Baselines quantify sensitivity but do not provide external labels.

## 13. Final Verdict

`REAL_PANEL_CORE_RUN_COMPLETE`
