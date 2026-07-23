# ValidEval NeurIPS Fix Prompt Pack

Generated: 2026-06-12 07:47 UTC

This pack contains **20 Markdown prompt files** designed to address the external review and move ValidEval toward NeurIPS Evaluations & Datasets range.

Core strategy:

1. Freeze feature sprawl.
2. Stop spending credits on small Ollama GPQA loops.
3. Build/import wide response matrices from published per-instance predictions.
4. Validate diagnostics against external ground truth, especially MMLU-Redux.
5. Add cross-flaw and held-out synthetic validation.
6. Use real/wide-panel IRT only when panel validity passes.
7. Write the paper from evidence, not hype.

## Prompt index

| # | File | Purpose | Working time | CPU runtime | GPU runtime | When |
|---:|---|---|---:|---:|---:|---|
| 01 | [01_freeze_repo_git_repro_audit_trail.md](./01_freeze_repo_git_repro_audit_trail.md) | Fixes the reproducibility/audit-trail criticism and freezes feature sprawl. | 45–90 min | 1–3 min | Not required | Now |
| 02 | [02_scope_trim_claims_ledger_evidence_pivot.md](./02_scope_trim_claims_ledger_evidence_pivot.md) | Converts the brutal review into an evidence-first plan and prevents overclaiming. | 1–2 hr | <1 min | Not required | Now |
| 03 | [03_generic_wide_response_matrix_importer.md](./03_generic_wide_response_matrix_importer.md) | Builds the critical importer for published per-instance predictions, avoiding LLM generation. | 3–6 hr | 1–10 min fixtures; 10–60 min large local files | Not required | Build now; real import later |
| 04 | [04_leaderboard_helm_details_importers.md](./04_leaderboard_helm_details_importers.md) | Adds adapters for published prediction-detail files stored locally. | 4–8 hr | 10–90 min depending on local data size | Not required | Build now; real import later |
| 05 | [05_mmlu_redux_ground_truth_ingestion.md](./05_mmlu_redux_ground_truth_ingestion.md) | Creates external ground-truth ingestion for independently documented MMLU flaws. | 2–4 hr | 1–5 min fixtures; 5–20 min real files | Not required | Now/build-only |
| 06 | [06_export_flags_and_validate_against_ground_truth.md](./06_export_flags_and_validate_against_ground_truth.md) | Turns diagnostics into externally testable predictions with precision/recall/enrichment. | 4–8 hr | 5–30 min fixtures; 30–120 min large benchmark | Not required | Build now; real execution later |
| 07 | [07_cross_flaw_confusion_matrix_validation.md](./07_cross_flaw_confusion_matrix_validation.md) | Fixes synthetic-validation circularity by testing all detectors on all flaws. | 4–8 hr | 5–30 min synthetic small; 30–90 min larger configs | Not required | Now |
| 08 | [08_heldout_synthetic_generators.md](./08_heldout_synthetic_generators.md) | Adds independent generator families so detectors are not validated only on mirror-image flaws. | 4–10 hr | 10–60 min synthetic | Not required | After Prompt 07 |
| 09 | [09_real_irt_2pl_wide_matrix.md](./09_real_irt_2pl_wide_matrix.md) | Replaces proxy item-total discrimination with credible psychometrics once matrix is wide. | 6–14 hr | 30 min–4 hr depending on matrix | Optional; can speed PyTorch/py-irt | Build now; run on wide matrix later |
| 10 | [10_mmlu_redux_main_experiment_pipeline.md](./10_mmlu_redux_main_experiment_pipeline.md) | Creates the main paper experiment: ValidEval flags versus MMLU-Redux issues. | 8–16 hr build; 1–4 hr real run | 30 min–4 hr real run depending rows/models | Not required | Build now; execute after data |
| 11 | [11_gpqa_wide_panel_reanalysis_protocol.md](./11_gpqa_wide_panel_reanalysis_protocol.md) | Demotes small GPQA to protocol demo and prepares serious GPQA reanalysis. | 3–6 hr build; 30 min–3 hr run after data import | 30 min–3 hr if wide predictions available | Not required | Build now; execute only with wide data |
| 12 | [12_secondary_benchmark_gsm8k_or_truthfulqa_plan.md](./12_secondary_benchmark_gsm8k_or_truthfulqa_plan.md) | Plans one second case study without feature sprawl. | 2–4 hr plan; 4–12 hr if scaffold | 1–60 min local data | Not required | Plan now; execute after MMLU |
| 13 | [13_statistical_grounding_multiplicity_materiality_uncertainty.md](./13_statistical_grounding_multiplicity_materiality_uncertainty.md) | Hardens stats layer reviewers will attack. | 4–8 hr | 10–90 min depending bootstrap | Not required | Build now; run later |
| 14 | [14_panel_validity_and_failure_modes.md](./14_panel_validity_and_failure_modes.md) | Prevents repeating the GPQA chance-panel mistake. | 3–6 hr | 5–30 min | Not required | Now |
| 15 | [15_neurips_paper_draft_from_evidence_not_hype.md](./15_neurips_paper_draft_from_evidence_not_hype.md) | Starts the actual paper while marking missing results explicitly. | 4–10 hr scaffold; 20–40 hr human revision later | <1 min | Not required | Now |
| 16 | [16_related_work_positioning_and_citation_map.md](./16_related_work_positioning_and_citation_map.md) | Prevents attacks that ValidEval ignores prior benchmark/eval/psychometrics work. | 3–8 hr | <1 min | Not required | Now; human verify citations later |
| 17 | [17_external_review_packet_and_release_hardening.md](./17_external_review_packet_and_release_hardening.md) | Creates a clean review packet instead of dumping phase reports. | 2–5 hr | 1–10 min | Not required | After initial evidence scaffolds |
| 18 | [18_final_neurips_readiness_audit_gate.md](./18_final_neurips_readiness_audit_gate.md) | Final reviewer-style go/no-go before submission. | 3–6 hr | 5–30 min | Not required | After evidence experiments |
| 19 | [19_workshop_paper_first_strategy.md](./19_workshop_paper_first_strategy.md) | Creates lower-risk workshop plan around validation harness. | 2–5 hr | <1 min | Not required | Optional before main |
| 20 | [20_master_execution_order_and_time_budget.md](./20_master_execution_order_and_time_budget.md) | Builds the master schedule so you do not burn credits randomly. | 30–60 min | <1 min | Not required | Now |

## Recommended order

Immediate: 01, 02, 20.
Evidence infra: 03, 04, 05, 06.
Synthetic validation: 07, 08, 14, 13, 09.
Main experiments: 10, 11, 12.
Paper/review: 15, 16, 17, 19, 18.

## Most important prompts

If you only do five: 03, 06, 07, 10, 14.

## GPU note

The preferred NeurIPS path is mostly CPU-only because it imports published per-instance predictions instead of generating new outputs. GPU is optional only for IRT fitting or local LLM generation, which is not recommended now.
