# ValidEval Top-Tier Upgrade Pack V2

This pack is designed to move ValidEval from **workshop-ready** to a serious **TMLR/COLM/NeurIPS D&B candidate** by adding real, artifact-backed value instead of more scaffolding.

## Core strategy

The project already has:

- active 39-model HELM MMLU panel,
- panel validity pass,
- proxy IRT artifacts,
- subject-level ranking sensitivity,
- weak/negative MMLU-Redux stress test,
- compiled paper,
- reviewer packet,
- final gate currently `WORKSHOP_READY_ONLY`.

The next value jump requires:

1. multi-benchmark evidence,
2. stronger real-panel findings,
3. direct/hash or explicitly blocked external validation,
4. stronger psychometrics and uncertainty,
5. Kaggle-executable open-model panels,
6. artifact-backed figures/tables,
7. a paper story that is no longer “toolkit + audit prose,” but a real measurement-science result.

## Execution order

Run in order:

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

## Important

This pack is aggressive, but not reckless. It must not fake readiness.

Every prompt must report:

- what actually ran,
- what failed,
- what evidence changed,
- what claims are still blocked,
- whether the paper ceiling improved.

If a run is blocked, preserve the blocker and move to the next honest value path.
