# ValidEval Evidence Reconciliation Audit

Audit date: 2026-07-08

Scope: prompt-pack prompts `00_global_execution_rules.md` and
`01_evidence_reconciliation_gate.md` only. This audit performs shape-only
inspection and status reconciliation. It does not run diagnostics, recompute
metrics, run inference, download files, or upgrade claims.

## 1. Executive Summary

The active MMLU evidence source is the 39-model HELM MMLU wide panel, not the
older 3-model pilot. Shape-only inspection found:

- `cache/mmlu/wide/matrix.csv`: 39 model rows, 14,042 item columns, 57 subjects.
- `cache/mmlu/wide/predictions.jsonl`: 547,638 rows, 39 models, 14,042 items,
  57 subjects.
- `data/external/mmlu/prediction_details_wide.jsonl`: 547,638 rows, 39 models,
  14,042 items, 57 subjects.
- `results/mmlu/panel_validity/panel_validity.json`: `status=pass`,
  `n_models=39`, `n_items=14042`, `missing_fraction=0.0`.

The 3-model files still exist as backups and limited-pilot documentation. They
are important provenance, but they are not the active panel. Some older status
documents can still be misread as current truth, so claim/status docs should be
cleaned in the next approved prompt. Per the user instruction to stop after
creating this audit, this pass does not edit those downstream docs.

Final verdict: `39_MODEL_PANEL_PRESENT_BUT_DOCS_STALE`.

## 2. Files Inspected

Prompt pack read completely:

- `valideval_execution_prompt_pack/README_INDEX.md`
- `valideval_execution_prompt_pack/00_global_execution_rules.md`
- `valideval_execution_prompt_pack/01_evidence_reconciliation_gate.md`
- `valideval_execution_prompt_pack/02_claims_and_paper_story_sync.md`
- `valideval_execution_prompt_pack/03_real_panel_helm_mmlu_core_runs.md`
- `valideval_execution_prompt_pack/04_mmlu_redux_direct_alignment_and_validation.md`
- `valideval_execution_prompt_pack/05_irt_and_psychometric_runs.md`
- `valideval_execution_prompt_pack/06_real_panel_ranking_disagreement_and_baselines.md`
- `valideval_execution_prompt_pack/07_decoupled_synthetic_execution_protocol.md`
- `valideval_execution_prompt_pack/08_second_benchmark_selection_and_cpu_path.md`
- `valideval_execution_prompt_pack/09_kaggle_gpu_notebook_builder.md`
- `valideval_execution_prompt_pack/10_kaggle_results_import_and_validation.md`
- `valideval_execution_prompt_pack/11_figures_tables_and_artifact_manifest.md`
- `valideval_execution_prompt_pack/12_paper_rewrite_compile_and_appendix.md`
- `valideval_execution_prompt_pack/13_reviewer_packet_rebuild_and_zip_audit.md`
- `valideval_execution_prompt_pack/14_final_venue_gate_and_submission_strategy.md`

Required evidence paths inspected:

- `cache/mmlu/`
- `cache/mmlu/wide/`
- `cache/mmlu/wide/backups/`
- `data/external/mmlu/`
- `data/external/mmlu/backups/`
- `data/external/mmlu/lm_eval_outputs/`
- `results/mmlu/`
- `results/mmlu/panel_validity/`
- `results/mmlu/irt/`
- `results/mmlu/redux_validation/`
- `results/mmlu/redux_issue_specific_validation_subject_normalized/`
- `results/mmlu/redux_label_error_subject_matched_null_confirmatory/`
- `results/neurips_small_runs/`
- `LIMITED_REAL_MMLU_PANEL_VALIDITY_REPORT.md`
- `MMLU_WIDE_PANEL_ACQUISITION_REPORT.md`
- `MMLU_PANEL_VALIDITY_REPORT.md`
- `MMLU_EVIDENCE_GATE_REPORT.md`
- `MMLU_REDUX_WEAK_SIGNAL_DIAGNOSIS.md`
- `MMLU_REDUX_SUBJECT_NORMALIZED_VALIDATION_REPORT.md`
- `REAL_EMPIRICAL_SPINE_REFRAME.md`
- `FINAL_NO_RUN_READINESS_AUDIT.md`
- `NEURIPS_SUBMISSION_GO_NO_GO.md`
- `CLAIMS_LEDGER_NEURIPS.md`
- `paper/CLAIMS_LEDGER.md`
- `paper/claims.md`
- `paper/experiments.md`
- `paper/reframed_abstract_negative_result.md`
- `paper/reframed_intro_negative_result.md`

Inspection commands run:

- Shape-only Python inspection from prompt 01.
- File inventories for `cache/mmlu`, `data/external/mmlu`, `results/mmlu`,
  and `results/neurips_small_runs`.
- Contradictory-claim search over docs, code, configs, and JSON status files.
- Additional shape-only summary for the active wide files and preserved
  3-model backups.

## 3. Matrix Artifacts Found

| Path | Exists? | Rows | Models | Items | Subjects | Notes |
|---|---:|---:|---:|---:|---:|---|
| `cache/mmlu/wide/matrix.csv` | yes | 39 | 39 | 14,042 | 57 | Active wide matrix. First column is `model_id`; remaining columns are item ids. |
| `cache/mmlu/wide/predictions.jsonl` | yes | 547,638 | 39 | 14,042 | 57 | Active imported wide predictions. |
| `data/external/mmlu/prediction_details_wide.jsonl` | yes | 547,638 | 39 | 14,042 | 57 | Active normalized public HELM source file. |
| `data/external/mmlu/matrix.csv` | no |  |  |  |  | Prompt-listed path is absent; active matrix is under `cache/mmlu/wide/`. |
| `results/mmlu/irt/item_parameters.csv` | yes | 14,042 |  | 14,042 | 57 | Proxy IRT item-parameter artifact. |
| `results/mmlu/panel_validity/panel_validity_report.json` | no |  |  |  |  | Prompt-listed filename is absent. |
| `results/mmlu/panel_validity/panel_validity.json` | yes |  | 39 | 14,042 |  | Current panel-validity JSON; `status=pass`. |
| `cache/mmlu/wide/backups/three_model_matrix_20260612T160228Z.csv` | yes | 3 | 3 | 14,042 | 57 | Preserved predecessor matrix, not active. |
| `cache/mmlu/wide/backups/three_model_predictions_20260612T160228Z.jsonl` | yes | 42,126 | 3 | 14,042 | 57 | Preserved predecessor predictions, not active. |
| `data/external/mmlu/backups/three_model_prediction_details_20260612T160228Z.jsonl` | yes | 42,126 | 3 | 14,042 | 57 | Preserved predecessor source file, not active. |

The active wide prediction row count equals `39 * 14,042 = 547,638`.

## 4. Active Evidence Source

The active evidence chain is:

```text
data/external/mmlu/prediction_details_wide.jsonl
-> cache/mmlu/wide/predictions.jsonl
-> cache/mmlu/wide/matrix.csv
-> results/mmlu/panel_validity/panel_validity.json
```

Current status:

- Active matrix: `cache/mmlu/wide/matrix.csv`
- Active imported predictions: `cache/mmlu/wide/predictions.jsonl`
- Active normalized public source: `data/external/mmlu/prediction_details_wide.jsonl`
- Panel-validity status: `pass`
- Missing fraction: `0.0`
- Evidence source: public HELM MMLU artifacts, no model inference in this
  reconciliation pass.

The report `MMLU_WIDE_PANEL_ACQUISITION_REPORT.md` also records the active
cache rebuild, 39 model rows, 14,042 item columns, 0 missing cells, and a
passing strict panel-validity gate.

## 5. 3-Model Pilot Status

The 3-model evidence is historical or limited-pilot evidence, not the current
active panel.

Relevant artifacts:

- `LIMITED_REAL_MMLU_PANEL_VALIDITY_REPORT.md`
- `data/external/mmlu/lm_eval_outputs/`
- `cache/mmlu/wide/backups/three_model_matrix_20260612T160228Z.csv`
- `cache/mmlu/wide/backups/three_model_predictions_20260612T160228Z.jsonl`
- `data/external/mmlu/backups/three_model_prediction_details_20260612T160228Z.jsonl`

The limited report records a 3-model, 310-item `mmlu_high_school_biology` pilot
that was blocked by `model_count_below_30`. The backup files record the
previous 3-model all-subject wide cache before the 39-model active cache was
rebuilt. These artifacts should be cited only as provenance or pilot evidence.
They should not be used to claim that the current active panel has only 3
models.

## 6. 39-Model Panel Status

The 39-model panel is present and active.

Artifact-backed status:

- `data/external/mmlu/prediction_details_wide.jsonl`: found, 615,154,346 bytes,
  547,638 rows.
- `cache/mmlu/wide/predictions.jsonl`: found, 692,918,942 bytes, 547,638 rows.
- `cache/mmlu/wide/matrix.csv`: found, 2,872,534 bytes, 39 rows and 14,042 item
  columns.
- `cache/mmlu/wide/predictions.jsonl.summary.json`: `status=ok`,
  `model_count=39`, `item_count=14042`, `rows_read=547638`,
  `rows_written=547638`.
- `results/mmlu/panel_validity/panel_validity.json`: `status=pass`,
  `n_models=39`, `n_items=14042`, `missing_fraction=0.0`.

Allowed interpretation: the panel-size blocker is cleared for this active MMLU
matrix under the current panel-validity gate. This does not by itself establish
MMLU validity, invalidity, or diagnostic detection success.

## 7. IRT Status

Proxy IRT artifacts exist for the active 39-model matrix:

- `results/mmlu/irt/fit_summary.json`
- `results/mmlu/irt/fit_summary.md`
- `results/mmlu/irt/item_parameters.csv`
- `results/mmlu/irt/model_abilities.csv`
- `results/mmlu/irt/flags.jsonl`

Shape-only inspection found `results/mmlu/irt/item_parameters.csv` with 14,042
rows. The fit summary states that proxy estimation ran, while Rasch/1PL and full
parametric 2PL were not run or are unavailable in this artifact set.

Allowed claim: proxy item-level psychometric diagnostics exist for the active
39-model panel.

Blocked claim: full psychometric IRT, full 2PL, or externally validated item
flaw detection.

## 8. MMLU-Redux Status

MMLU-Redux artifacts exist and should be interpreted as weak or negative
external-validation evidence under the current protocol.

Relevant artifacts:

- `results/mmlu/redux_validation/metrics.json`
- `results/mmlu/redux_validation/summary.md`
- `results/mmlu/redux_validation/top_flagged_items_sanitized.md`
- `results/mmlu/redux_issue_specific_validation_subject_normalized/`
- `results/mmlu/redux_label_error_subject_matched_null_confirmatory/`
- `MMLU_REDUX_WEAK_SIGNAL_DIAGNOSIS.md`
- `MMLU_REDUX_SUBJECT_NORMALIZED_VALIDATION_REPORT.md`
- `MMLU_EVIDENCE_GATE_REPORT.md`

Shape/status inspection found the broad matrix-item anomaly validation status
`ok`, with 370 ground-truth issue rows, AUROC 0.539, AUPRC 0.0289, and
Precision@10 0.0. Existing status docs report that grouped proxy-IRT validation
is also weak, and that issue-specific/subject-normalized/focused-null results
support at most limited review-queue hints.

Allowed claim: MMLU-Redux is a weak or negative external-validation stress test
for the current matrix-derived diagnostics.

Blocked claims:

- Generic MMLU error-detection success.
- MMLU-Redux validates the diagnostics.
- Redux alignment is direct-id or hash-confirmed.
- The narrow review-queue hints are generic detection-success evidence.

## 9. Synthetic Harness Status

Legacy synthetic AUCs remain demoted to wiring or sanity-check evidence. They
must not be used as independent diagnostic-validation evidence.

Current claim state from inspected docs:

- Legacy controlled synthetic harness: `DEMOTED_TO_WIRING_CHECK` /
  wiring-only.
- Decoupled synthetic validation: `RESULT_REQUIRED` until an approved run
  produces complete artifacts.
- Cross-flaw and held-out follow-up: existing artifacts and plans are not a
  substitute for a decoupled validation run.

This reconciliation did not execute prompt 07 and did not run synthetic
validation.

## 10. Claims Allowed Now

The following claims are allowed under this gate:

- ValidEval has an active public HELM MMLU wide panel with 39 models and 14,042
  items.
- The active wide matrix has 0 missing cells under the current panel-validity
  artifact.
- The current panel-validity gate passes for the active 39-model panel.
- The old 3-model panel/pilot exists as provenance and backup evidence, not as
  the active panel.
- Proxy IRT artifacts exist for the active 39-model panel.
- MMLU-Redux validation artifacts exist but support a weak/negative stress-test
  interpretation.
- Legacy synthetic AUCs are wiring/sanity-check artifacts only.
- Decoupled synthetic validation remains `RESULT_REQUIRED`.

## 11. Claims Blocked Now

The following claims remain blocked:

- Generic MMLU error-detection success.
- Global MMLU validity or invalidity.
- Treating the historical 3-model pilot as the current active MMLU panel.
- Treating synthetic validation as proof of diagnostic validity.
- `Legacy synthetic AUCs validate diagnostics.`
- `MMLU-Redux provides positive detection-success evidence.`
- `MMLU-Redux alignment is direct-id or hash-confirmed.`
- `Full IRT`, `full 2PL`, or `Rasch/1PL` was run on the active panel.
- Real-panel ranking sensitivity, ranking flips, or diagnostic disagreement
  exist as artifact-backed findings.
- Decoupled synthetic validation has been executed.
- A second benchmark has been run.
- The project is NeurIPS-ready.

## 12. Stale or Contradictory Docs

Canonical/current docs that align with the active 39-model state:

- `MMLU_WIDE_PANEL_ACQUISITION_REPORT.md`
- `MMLU_PANEL_VALIDITY_REPORT.md`
- `MMLU_EVIDENCE_GATE_REPORT.md`
- `MMLU_REDUX_WEAK_SIGNAL_DIAGNOSIS.md`
- `MMLU_REDUX_SUBJECT_NORMALIZED_VALIDATION_REPORT.md`
- `REAL_EMPIRICAL_SPINE_REFRAME.md`
- `CLAIMS_LEDGER_NEURIPS.md`
- `paper/claims.md`
- `paper/experiments.md`
- `paper/reframed_abstract_negative_result.md`
- `paper/reframed_intro_negative_result.md`

Docs that should be clarified or updated in a later approved prompt:

- `LIMITED_REAL_MMLU_PANEL_VALIDITY_REPORT.md`: accurate for the limited
  3-model, 310-item pilot, but should carry an explicit "historical pilot, not
  active panel" banner.
- `NEURIPS_SUBMISSION_GO_NO_GO.md`: used pre-reconciliation venue language; the
  panel-size evidence changed, even though submission readiness remains blocked
  by other missing artifacts.
- `REAL_MMLU_EVIDENCE_CREATION_REPORT.md`: contradictory-search output found
  stale language saying MMLU-Redux validation was blocked by a missing file,
  while current `results/mmlu/redux_validation/metrics.json` and later reports
  exist.
- Older no-run prompt-pack files and dry-run audits should remain historical,
  but downstream docs should identify the current active evidence source before
  citing any 3-model blocker.

No stale docs were edited in this pass because the user requested a stop after
creating this evidence reconciliation audit.

## 13. Venue Implication

The panel-size blocker for the MMLU empirical spine is cleared. That improves
the evidence base, but it does not make the project submission-ready by itself.

Still missing for a top venue or main submission:

- artifact-backed real-panel ranking/disagreement analysis,
- direct/hash-confirmed MMLU-Redux alignment or stronger external validation,
- decoupled synthetic validation if it is to be claimed,
- second-benchmark evidence,
- final figures/tables/paper compilation,
- reviewer packet rebuild and ZIP audit,
- final venue gate.

Current implication: the project can proceed to prompt 02 for claim/story sync,
but should not claim NeurIPS readiness from this reconciliation alone.

## 14. Required Fixes

Recommended next fixes, after user approval:

1. Run prompt 02 to sync claim/status docs against this audit.
2. Add historical/not-active banners to 3-model pilot reports.
3. Update `NEURIPS_SUBMISSION_GO_NO_GO.md` so it describes the reconciled state
   and preserves remaining blockers honestly.
4. Update or archive stale MMLU evidence-creation text that says Redux
   validation is still blocked by a missing file.
5. Keep real-panel ranking/disagreement, second-benchmark evidence, direct/hash
   alignment, and decoupled synthetic validation as `RESULT_REQUIRED` until the
   corresponding prompts are approved and artifacts exist.

## 15. Final Verdict

`39_MODEL_PANEL_PRESENT_BUT_DOCS_STALE`
