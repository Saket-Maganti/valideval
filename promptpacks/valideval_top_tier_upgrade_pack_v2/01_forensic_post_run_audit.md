# Prompt 01 — Forensic Post-Run Audit Before More Upgrades

## Objective

Before adding more runs, audit the current post-03–14 state. Confirm what is real, what is blocked, and what claims the paper can actually make.

## Inputs

Read:

```text
FINAL_SUBMISSION_GATE_AND_VENUE_STRATEGY.md
PAPER_REWRITE_AND_COMPILE_REPORT.md
MMLU_REAL_PANEL_CORE_RUN_REPORT.md
MMLU_RANKING_DISAGREEMENT_BASELINES_REPORT.md
MMLU_IRT_PSYCHOMETRIC_RUN_REPORT.md
MMLU_REDUX_DIRECT_ALIGNMENT_VALIDATION_REPORT.md
DECOUPLED_SYNTHETIC_EXECUTION_REPORT.md
SECOND_BENCHMARK_RUN_REPORT.md
KAGGLE_NOTEBOOK_BUILD_REPORT.md
KAGGLE_OUTPUT_IMPORT_AND_VALIDATION_REPORT.md
FIGURE_TABLE_COMPLETENESS_AUDIT.md
REVIEWER_PACKET_ZIP_AUDIT.md
CLAIMS_LEDGER_NEURIPS.md
paper/main.pdf
```

## Tasks

1. Confirm which result artifacts exist.
2. Confirm every numerical claim in paper reports traces to a file.
3. Confirm old 3-model language is no longer current.
4. Confirm synthetic evidence remains demoted.
5. Confirm MMLU-Redux remains weak/negative and direct/hash blocked.
6. Confirm ranking/disagreement findings are artifact-backed.
7. Confirm reviewer ZIP excludes raw/cache artifacts.
8. Confirm final gate is justified.

## Create

```text
FINAL_FORENSIC_POST_RUN_AUDIT.md
```

Final verdict:

```text
CURRENT_STATE_CONFIRMED_WORKSHOP_ONLY
CURRENT_STATE_HAS_OVERCLAIMS_FIX_REQUIRED
CURRENT_STATE_AMBIGUOUS_BLOCKED
```

## Verification

```bash
ruff check .
python3 -m pytest -q
```
