# Prompt 14 — Final Venue Gate and Submission Strategy

## Objective

Decide honestly whether ValidEval is ready for:

- NeurIPS Datasets & Benchmarks,
- ICLR/NeurIPS workshops,
- COLM/TMLR,
- DMLR/TMLR,
- or not ready.

## Read

```text
VALID_EVAL_EVIDENCE_RECONCILIATION_AUDIT.md
CLAIMS_AND_STORY_SYNC_AUDIT.md
MMLU_REAL_PANEL_CORE_RUN_REPORT.md
MMLU_REDUX_DIRECT_ALIGNMENT_VALIDATION_REPORT.md
MMLU_IRT_PSYCHOMETRIC_RUN_REPORT.md
MMLU_RANKING_DISAGREEMENT_BASELINES_REPORT.md
DECOUPLED_SYNTHETIC_EXECUTION_REPORT.md
SECOND_BENCHMARK_RUN_REPORT.md
FIGURE_TABLE_COMPLETENESS_AUDIT.md
PAPER_REWRITE_AND_COMPILE_REPORT.md
REVIEWER_PACKET_ZIP_AUDIT.md
NEURIPS_SUBMISSION_GO_NO_GO.md
paper/main.pdf
```

Use only existing artifacts.

## Gate criteria

### NeurIPS D&B / top target requires

- compiled paper,
- real ≥30-model panel,
- at least one real empirical finding,
- no circular synthetic evidence claim,
- all numbers trace to artifacts,
- MMLU-Redux framed honestly,
- baselines present,
- reviewer packet ready,
- related work complete,
- limitations explicit.

### TMLR/COLM requires

- compiled paper,
- one strong real panel,
- honest negative/cautionary finding,
- reproducible code/results,
- no major unsupported claims.

### Workshop requires

- coherent paper,
- honest evidence state,
- at least one real pilot/public-artifact analysis,
- clear future work.

## Create

```text
FINAL_SUBMISSION_GATE_AND_VENUE_STRATEGY.md
```

Structure:

```markdown
# Final Submission Gate and Venue Strategy

## 1. Executive Summary

## 2. Evidence Inventory

## 3. Paper Status

## 4. Reviewer Packet Status

## 5. NeurIPS D&B Gate

| Criterion | Status | Artifact |
|---|---|---|

## 6. TMLR/COLM Gate

| Criterion | Status | Artifact |
|---|---|---|

## 7. Workshop Gate

| Criterion | Status | Artifact |
|---|---|---|

## 8. Recommended Venue

## 9. Backup Venue

## 10. Claims To Emphasize

## 11. Claims To Avoid

## 12. Remaining Blockers

## 13. Final Verdict
```

Final verdict:

```text
NEURIPS_DB_READY_CANDIDATE
TMLR_COLM_READY_CANDIDATE
WORKSHOP_READY_ONLY
NOT_READY_FOR_SUBMISSION
```

Update go/no-go docs only with artifact-backed status.

## Verification

```bash
ruff check .
python3 -m pytest -q
```
