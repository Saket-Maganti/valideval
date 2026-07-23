# Decoupled Synthetic Protocol Build Audit

## 1. Executive Summary

This no-run build audited and hardened the decoupled synthetic harness protocol. It added explicit dry-run guard fields, fixture-level hidden-label stripping checks, a protocol audit, a preregistered future execution manifest, and a baseline plan. No validation, generation, inference, metric computation, threshold tuning, download, or evidence-state upgrade was performed.

## 2. What Was Audited

- `src/valideval/validation/decoupled_synthetic.py`
- `src/valideval/validation/synthetic_benchmark.py`
- `src/valideval/validation/validation_runner.py`
- `src/valideval/validation/flaw_generators.py`
- `src/valideval/validation/heldout_generators.py`
- `tests/test_synthetic_harness_decoupling.py`
- `SYNTHETIC_HARNESS_CIRCULARITY_AUDIT.md`
- `DECOUPLED_SYNTHETIC_HARNESS_DESIGN.md`
- `SYNTHETIC_DEMOTION_AND_DECOUPLING_BUILD_AUDIT.md`
- claims and paper/reviewer surfaces

## 3. What Was Hardened

The decoupled preflight now records:

- `status: dry_run_only`
- `preflight_status: dry_run_ready`
- `hidden_label_guard: pass`
- `flaw_type_guard: pass`
- `fixed_readout_guard: pass`
- `evidence_state_impact: none`
- `generation_run: false`
- `model_inference_run: false`
- `auc_computed: false`
- `metrics_written: false`

The forbidden hidden metadata list now includes `injected_flaw`, `ground_truth_flaw`, `synthetic_label`, and `oracle_flaw` in addition to the earlier legacy label keys.

## 4. Guard Tests

Added `tests/test_decoupled_synthetic_protocol_guards.py`. It checks:

- model API excludes hidden and label-like parameters,
- observable item fields do not expose hidden flaw fields,
- fixed readout branches do not use flaw-family names,
- dry-run manifest records no-run and guard statuses,
- paper/claim files do not promote legacy synthetic results.

Existing decoupling tests were updated for the hardened manifest schema.

## 5. Fixture-Level Hidden-Label Checks

Added fixtures:

- `tests/fixtures/decoupled_synthetic/observable_item_clean.json`
- `tests/fixtures/decoupled_synthetic/observable_item_with_hidden_labels.json`

Fixture tests verify that clean observable items load, top-level hidden fields are rejected by the dataclass constructor, metadata hidden fields are stripped before prediction, hidden metadata does not change model prediction, and hidden fields cannot reach fixed readout inputs.

## 6. Preregistered Manifest

Added `DECOUPLED_SYNTHETIC_PREREGISTERED_EXECUTION_MANIFEST.md`. It freezes future-run requirements, including model behavior, diagnostics, readouts, baselines, primary/secondary metrics, threshold rules, held-out transfer, failure criteria, claim-upgrade criteria, and commands not to run yet.

All future values remain `[RESULT REQUIRED]`.

## 7. Baseline Plan

Added `DECOUPLED_SYNTHETIC_BASELINES_PLAN.md` with:

- random diagnostic baseline,
- majority/difficulty baseline,
- prompt-length baseline,
- choice-length baseline,
- subject-only baseline,
- naive disagreement baseline,
- legacy wiring-only negative control,
- ablation without hidden labels,
- held-out generator baseline.

No baseline was computed.

## 8. Dry-Run Manifest

Verified:

```bash
python3 -m valideval decoupled-synthetic-preflight --dry-run
```

The command wrote `results/preflight/decoupled_synthetic_preflight.json` and did not generate items, run models, compute AUC, compute metrics, tune thresholds, or upgrade evidence.

## 9. Evidence States

| Evidence surface | State |
|---|---|
| Legacy synthetic AUCs | `DEMOTED_TO_WIRING_CHECK` |
| Decoupled synthetic validation | `RESULT_REQUIRED` |
| Decoupled preflight guard fields | Build-only / dry-run-only |
| MMLU-Redux | Weak/negative external-validation stress test |
| Real-panel disagreement/ranking sensitivity | `RESULT_REQUIRED` |

## 10. What Was Not Run

- No synthetic generation.
- No synthetic validation.
- No model inference.
- No diagnostic scoring over generated data.
- No AUC computation.
- No metric recomputation.
- No threshold tuning.
- No held-out/cross-flaw execution.
- No MMLU-Redux rerun.
- No downloads.
- No empirical value changes.
- No evidence-state upgrades.

## 11. Verification

Commands run:

```bash
ruff check .
python3 -m pytest -q tests/test_synthetic_harness_decoupling.py
python3 -m pytest -q tests/test_decoupled_synthetic_protocol_guards.py
python3 -m pytest -q tests/test_real_panel_dryrun_commands.py
python3 -m valideval decoupled-synthetic-preflight --dry-run
python3 -m pytest -q
```

Final results:

- `ruff check .`: passed
- `tests/test_synthetic_harness_decoupling.py`: 7 passed
- `tests/test_decoupled_synthetic_protocol_guards.py`: 10 passed
- `tests/test_real_panel_dryrun_commands.py`: 2 passed
- `decoupled-synthetic-preflight --dry-run`: exited 0 and wrote manifest only
- full suite: 203 passed

## 12. Remaining Blockers

- Decoupled synthetic validation has not been executed.
- Future generator code must still prove no prompt/public-metadata hidden-label leakage.
- Future baselines and held-out transfer remain `[RESULT REQUIRED]`.
- Threshold sensitivity remains `[RESULT REQUIRED: sensitivity analysis]`.
- MMLU-Redux remains weak/negative under the current protocol.
- Real-panel disagreement and ranking sensitivity remain `RESULT_REQUIRED`.

## 13. Final Verdict

DECOUPLED_SYNTHETIC_PROTOCOL_READY_NO_RUN
