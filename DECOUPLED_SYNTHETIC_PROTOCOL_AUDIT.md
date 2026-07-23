# Decoupled Synthetic Protocol Audit

## 1. Executive Summary

The decoupled synthetic harness is still a scaffold and dry-run preflight only. Static inspection shows that the new model API does not accept hidden flaw labels, `ObservableItemFeatures.public_metadata()` strips the hidden-label keys currently known to the protocol, and `FixedDiagnosticReadout.score_items` does not accept or branch on flaw family. The legacy controlled harness remains demoted to wiring/sanity-check status.

The protocol is ready to be preregistered for a future approved run, but not ready to support any diagnostic-validation claim today. Evidence state remains `RESULT_REQUIRED`.

## 2. Files Reviewed

- `src/valideval/validation/decoupled_synthetic.py`
- `src/valideval/validation/synthetic_benchmark.py`
- `src/valideval/validation/validation_runner.py`
- `src/valideval/validation/flaw_generators.py`
- `src/valideval/validation/heldout_generators.py`
- `tests/test_synthetic_harness_decoupling.py`
- `SYNTHETIC_HARNESS_CIRCULARITY_AUDIT.md`
- `DECOUPLED_SYNTHETIC_HARNESS_DESIGN.md`
- `SYNTHETIC_DEMOTION_AND_DECOUPLING_BUILD_AUDIT.md`
- `NO_RUN_RULES_AND_EVIDENCE_STATE_LOCK.md`
- `CLAIMS_LEDGER_NEURIPS.md`
- `paper/claims.md`
- `paper/diagnostic_validation.md`
- `paper/limitations.md`

## 3. Legacy Harness Status

The legacy harness is intentionally still present because existing tests and historical reports use it as a wiring surface. It remains labeled `legacy_wiring_only`. The circularity audit found direct coupling between injected labels, controlled model behavior, and flaw-aware score extraction. Its historical AUCs remain demoted to `DEMOTED_TO_WIRING_CHECK`.

## 4. New Decoupled Harness Status

The new scaffold defines:

- `ObservableItemFeatures`
- `FlawAgnosticSyntheticModelConfig`
- `FlawAgnosticSyntheticModel`
- `PanelOutput`
- `FixedDiagnosticReadout`
- `build_decoupled_synthetic_preflight`

The module is scaffold-only. It does not generate data, run models, compute AUC, compute metrics, or tune thresholds.

## 5. Hidden-Label Leakage Check

`ObservableItemFeatures` exposes only observable fields plus generic metadata. Hidden-label keys are stripped from `public_metadata()`, including `is_flawed`, `flaw_type`, `injected_flaw`, `ground_truth_flaw`, `synthetic_label`, and `oracle_flaw`.

The dry-run manifest now records `hidden_label_guard`. A passing guard means hidden-label fields are not dataclass fields and are stripped from public metadata before model use.

## 6. Flaw-Type Leakage Check

`FlawAgnosticSyntheticModel.predict` accepts only `self`, `item`, and `variant`. It has no `is_flawed`, `flaw_type`, `label`, `injected`, or `ground_truth_flaw` parameter. The preflight records `flaw_type_guard`.

## 7. Fixed-Readout Check

`FixedDiagnosticReadout.score_items` accepts only `self` and `panel_outputs`. It computes a fixed item-instability score from invalid-output rate and model correctness disagreement. It does not accept hidden labels or switch by flaw family. The preflight records `fixed_readout_guard`.

## 8. Generator / Model / Diagnostic Separation

The intended future separation is:

- generator stores hidden labels only for final evaluation,
- model receives observable item features only,
- readout scores outputs without target labels,
- evaluator compares fixed scores to labels after scoring,
- baselines and thresholds are frozen before execution.

This separation is specified and guarded at the scaffold/preflight layer, but not yet exercised by an approved evidence run.

## 9. Remaining Circularity Risks

- Future generator code could accidentally leak labels through public metadata or prompt text.
- Future diagnostic wrappers could reintroduce per-flaw readout selection.
- Future threshold selection could be tuned after target-label inspection.
- Future held-out generators could mirror detector behavior too closely.
- Legacy validation commands remain available and must not be cited as decoupled evidence.

## 10. Required Guards Before Execution

- Preflight must pass with `hidden_label_guard: pass`.
- Preflight must pass with `flaw_type_guard: pass`.
- Preflight must pass with `fixed_readout_guard: pass`.
- Fixture-level hidden-label stripping tests must pass.
- Baseline plan must be frozen.
- Thresholds must be preregistered or reported as `[RESULT REQUIRED: sensitivity analysis]`.
- Reviewer-facing audit must confirm no empirical state has been upgraded before execution.

## 11. Evidence-State Impact

This audit changes no empirical values and upgrades no evidence state.

| Surface | State |
|---|---|
| Legacy synthetic AUCs | `DEMOTED_TO_WIRING_CHECK` |
| Decoupled synthetic validation | `RESULT_REQUIRED` |
| Dry-run guard manifest | Build-only / no evidence impact |
| MMLU-Redux | Weak/negative external-validation stress test |
| Real-panel disagreement/ranking sensitivity | `RESULT_REQUIRED` |

## 12. Final Verdict

DECOUPLED_PROTOCOL_READY_FOR_PREREGISTERED_FUTURE_RUN
