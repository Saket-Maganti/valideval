# Prompt 02 — MMLU Deep Diagnostic Value Run

## Objective

Extract more value from the existing 39-model MMLU panel without needing new model inference.

The current strongest real finding is subject-level rank sensitivity. This prompt deepens it into a paper-worthy empirical section.

## Inputs

```text
cache/mmlu/wide/matrix.csv
cache/mmlu/wide/predictions.jsonl
results/mmlu/irt/
results/mmlu/ranking_disagreement/
results/mmlu/real_panel_baselines/
```

## Analyses to run

Implement/run:

1. Subject-level rank variance distribution.
2. Per-model most/least favorable subjects.
3. Pairwise model rank reversals by subject.
4. Subject cluster analysis by model-performance profile.
5. Item difficulty vs subject rank instability.
6. Negative/low discrimination flags by subject.
7. Stability of top-1/top-3/top-5 models across subjects.
8. Bootstrap confidence intervals for subject rank ranges.
9. Materiality classification:
   - negligible,
   - moderate,
   - severe.
10. Model-family analysis if model metadata exists.

## Commands

Use existing CLI if available. Otherwise implement:

```bash
python3 -m valideval mmlu-deep-diagnostic-value   --matrix cache/mmlu/wide/matrix.csv   --predictions cache/mmlu/wide/predictions.jsonl   --irt results/mmlu/irt   --output results/mmlu/deep_diagnostic_value   --bootstrap 1000   --execute
```

## Required outputs

```text
results/mmlu/deep_diagnostic_value/subject_rank_ranges.csv
results/mmlu/deep_diagnostic_value/pairwise_rank_reversals.csv
results/mmlu/deep_diagnostic_value/model_subject_profiles.csv
results/mmlu/deep_diagnostic_value/subject_clusters.csv
results/mmlu/deep_diagnostic_value/bootstrap_rank_ranges.csv
results/mmlu/deep_diagnostic_value/materiality_summary.json
```

## Figures

```text
paper/figures/mmlu_subject_rank_range_distribution.pdf
paper/figures/mmlu_pairwise_rank_reversal_heatmap.pdf
paper/figures/mmlu_model_subject_profile_heatmap.pdf
paper/figures/mmlu_materiality_summary.pdf
```

## Report

Create:

```text
MMLU_DEEP_DIAGNOSTIC_VALUE_REPORT.md
```

Final verdict:

```text
MMLU_DEEP_FINDING_STRONG
MMLU_DEEP_FINDING_MODERATE
MMLU_DEEP_FINDING_WEAK
MMLU_DEEP_RUN_BLOCKED
```

## Claims allowed if supported

- subject-level ranking sensitivity is severe/moderate under defined materiality criteria,
- model ranking claims on aggregate MMLU can hide large subject-level variation,
- validity diagnostics should be reported with uncertainty and subject-level profiles.

Blocked:

- MMLU is invalid,
- ValidEval detects item errors,
- subject rank sensitivity proves benchmark invalidity.

## Verification

```bash
ruff check .
python3 -m pytest -q
```
