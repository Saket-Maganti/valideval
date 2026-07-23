# Prompt 11 — Figures, Tables, and Artifact Manifest

## Objective

Turn completed real runs into paper-ready tables/figures and a clean artifact manifest.

## Inputs

Use existing artifacts only:

```text
MMLU_REAL_PANEL_CORE_RUN_REPORT.md
MMLU_REDUX_DIRECT_ALIGNMENT_VALIDATION_REPORT.md
MMLU_IRT_PSYCHOMETRIC_RUN_REPORT.md
MMLU_RANKING_DISAGREEMENT_BASELINES_REPORT.md
DECOUPLED_SYNTHETIC_EXECUTION_REPORT.md
SECOND_BENCHMARK_RUN_REPORT.md
results/mmlu/
results/decoupled_synthetic/
results/<second_benchmark>/
```

Do not invent missing results.

## Tables

Create CSV and LaTeX where possible under `paper/tables/`:

```text
evidence_state_summary
panel_shapes
mmlu_panel_validity
mmlu_irt_summary
mmlu_redux_validation
ranking_disagreement
baseline_comparison
second_benchmark_summary
claims_allowed_blocked
```

For missing results, write `[RESULT REQUIRED]`.

## Figures

Create PDF and PNG where data exists under `paper/figures/`:

```text
panel_ability_spread
mmlu_item_difficulty_distribution
mmlu_discrimination_distribution
mmlu_redux_validation_pr_curve
mmlu_ranking_instability
diagnostic_disagreement_heatmap
baseline_comparison
evidence_gate_flow
```

No raw question text.

## Reports

Create:

```text
ARTIFACT_MANIFEST_FOR_PAPER.md
FIGURE_TABLE_COMPLETENESS_AUDIT.md
```

Final verdict for asset audit:

```text
PAPER_ASSETS_READY
PAPER_ASSETS_PARTIAL_RESULT_REQUIRED
PAPER_ASSETS_BLOCKED
```

## Verification

```bash
ruff check .
python3 -m pytest -q
```
