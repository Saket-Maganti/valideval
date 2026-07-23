# Synthetic Evidence Status Table

| Evidence block | Status | Existing artifact | Main metric | Claim allowed | Claim blocked |
|---|---|---|---|---|---|
| Legacy controlled synthetic flaw detection | DEMOTED_TO_WIRING_CHECK | `validation_reports/diagnostic_validation_summary.md`; `SYNTHETIC_HARNESS_CIRCULARITY_AUDIT.md` | Historical 12-experiment summary; current synthetic AUCs are retained but demoted | Legacy harness can be used as a wiring/sanity-check surface | Treating current synthetic AUCs as independent diagnostic-validation evidence |
| Cross-flaw specificity | WEAK / LEGACY_CONTEXT | `results/neurips_small_runs/cross_flaw_confusion/cross_flaw_matrix.json` | 64 pairings; 7 strong off-target activations using AUC >= 0.8 | Cross-flaw artifacts identify specificity risks and motivate future decoupled tests | Diagnostics fire only on intended threat families |
| Held-out generator transfer | WEAK / LEGACY_CONTEXT | `results/neurips_small_runs/heldout_generators/heldout_transfer.json` | 6 families; 3 paper-eligible; transfer drops up to 0.48958333333333337 | Held-out artifacts identify transfer risks and motivate future decoupled tests | Universal held-out generator transfer |
| False-positive / null control | DEMOTED_TO_WIRING_CHECK | `validation_reports/diagnostic_validation_summary.md` | Clean FPR reported for 12 experiments; historical credible rows range from 0.0 to 0.06628787878787878 | Synthetic clean/null behavior can be reported as legacy sanity-check behavior only | Real-benchmark FPR is controlled |
| Materiality thresholding | WEAK / LEGACY_CONTEXT | `validation_reports/diagnostic_validation_summary.json` | 4 rows marked `practically material`; 1 row marked `negligible`; others statistically detectable | Materiality labels can qualify legacy detector separability reports | AUC alone establishes practical importance |
| Power analysis | WEAK | `results/toy_mcq/mock/power.json` | Toy MDD 0.25433934108924844; do-not-overinterpret band 25.433934108924845 points | Toy power output exists as a planning aid | Synthetic-harness power is complete |
| Calibration | BLOCKED | `results/toy_mcq/mock/calibration.json` | `calibration_status`: `requires_confidence_outputs`; ECE/Brier/NLL are null | Calibration surface correctly blocks numeric claims without confidence outputs | Numeric calibration has been established |
| Diagnostic family confusion matrix | WEAK | `results/neurips_small_runs/cross_flaw_confusion/cross_flaw_matrix.json` | 8x8 matrix; 7 strong off-target activations | The matrix can be used to flag diagnostic-specificity limitations | Universal diagnostic specificity |
| Synthetic-to-real caveat | NOT_RUN | `validation_reports/diagnostic_validation_summary.md` | Report states synthetic validation is not real benchmark evidence | Current synthetic AUCs are not treated as independent evidence | Real-benchmark validity conclusions from synthetic evidence alone |
| Decoupled synthetic diagnostic validation | RESULT_REQUIRED | `DECOUPLED_SYNTHETIC_HARNESS_DESIGN.md`; `src/valideval/validation/decoupled_synthetic.py` | Scaffold only; no AUC computed; no metrics written | Future approved dry-run and execution plan can be inspected | Claiming decoupled validation has run |
| Cross-flaw / held-out follow-up plan | RESULT_REQUIRED | `PREREGISTERED_CROSS_FLAW_HELDOUT_INVESTIGATION_PLAN.md`; `CONFIRMATORY_RUN_COMMAND_MANIFEST.md`; `RUNBOOK_CONFIRMATORY_SYNTHETIC_VALIDATION.md`; `BUILD_ONLY_POLISH_AUDIT.md` | No-run plan and build-only readiness artifacts; no confirmatory artifacts yet | The investigation is preregistered, execution is intentionally deferred, and the future runbook/manifest/preflight surface is ready | Treating the no-run plan, templates, preflight checker, or command manifest as empirical evidence |

## Build-Only Confirmatory Readiness Note

Confirmatory synthetic cross-flaw and held-out validation is preregistered but not executed. The
Phase 43A build-only surface adds a command manifest, runbook, report templates, audit report, and
static preflight checker for a later approved run. No validation command has been run in this phase,
no metrics have been recomputed, no thresholds have been tuned, and no evidence state has been
upgraded. After the circularity audit, current synthetic AUCs are demoted to wiring/sanity-check
artifacts pending a decoupled, flaw-agnostic harness with fixed readout.
