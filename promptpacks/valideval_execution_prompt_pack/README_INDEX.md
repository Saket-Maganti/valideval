# ValidEval Execution Prompt Pack — Fix Issues, Run Evidence, Build Kaggle Path

This pack moves ValidEval from no-run scaffolding into actual artifact-backed evidence.

It addresses the known issues:

- conflicting evidence state: 3-model pilot vs 39-model HELM MMLU panel,
- legacy synthetic harness circularity,
- missing or weak real-panel findings,
- MMLU-Redux weak/negative validation needing direct/hash-backed hardening,
- IRT / psychometric claims needing a wide panel and real run artifacts,
- lack of a second benchmark,
- missing Kaggle GPU notebook path if local compute is insufficient,
- missing final paper figures/tables/PDF and reviewer packet.

Run order:

1. `00_global_execution_rules.md`
2. `01_evidence_reconciliation_gate.md`
3. `02_claims_and_paper_story_sync.md`
4. `03_real_panel_helm_mmlu_core_runs.md`
5. `04_mmlu_redux_direct_alignment_and_validation.md`
6. `05_irt_and_psychometric_runs.md`
7. `06_real_panel_ranking_disagreement_and_baselines.md`
8. `07_decoupled_synthetic_execution_protocol.md`
9. `08_second_benchmark_selection_and_cpu_path.md`
10. `09_kaggle_gpu_notebook_builder.md`
11. `10_kaggle_results_import_and_validation.md`
12. `11_figures_tables_and_artifact_manifest.md`
13. `12_paper_rewrite_compile_and_appendix.md`
14. `13_reviewer_packet_rebuild_and_zip_audit.md`
15. `14_final_venue_gate_and_submission_strategy.md`

Core rule: run real analyses only after the relevant gate passes. If a run fails, document it; never fabricate or soften blockers.
