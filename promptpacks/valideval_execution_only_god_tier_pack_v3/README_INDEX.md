# ValidEval Execution-Only God-Tier Pack V3

This pack is designed for the phase after the V2 upgrade autorun. It is not a scaffold pack. It is an execution pack whose purpose is to produce the missing evidence that blocks ValidEval from moving beyond `STRONG_WORKSHOP_READY`.

## Starting point

The latest project report says V2 ended at:

- `MOSTLY_COMPLETE_WITH_DEFERRED_HEAVY_RUNS`
- final venue gate: `STRONG_WORKSHOP_READY`
- strong MMLU evidence:
  - 39-model HELM MMLU panel
  - 14,042 items
  - panel validity pass
  - median subject-rank range 19
  - 37 models severe by rank-range >= 10
  - scalable approximate IRT complete
  - bootstrap/materiality complete
  - diagnostic-family ablation complete
  - sanitized human-review queue ready
- top-tier blockers:
  - no GSM8K / second-benchmark matrix
  - no cross-benchmark evidence
  - no third-benchmark matrix
  - no human labels
  - no strong external-label validation
  - full 2PL unavailable
  - bibliography/citation pass still broken

## V3 mission

Shift from strong workshop to serious COLM/TMLR/NeurIPS D&B candidacy by executing:

1. real GSM8K Kaggle/Colab run,
2. local GSM8K import + validation,
3. GSM8K diagnostics,
4. MMLU-GSM8K cross-benchmark analysis,
5. optional BBH/TruthfulQA third benchmark,
6. human-label collection/import if labels are available,
7. final paper and artifact gate.

## Execution order

1. `00_execution_only_rules.md`
2. `01_v3_state_lock.md`
3. `02_run_gsm8k_on_kaggle_or_colab.md`
4. `03_import_gsm8k_outputs.md`
5. `04_run_gsm8k_diagnostics.md`
6. `05_cross_benchmark_mmlu_gsm8k.md`
7. `06_run_third_benchmark_bbh_or_truthfulqa.md`
8. `07_import_third_benchmark_outputs.md`
9. `08_three_benchmark_transfer.md`
10. `09_human_label_collection.md`
11. `10_human_label_import.md`
12. `11_external_label_validation.md`
13. `12_psychometric_uncertainty_rerun_all_benchmarks.md`
14. `13_result_consistency_ablation_rerun.md`
15. `14_final_results_tables_and_figures.md`
16. `15_bibliography_and_citation_repair.md`
17. `16_top_tier_paper_rewrite.md`
18. `17_reviewer_packet_v3_freeze.md`
19. `18_reviewer_simulation_v3.md`
20. `19_final_god_tier_gate.md`
21. `20_master_controller_execute_with_gates.md`

## Minimum real win

GSM8K must be actually run/imported. Without that, V3 cannot honestly move above strong workshop.
