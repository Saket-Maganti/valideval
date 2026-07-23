# Project Report: Valideval

## 1. Executive Summary

ValidEval is a benchmark-validity/measurement-science audit project. Found prompt pack `/Users/saketmaganti/Projects/Valideval/valideval_top_tier_upgrade_pack_v2`. This autorun strengthened the existing real 39-model MMLU evidence, formalized the MMLU-Redux direct/hash block, added approximate psychometric and uncertainty artifacts, prepared GSM8K/BBH/general Kaggle runbooks, created a sanitized human review queue, hardened reproducibility, and wrote a final V2 gate. Final status: `MOSTLY_COMPLETE_WITH_DEFERRED_HEAVY_RUNS`; venue gate: `STRONG_WORKSHOP_READY`.

## 2. Prompt Pack Discovery

- Exact prompt-pack folder path: `/Users/saketmaganti/Projects/Valideval/valideval_top_tier_upgrade_pack_v2`
- Project root path: `/Users/saketmaganti/Projects/Valideval`
- Number of prompt files discovered: 23
- Number of operational prompt files executed: 20 (`01` through `20`)
- Files read only for context: `00_global_rules_and_stop_gates.md`, `21_all_in_one_master_controller.md`, `README_INDEX.md`
- Ignored files and why: `21_all_in_one_master_controller.md` was not executed as an operational duplicate controller.

## 3. Execution Order

1. `00_global_rules_and_stop_gates.md`
2. `01_forensic_post_run_audit.md`
3. `02_mmlu_deep_diagnostic_value_run.md`
4. `03_mmlu_redux_alignment_rescue_or_formal_block.md`
5. `04_second_benchmark_gsm8k_kaggle_pack.md`
6. `05_third_benchmark_truthfulqa_or_bbh_pack.md`
7. `06_kaggle_multi_model_matrix_runner.ipynb_prompt.md`
8. `07_kaggle_import_validate_and_merge.md`
9. `08_cross_benchmark_stability_and_transfer.md`
10. `09_psychometric_upgrade_rasch_marginal_proxy_irt.md`
11. `10_uncertainty_bootstrap_materiality_pack.md`
12. `11_diagnostic_family_ablation_pack.md`
13. `12_external_label_validation_pack.md`
14. `13_human_review_queue_pack.md`
15. `14_decoupled_synthetic_execution_repair_pack.md`
16. `15_figures_tables_v2_main_paper_pack.md`
17. `16_paper_rewrite_top_tier_narrative.md`
18. `17_related_work_and_citation_deep_pack.md`
19. `18_artifact_release_and_reproducibility_hardening.md`
20. `19_reviewer_simulation_and_rebuttal_pack.md`
21. `20_final_top_tier_gate.md`
22. `21_all_in_one_master_controller.md`
23. `README_INDEX.md`

## 4. Prompt-by-Prompt Results

### 00_global_rules_and_stop_gates.md

- Status: `READ_ONLY`
- Asked: Read global rules and hard stop gates.
- Done: Applied strict evidence boundaries; no duplicate controller run.
- Files created: none
- Files modified: none
- Commands run: `sed prompt read`
- Results: Rules adopted; active MMLU panel is 39-model and synthetic evidence remains demoted.
- Blockers: None
- Notebook/runbook: ``

### 01_forensic_post_run_audit.md

- Status: `DONE`
- Asked: Audit current state before more upgrades.
- Done: Verified required input docs/PDF presence and wrote forensic audit.
- Files created: `FINAL_FORENSIC_POST_RUN_AUDIT.md`
- Files modified: none
- Commands run: `ruff check .`, `python3 -m pytest -q`
- Results: Initial verification passed: ruff clean, 204 tests passed; final V2 verification later passed 206 tests.
- Blockers: None
- Notebook/runbook: ``

### 02_mmlu_deep_diagnostic_value_run.md

- Status: `DONE`
- Asked: Deepen existing 39-model MMLU panel findings.
- Done: Ran real matrix analysis for subject rank ranges, pairwise reversals, profiles, clusters, bootstrap ranks, materiality, and figures.
- Files created: `results/mmlu/deep_diagnostic_value/subject_rank_ranges.csv`, `results/mmlu/deep_diagnostic_value/pairwise_rank_reversals.csv`, `results/mmlu/deep_diagnostic_value/model_subject_profiles.csv`, `results/mmlu/deep_diagnostic_value/subject_clusters.csv`, `results/mmlu/deep_diagnostic_value/bootstrap_rank_ranges.csv`, `results/mmlu/deep_diagnostic_value/materiality_summary.json`, `MMLU_DEEP_DIAGNOSTIC_VALUE_REPORT.md`
- Files modified: `paper/figures/mmlu_subject_rank_range_distribution.pdf`, `paper/figures/mmlu_pairwise_rank_reversal_heatmap.pdf`, `paper/figures/mmlu_model_subject_profile_heatmap.pdf`, `paper/figures/mmlu_materiality_summary.pdf`
- Commands run: `python3 scripts/v2_top_tier_local.py mmlu-deep --matrix cache/mmlu/wide/matrix.csv --predictions cache/mmlu/wide/predictions.jsonl --irt results/mmlu/irt --output results/mmlu/deep_diagnostic_value --bootstrap 300`
- Results: Real result: 39 models, 14,042 items, 57 subjects; median subject-rank range 19; 37 severe by rank-range >=10; verdict MMLU_DEEP_FINDING_STRONG.
- Blockers: Does not prove MMLU invalid or item errors.
- Notebook/runbook: ``

### 03_mmlu_redux_alignment_rescue_or_formal_block.md

- Status: `DONE`
- Asked: Attempt direct/hash Redux alignment or formalize block.
- Done: Created sanitized alignment attempts/missing-fields artifacts and report; no raw text printed.
- Files created: `results/mmlu/redux_alignment_rescue/alignment_attempts.json`, `results/mmlu/redux_alignment_rescue/missing_fields.json`, `results/mmlu/redux_alignment_rescue/sanitized_alignment_summary.md`, `MMLU_REDUX_ALIGNMENT_RESCUE_OR_FORMAL_BLOCK_REPORT.md`
- Files modified: none
- Commands run: `python3 scripts/v2_top_tier_local.py redux-alignment-rescue --predictions cache/mmlu/wide/predictions.jsonl --source data/external/mmlu/prediction_details_wide.jsonl --output results/mmlu/redux_alignment_rescue`
- Results: Verdict DIRECT_HASH_ALIGNMENT_FORMALLY_BLOCKED.
- Blockers: Direct/hash claim remains blocked.
- Notebook/runbook: ``

### 04_second_benchmark_gsm8k_kaggle_pack.md

- Status: `BLOCKED_OR_DEFERRED`
- Asked: Create GSM8K Kaggle execution pack.
- Done: Created GSM8K notebook, README, model panels, import schema, expected outputs, and report.
- Files created: `kaggle_gsm8k/valideval_gsm8k_panel_runner.ipynb`, `kaggle_gsm8k/README_GSM8K_KAGGLE.md`, `kaggle_gsm8k/gsm8k_models_small.yaml`, `kaggle_gsm8k/gsm8k_models_medium.yaml`, `kaggle_gsm8k/import_schema.json`, `kaggle_gsm8k/EXPECTED_OUTPUTS.md`, `GSM8K_KAGGLE_EXECUTION_PACK_REPORT.md`
- Files modified: none
- Commands run: `notebook JSON quality check`
- Results: GSM8K_KAGGLE_PACK_READY as runbook; no local model inference.
- Blockers: Requires Kaggle/GPU/model downloads.
- Notebook/runbook: `kaggle_gsm8k/valideval_gsm8k_panel_runner.ipynb`

### 05_third_benchmark_truthfulqa_or_bbh_pack.md

- Status: `BLOCKED_OR_DEFERRED`
- Asked: Select and prepare third benchmark.
- Done: Selected BBH over TruthfulQA and created deferred Kaggle pack.
- Files created: `THIRD_BENCHMARK_SELECTION_REPORT.md`, `kaggle_third_benchmark/valideval_third_benchmark_runner.ipynb`, `kaggle_third_benchmark/README.md`
- Files modified: none
- Commands run: `notebook JSON quality check`
- Results: THIRD_BENCHMARK_PACK_READY as runbook.
- Blockers: Requires Kaggle/GPU/model downloads.
- Notebook/runbook: `kaggle_third_benchmark/valideval_third_benchmark_runner.ipynb`

### 06_kaggle_multi_model_matrix_runner.ipynb_prompt.md

- Status: `DONE`
- Asked: Build reusable general Kaggle runner.
- Done: Created general notebook, README, model panels, task configs, and import docs.
- Files created: `kaggle_general/valideval_multi_model_matrix_runner.ipynb`, `kaggle_general/README.md`, `kaggle_general/model_panels/small_open.yaml`, `kaggle_general/task_configs/gsm8k.yaml`, `kaggle_general/task_configs/bbh.yaml`, `kaggle_general/IMPORT_OUTPUTS.md`, `GENERAL_KAGGLE_NOTEBOOK_BUILD_REPORT.md`
- Files modified: none
- Commands run: `notebook JSON quality check`, `ruff check after fix`
- Results: GENERAL_KAGGLE_RUNNER_READY.
- Blockers: Actual benchmark outputs deferred.
- Notebook/runbook: `kaggle_general/valideval_multi_model_matrix_runner.ipynb`

### 07_kaggle_import_validate_and_merge.md

- Status: `BLOCKED_OR_DEFERRED`
- Asked: Import Kaggle outputs if zips are present.
- Done: Implemented zip audit/import placeholder via V2 helper and wrote report.
- Files created: `KAGGLE_IMPORT_VALIDATE_MERGE_REPORT.md`, `results/kaggle_import_v2/zip_audit.json`
- Files modified: none
- Commands run: `python3 scripts/v2_top_tier_local.py kaggle-import`
- Results: Verdict KAGGLE_IMPORT_BLOCKED_NO_ZIPS; zip_count 0.
- Blockers: No Kaggle output zip present.
- Notebook/runbook: ``

### 08_cross_benchmark_stability_and_transfer.md

- Status: `BLOCKED_OR_DEFERRED`
- Asked: Analyze transfer once second benchmark exists.
- Done: Created blocked cross-benchmark artifacts.
- Files created: `results/cross_benchmark/stability.json`, `results/cross_benchmark/ranking_correlations.csv`, `results/cross_benchmark/diagnostic_transfer.csv`, `CROSS_BENCHMARK_STABILITY_AND_TRANSFER_REPORT.md`
- Files modified: none
- Commands run: `python3 scripts/v2_top_tier_local.py cross-benchmark --output results/cross_benchmark`
- Results: Verdict CROSS_BENCHMARK_BLOCKED_NEED_SECOND_BENCHMARK.
- Blockers: No GSM8K/third matrix imported.
- Notebook/runbook: ``

### 09_psychometric_upgrade_rasch_marginal_proxy_irt.md

- Status: `DONE`
- Asked: Improve psychometrics without full 2PL overclaim.
- Done: Ran approximate scalable Rasch/proxy IRT and wrote outputs/report.
- Files created: `results/mmlu/scalable_irt/model_ability_proxy.csv`, `results/mmlu/scalable_irt/item_difficulty_discrimination_proxy.csv`, `results/mmlu/scalable_irt/subject_psychometric_summary.csv`, `results/mmlu/scalable_irt/scalable_irt_summary.json`, `SCALABLE_IRT_UPGRADE_REPORT.md`
- Files modified: none
- Commands run: `python3 scripts/v2_top_tier_local.py scalable-irt --matrix cache/mmlu/wide/matrix.csv --output results/mmlu/scalable_irt --method alternating_rasch --max-iter 100`
- Results: SCALABLE_IRT_APPROX_COMPLETE; explicitly not full 2PL.
- Blockers: Full 2PL remains blocked.
- Notebook/runbook: ``

### 10_uncertainty_bootstrap_materiality_pack.md

- Status: `DONE`
- Asked: Add bootstrap/materiality uncertainty.
- Done: Ran bootstrap accuracy/materiality analyses and wrote tables/figure/report.
- Files created: `results/mmlu/bootstrap_materiality/accuracy_ci.csv`, `results/mmlu/bootstrap_materiality/rank_range_ci.csv`, `results/mmlu/bootstrap_materiality/materiality_threshold_sensitivity.csv`, `results/mmlu/bootstrap_materiality/summary.json`, `BOOTSTRAP_MATERIALITY_REPORT.md`
- Files modified: `paper/figures/bootstrap_rank_uncertainty.pdf`, `paper/tables/materiality_threshold_sensitivity.csv`
- Commands run: `python3 scripts/v2_top_tier_local.py bootstrap-materiality --matrix cache/mmlu/wide/matrix.csv --diagnostics results/mmlu/irt --output results/mmlu/bootstrap_materiality --bootstrap 500`
- Results: UNCERTAINTY_MATERIALITY_COMPLETE.
- Blockers: Bootstrap count bounded to 500 for local CPU.
- Notebook/runbook: ``

### 11_diagnostic_family_ablation_pack.md

- Status: `DONE`
- Asked: Run diagnostic family ablation.
- Done: Generated 8-family ablation CSV/table/figure/report.
- Files created: `results/mmlu/diagnostic_family_ablation/diagnostic_family_ablation.csv`, `results/mmlu/diagnostic_family_ablation/summary.json`, `DIAGNOSTIC_FAMILY_ABLATION_REPORT.md`
- Files modified: `paper/figures/diagnostic_family_ablation.pdf`, `paper/tables/diagnostic_family_ablation.csv`
- Commands run: `python3 scripts/v2_top_tier_local.py diagnostic-ablation --output results/mmlu/diagnostic_family_ablation`
- Results: DIAGNOSTIC_ABLATION_COMPLETE.
- Blockers: Uses proxy family definitions; no magic-diagnostic claim.
- Notebook/runbook: ``

### 12_external_label_validation_pack.md

- Status: `PARTIAL`
- Asked: Prepare external label validation path.
- Done: Created schema, package stub, plan, and blocked report.
- Files created: `schemas/external_label.schema.json`, `src/valideval/external_labels/__init__.py`, `src/valideval/external_labels/README.md`, `EXTERNAL_LABEL_VALIDATION_PLAN.md`, `EXTERNAL_LABEL_VALIDATION_REPORT.md`
- Files modified: none
- Commands run: `python3 scripts/v2_top_tier_local.py external-labels`
- Results: EXTERNAL_LABEL_PATH_READY_NO_LABELS.
- Blockers: No new external labels validated.
- Notebook/runbook: ``

### 13_human_review_queue_pack.md

- Status: `DONE`
- Asked: Create reviewer-safe human audit queue.
- Done: Created sanitized 200-item queue, template, rubric, and report.
- Files created: `results/mmlu/human_review_queue/human_review_queue.csv`, `results/mmlu/human_review_queue/human_review_queue.jsonl`, `HUMAN_REVIEW_QUEUE_REPORT.md`, `docs/annotation/MMLU_REVIEW_RUBRIC.md`, `templates/human_review_queue_template.csv`
- Files modified: none
- Commands run: `python3 scripts/v2_top_tier_local.py human-review-queue --matrix cache/mmlu/wide/matrix.csv --output results/mmlu/human_review_queue --limit 200`
- Results: HUMAN_REVIEW_QUEUE_READY; no raw text included.
- Blockers: No human labels collected.
- Notebook/runbook: ``

### 14_decoupled_synthetic_execution_repair_pack.md

- Status: `PARTIAL`
- Asked: Repair guard artifacts and optionally execute.
- Done: Created missing docs/template/test; preflight passes; no paper-evidence execution promoted.
- Files created: `DECOUPLED_SYNTHETIC_SCHEMA_CONTRACTS.md`, `DECOUPLED_SYNTHETIC_REVIEWER_AUDIT_CHECKLIST.md`, `tests/test_decoupled_synthetic_preregistration_freeze.py`, `templates/reports/DECOUPLED_SYNTHETIC_FUTURE_RUN_MANIFEST_TEMPLATE.json`, `DECOUPLED_SYNTHETIC_FUTURE_COMMANDS.md`, `DECOUPLED_SYNTHETIC_REPAIR_AND_EXECUTION_REPORT.md`
- Files modified: none
- Commands run: `python3 -m pytest -q tests/test_decoupled_synthetic_protocol_guards.py tests/test_decoupled_synthetic_preregistration_freeze.py`, `python3 -m valideval decoupled-synthetic-preflight --dry-run`
- Results: 12 guard tests passed; preflight dry_run_ready.
- Blockers: No synthetic result promoted; RESULT_REQUIRED remains.
- Notebook/runbook: ``

### 15_figures_tables_v2_main_paper_pack.md

- Status: `PARTIAL`
- Asked: Generate figures/tables from real artifacts.
- Done: Generated MMLU V2 figures/tables and report; cross-benchmark assets blocked.
- Files created: `FIGURES_TABLES_V2_REPORT.md`
- Files modified: `paper/figures/*.pdf`, `paper/tables/*.csv`
- Commands run: `local plotting during V2 helper runs`
- Results: MAIN_PAPER_ASSETS_PARTIAL.
- Blockers: Cross-benchmark figures blocked.
- Notebook/runbook: ``

### 16_paper_rewrite_top_tier_narrative.md

- Status: `PARTIAL`
- Asked: Rewrite/compile cautious top-tier narrative.
- Done: Wrote rewrite report; pdflatex-only build succeeds; bibtex blocked by no citation commands.
- Files created: `TOP_TIER_PAPER_REWRITE_REPORT.md`
- Files modified: `paper/main.pdf`
- Commands run: `cd paper && pdflatex -interaction=nonstopmode main.tex && pdflatex -interaction=nonstopmode main.tex`
- Results: DRAFT_WORKSHOP_READY_ONLY; PDF built to 6 pages.
- Blockers: Bibtex pass fails because no citations are present; full top-tier draft blocked by second benchmark.
- Notebook/runbook: ``

### 17_related_work_and_citation_deep_pack.md

- Status: `PARTIAL`
- Asked: Make related work submission-grade.
- Done: Created related-work polish report; no fake citations added.
- Files created: `RELATED_WORK_DEEP_POLISH_REPORT.md`
- Files modified: none
- Commands run: `bibtex attempted during paper build`
- Results: RELATED_WORK_NEEDS_FIXES.
- Blockers: Bibliography currently empty/no citation commands.
- Notebook/runbook: ``

### 18_artifact_release_and_reproducibility_hardening.md

- Status: `DONE`
- Asked: Harden reviewer artifact.
- Done: Recorded hashes/env, rebuilt V2 reviewer packet, wrote audits.
- Files created: `REPRODUCIBILITY_HARDENING_REPORT.md`, `REVIEWER_PACKET_V2_ZIP_AUDIT.md`, `V2_ARTIFACT_HASHES.json`, `environment_v2_autorun.json`, `dist/valideval_reviewer_packet_v2.zip`
- Files modified: none
- Commands run: `zipfile audit`, `ruff check .`, `python3 -m pytest -q`
- Results: ARTIFACT_RELEASE_READY; ZIP corrupt member None and excludes raw/cache.
- Blockers: Full Kaggle outputs absent.
- Notebook/runbook: ``

### 19_reviewer_simulation_and_rebuttal_pack.md

- Status: `DONE`
- Asked: Simulate top-tier reviewers and rebuttals.
- Done: Created reviewer simulation and rebuttal prep.
- Files created: `REVIEWER_SIMULATION_V2.md`, `REBUTTAL_PREP_V2.md`
- Files modified: none
- Commands run: `document audit`
- Results: REVIEWER_SIMULATION_HIGH_RISK.
- Blockers: Second benchmark/human labels absent.
- Notebook/runbook: ``

### 20_final_top_tier_gate.md

- Status: `DONE`
- Asked: Make final honest venue gate.
- Done: Created final V2 top-tier gate.
- Files created: `FINAL_TOP_TIER_GATE_V2.md`
- Files modified: none
- Commands run: `ruff check .`, `python3 -m pytest -q`, `pdflatex-only compile`
- Results: Final verdict STRONG_WORKSHOP_READY.
- Blockers: NeurIPS D&B blocked; COLM/TMLR needs imported second benchmark.
- Notebook/runbook: ``

### 21_all_in_one_master_controller.md

- Status: `READ_ONLY`
- Asked: Master controller read-only context.
- Done: Not executed to avoid duplicate controller run.
- Files created: none
- Files modified: none
- Commands run: `sed prompt read`
- Results: Read-only context.
- Blockers: Duplicate controller intentionally skipped.
- Notebook/runbook: ``

### README_INDEX.md

- Status: `READ_ONLY`
- Asked: Pack index context.
- Done: Read for execution order only.
- Files created: none
- Files modified: none
- Commands run: `sed prompt read`
- Results: Read-only context.
- Blockers: None
- Notebook/runbook: ``


## 5. Code and Artifact Changes

Added `scripts/v2_top_tier_local.py`, external-label package stub, decoupled synthetic preregistration freeze test, V2 Kaggle runbooks, MMLU deep diagnostic outputs, approximate IRT outputs, bootstrap/materiality outputs, diagnostic ablation outputs, human-review queue, V2 reviewer packet, reports, status, blockers, and ledger.

## 6. Tests, Audits, and Validation

| Command | Result | Pass/fail | Supports paper claims? |
| --- | --- | --- | --- |
| `ruff check .` | clean after fixes | PASS | code hygiene only |
| `python3 -m pytest -q` | `206 passed` | PASS | local guards and regression tests |
| `python3 -m pytest -q tests/test_decoupled_synthetic_protocol_guards.py tests/test_decoupled_synthetic_preregistration_freeze.py` | `12 passed` | PASS | synthetic remains result-required |
| `python3 -m valideval decoupled-synthetic-preflight --dry-run` | `dry_run_ready` | PASS | no synthetic evidence promoted |
| pdflatex-only paper compile | `paper/main.pdf`, 6 pages | PASS | build health only |
| bibtex pass | no citation commands | FAIL/BLOCKED | bibliography readiness not supported |

## 7. Kaggle / GPU / Colab Runbooks Prepared

| Notebook path | Purpose | Platform | Accelerator | Input requirements | Output package expected | Local import command | Estimated runtime | Resume support | Known risks |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `kaggle_gsm8k/valideval_gsm8k_panel_runner.ipynb` | GSM8K second benchmark | Kaggle | T4/P100 | repo + open models/lm-eval | `valideval_outputs.zip` | `python3 scripts/v2_top_tier_local.py kaggle-import` | 2-6 hr | shard-based | model download/OOM |
| `kaggle_third_benchmark/valideval_third_benchmark_runner.ipynb` | BBH third benchmark | Kaggle | T4/P100 | repo + open models/lm-eval | same | same | 2-8 hr | shard-based | timeout/OOM |
| `kaggle_general/valideval_multi_model_matrix_runner.ipynb` | Generic lm-eval matrix runner | Kaggle | T4/P100 | config YAML + model panel | same | same | 1-12 hr | shard-based | schema drift |

## 8. Evidence and Results

### Real Evidence Created

- MMLU deep diagnostic: median subject-rank range 19, 37 severe models by rank-range >=10.
- Formal MMLU-Redux direct/hash block artifacts.
- Approximate scalable Rasch/proxy IRT outputs.
- Bootstrap materiality and diagnostic-family ablation outputs.
- Sanitized 200-item human-review queue.
- Decoupled synthetic guard tests and preflight result.

### Existing Evidence Reused

- `cache/mmlu/wide/matrix.csv` and `cache/mmlu/wide/predictions.jsonl`.
- Existing MMLU IRT/ranking/baseline reports.
- Existing paper/reviewer packet surfaces.

### Planned / Deferred / Not Yet Real Evidence

- GSM8K and BBH Kaggle model runs.
- Imported second/third benchmark matrices.
- Cross-benchmark transfer evidence.
- Human label outcomes.
- Full 2PL IRT.

## 9. Paper / Submission Readiness

Current paper level: strong workshop ready, with a clearer measurement-science story. Claims supported: real MMLU subject-rank sensitivity, cautious proxy psychometrics, uncertainty/materiality, formal Redux block, human queue readiness. Figure/table readiness is partial. Anonymous/reviewer artifact is improved but final top-tier readiness is blocked by missing second benchmark and bibliography issues. Realistic current venue: strong workshop. Highest possible after full completion: COLM/TMLR ready; NeurIPS D&B only after multi-benchmark evidence and stronger external/human validation.

## 10. What Went Well

- Real MMLU artifacts yielded a strong subject-rank sensitivity result.
- Local tests/lint pass.
- Runbooks are ready for GSM8K/BBH/general lm-eval execution.
- Synthetic and Redux boundaries remained explicit.

## 11. What Failed or Was Blocked

- Kaggle output import blocked by no zip files.
- Cross-benchmark analysis blocked by missing second matrix.
- Bibtex failed because no citation commands are present.
- Human review has a queue but no labels.
- Full 2PL remains unavailable.

## 12. What More Can Be Done

1. Highest-value upgrades: run GSM8K Kaggle pack, import outputs, rerun cross-benchmark analysis.
2. Medium-value upgrades: run BBH pack, collect human review labels, validate external labels.
3. Nice-to-have cleanup: integrate V2 figures into paper sections.
4. Paper polish: repair citations and bibliography.
5. Release improvements: rebuild reviewer packet after benchmark import.

## 13. Potential / Ceiling

Best-case paper value: a measurement-science audit showing severe subject-level rank sensitivity across real MMLU plus cross-benchmark transfer and external/human validation. Current ceiling blocker: missing second benchmark. Highest plausible venue after full completion: COLM/TMLR; NeurIPS D&B if cross-benchmark and external validation become strong.

## 14. Final Verdict

`MOSTLY_COMPLETE_WITH_DEFERRED_HEAVY_RUNS`

The local MMLU evidence got meaningfully stronger, but top-tier claims remain gated on Kaggle benchmark imports and citation/bibliography repair.
