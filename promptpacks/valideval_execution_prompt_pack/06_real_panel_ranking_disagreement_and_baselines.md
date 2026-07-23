# Prompt 06 — Ranking Disagreement, Baselines, and Materiality

## Objective

Find whether ValidEval has a paper-worthy real-panel finding:

- ranking instability,
- subject-level rank flips,
- diagnostic-vs-accuracy disagreement,
- item subset sensitivity,
- baseline comparison,
- materiality.

## Inputs

Use whatever exists:

```text
cache/mmlu/wide/matrix.csv
cache/mmlu/wide/predictions.jsonl
results/mmlu/irt_proxy/
results/mmlu/irt_rasch/
results/mmlu/redux_validation_direct/
```

## Analyses

Run or implement:

1. Full accuracy ranking.
2. Subject-wise rankings.
3. Pairwise rank instability across subjects.
4. Accuracy vs IRT-weighted or validity-adjusted ranking if implemented.
5. Accuracy on suspicious-item subsets vs proxy-clean subsets.
6. Random subset baseline.
7. Subject-stratified random subset baseline.
8. Naive difficulty baseline.
9. Naive disagreement baseline.
10. Bootstrap uncertainty for rank differences.
11. Materiality threshold table.

Suggested commands:

```bash
python3 -m valideval ranking-disagreement   --matrix cache/mmlu/wide/matrix.csv   --irt results/mmlu/irt_proxy   --output results/mmlu/ranking_disagreement   --bootstrap 1000   --execute

python3 -m valideval real-panel-baselines   --matrix cache/mmlu/wide/matrix.csv   --output results/mmlu/real_panel_baselines   --bootstrap 1000   --execute
```

If commands do not exist, implement minimal equivalents.

## Figures

Create if data exists:

```text
paper/figures/mmlu_ranking_instability.pdf
paper/figures/mmlu_subject_rank_heatmap.pdf
paper/figures/mmlu_diagnostic_disagreement.pdf
paper/figures/mmlu_baseline_comparison.pdf
```

Also save PNG.

## Tables

```text
paper/tables/mmlu_top_rank_changes.csv
paper/tables/mmlu_subject_instability.csv
paper/tables/mmlu_diagnostic_baselines.csv
paper/tables/mmlu_materiality.csv
```

## Report

```text
MMLU_RANKING_DISAGREEMENT_BASELINES_REPORT.md
```

Final verdict:

```text
PUBLISHABLE_REAL_PANEL_FINDING_FOUND
REAL_PANEL_FINDING_WEAK_NEGATIVE
REAL_PANEL_ANALYSIS_BLOCKED
```

## Verification

```bash
ruff check .
python3 -m pytest -q
```
