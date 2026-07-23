# ValidEval No-Run Fix/Build Prompt Pack

This pack is for the current ValidEval situation after harsh review feedback and later HELM MMLU progress.

## Strategic diagnosis

The strongest paper is not “ValidEval detects benchmark errors.” The strongest paper is:

> Benchmark-validity diagnostics are themselves measurement instruments. They need validation for sensitivity, specificity, transfer, false-positive control, materiality, and claim authorization before they can support benchmark-validity claims.

## Current corrected state

- Earlier “mock-only” criticism is partly stale: a real 39-model HELM MMLU panel exists.
- MMLU-Redux remains weak/negative external validation; no detection-success claim is allowed.
- Cross-flaw specificity and held-out transfer remain weak/mixed.
- Confirmatory runs are deferred.
- The next build target is a real-panel finding engine, paper tightening, baselines, dry-run scaffolds, calibration/power infrastructure, and release slimming.

## Prompt order

| # | File | Purpose | Time |
|---:|---|---|---:|
| 00 | `00_global_no_run_rules.md` | Lock no-run rules and evidence states | 20–45 min |
| 01 | `01_paper_thesis_reframe.md` | Reframe paper around diagnostic validation | 1–3 hr |
| 02 | `02_surface_area_freeze.md` | Freeze/defer product sprawl | 1–3 hr |
| 03 | `03_real_panel_finding_engine.md` | Build dry-run real-panel finding engine | 3–8 hr |
| 04 | `04_baselines_ablations_scaffold.md` | Build baseline/ablation scaffolds | 3–6 hr |
| 05 | `05_figures_tables_templates.md` | Build result templates only | 2–5 hr |
| 06 | `06_ollama_panel_dryrun.md` | Wire local model panel dry-run path | 4–8 hr |
| 07 | `07_second_benchmark_scaffold.md` | Scaffold GSM8K/TruthfulQA no-run path | 4–8 hr |
| 08 | `08_calibration_logprob_infra.md` | Build calibration/logprob infrastructure | 4–8 hr |
| 09 | `09_power_materiality_scaffold.md` | Build power/materiality preflight | 3–6 hr |
| 10 | `10_mmlu_redux_alignment_upgrade.md` | Build direct/hash alignment preflight | 2–5 hr |
| 11 | `11_synthetic_confirmatory_consolidation.md` | Consolidate synthetic confirmatory no-run surface | 2–4 hr |
| 12 | `12_related_work_rewrite.md` | Write serious related work | 3–8 hr |
| 13 | `13_claims_ledger_sync.md` | Sync claims with evidence | 1–3 hr |
| 14 | `14_reviewer_packet_slimming.md` | Slim reviewer packet / repo hygiene | 2–5 hr |
| 15 | `15_final_no_run_readiness_audit.md` | Final no-run readiness audit | 1–3 hr |
| 16 | `16_later_run_plan.md` | Master later execution order | 1–2 hr |

## What this pack does not do

It does not execute any empirical run. It builds the safest path to run later.
