# MMLU Ranking Disagreement, Baselines, and Materiality Report

## Executive Summary

The ranking/disagreement prompt completed with saved artifacts. The strongest artifact-backed finding is subject-level rank sensitivity: every model has subject rank range >= 3, and the maximum subject rank range is 30. Proxy diagnostic-weighted ranking is very close to accuracy ranking, with max absolute rank delta 2 and no model at delta >= 3.

Final verdict: `PUBLISHABLE_REAL_PANEL_FINDING_FOUND`

This verdict means there is a cautious, paper-usable real-panel finding about subject-level ranking sensitivity under the observed matrix. It does not mean ValidEval detects MMLU errors or finds the true model ranking.

## Inputs

- Matrix: `cache/mmlu/wide/matrix.csv`
- IRT proxy: `results/mmlu/irt_proxy/`
- Bootstrap iterations: 1,000 per resampling baseline

## Ranking / Disagreement Results

- Spearman accuracy vs proxy diagnostic-weighted ranking: 0.9979757085020243
- Kendall accuracy vs proxy diagnostic-weighted ranking: 0.9784075573549258
- Max proxy diagnostic rank delta: 2
- Models with proxy diagnostic rank delta >= 3: 0

## Subject Instability

- Max subject rank range: 30
- Models with subject rank range >= 3: 39
- Models with subject rank range >= 10: 37

Top subject-instability rows are in `results/mmlu/ranking_disagreement/subject_instability.csv`.

## Baselines

| Baseline | Mean Spearman vs Full | Mean Top-5 Overlap | P95 Max Rank Delta | Top-1 Match |
|---|---:|---:|---:|---:|
| Random item bootstrap | 0.9987360759536542 | 0.9848 | 3.0 | 1.0 |
| Subject-stratified bootstrap | 0.9987457928704303 | 0.9838 | 3.0 | 1.0 |

Naive difficulty-only is not a model ranking baseline. Naive model disagreement is an item diagnostic, not an external label.

## Materiality

- Diagnostic rank delta >= 1: 11 models
- Diagnostic rank delta >= 3: 0 models
- Subject rank range >= 3: 39 models
- Subject rank range >= 10: 37 models

Materiality table: `results/mmlu/ranking_disagreement/materiality_thresholds.csv`

## Figures / Tables

Prompt 06 figure/table requests are fulfilled during Prompt 11 asset generation. The underlying data exists now:

- `results/mmlu/ranking_disagreement/accuracy_ranking.csv`
- `results/mmlu/ranking_disagreement/subject_rankings.csv`
- `results/mmlu/ranking_disagreement/subject_instability.csv`
- `results/mmlu/ranking_disagreement/accuracy_vs_diagnostic_rank_shift.csv`
- `results/mmlu/ranking_disagreement/baseline_comparison.csv`
- `results/mmlu/ranking_disagreement/materiality_thresholds.csv`

## Claims Allowed

- Subject-level rank sensitivity is artifact-backed under the active 39-model MMLU panel.
- Proxy diagnostic-weighted ranking was close to accuracy ranking in this run.
- Random and subject-stratified resampling baselines were run and saved.

## Claims Blocked

- True model ranking.
- MMLU validity or invalidity.
- MMLU error detection.
- External validation from MMLU-Redux.
- Full 2PL psychometric ranking.

## Final Verdict

`PUBLISHABLE_REAL_PANEL_FINDING_FOUND`
