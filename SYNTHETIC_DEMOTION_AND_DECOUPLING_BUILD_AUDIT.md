# Synthetic Demotion and Decoupling Build Audit

## 1. Executive Summary

This no-run build demotes the legacy controlled synthetic harness to wiring/sanity-check status, adds a decoupled synthetic scaffold, adds a dry-run CLI preflight, updates claim surfaces, and reframes the current empirical spine around the 39-model HELM MMLU panel plus the weak/negative MMLU-Redux external-validation result.

No validation experiment, synthetic generation, model inference, download, metric recomputation, threshold tuning, MMLU-Redux rerun, or real-panel analysis was run.

## 2. Circularity Finding

The legacy harness is circular by construction for scientific-evidence purposes. `flaw_generators.py` injects hidden target metadata such as `flaw_type`, `is_flawed`, and `ground_truth_signal`; `synthetic_benchmark.py` uses those labels in the controlled-output path; and `validation_runner.py` extracts item scores through a diagnostic/flaw-aware readout path. This can exercise wiring, but it cannot serve as independent diagnostic-validation evidence.

Primary audit artifact: `SYNTHETIC_HARNESS_CIRCULARITY_AUDIT.md`.

## 3. Claim Demotion

Current synthetic AUCs are retained only as historical wiring/sanity-check artifacts. The old status labels remain visible for traceability, but the claim state is demoted:

- legacy controlled synthetic flaw detection: `DEMOTED_TO_WIRING_CHECK`
- synthetic FPR/null controls: `DEMOTED_TO_WIRING_CHECK`
- cross-flaw and held-out artifacts: weak legacy context
- decoupled synthetic diagnostic validation: `RESULT_REQUIRED`

Updated surfaces include the main claims ledgers, paper claims, diagnostic-validation narrative, experiments, limitations, synthetic evidence table, readiness audit, and no-run evidence-state lock.

## 4. Decoupled Scaffold

Added `src/valideval/validation/decoupled_synthetic.py` with:

- `ObservableItemFeatures`
- `FlawAgnosticSyntheticModelConfig`
- `FlawAgnosticSyntheticModel`
- `PanelOutput`
- `FixedDiagnosticReadout`
- `build_decoupled_synthetic_preflight`

The model API has no `is_flawed` or `flaw_type` parameter. Hidden metadata keys are stripped before public metadata is used. The readout API accepts only panel outputs and does not switch by flaw family.

## 5. Dry-Run CLI

Added:

```bash
python3 -m valideval decoupled-synthetic-preflight --dry-run
```

The command writes a manifest only and reports:

- `generation_run: false`
- `model_inference_run: false`
- `auc_computed: false`
- `metrics_written: false`
- `claim_state: RESULT_REQUIRED`
- `legacy_harness_status: legacy_wiring_only`

Manifest written during verification: `results/preflight/decoupled_synthetic_preflight.json`.

## 6. Real Empirical Spine

Added `REAL_EMPIRICAL_SPINE_REFRAME.md` and draft paper sections:

- `paper/reframed_abstract_negative_result.md`
- `paper/reframed_intro_negative_result.md`

The reframed thesis centers the strongest non-circular evidence: a 39-model HELM MMLU public panel and a weak/negative MMLU-Redux external-validation stress test. It does not claim detection success.

## 7. Evidence States

| Evidence surface | State |
|---|---|
| Legacy synthetic AUCs | Historical wiring/sanity-check only |
| Independent synthetic diagnostic validation | `RESULT_REQUIRED` |
| Cross-flaw specificity | Weak legacy context |
| Held-out transfer | Weak legacy context |
| MMLU-Redux external validation | Weak/negative |
| HELM 39-model MMLU panel | Real substrate; downstream findings remain `RESULT_REQUIRED` |
| Decoupled synthetic harness | Scaffold/preflight only |

## 8. What Was Not Run

- No synthetic validation.
- No synthetic generation.
- No model inference.
- No downloads.
- No MMLU-Redux rerun.
- No real-panel analysis.
- No metric recomputation.
- No threshold tuning.
- No empirical values changed.
- No evidence state upgraded.

## 9. Verification

Commands run:

```bash
ruff format src/valideval/validation/decoupled_synthetic.py src/valideval/cli.py tests/test_synthetic_harness_decoupling.py
ruff check .
python3 -m pytest -q tests/test_synthetic_harness_decoupling.py
python3 -m pytest -q tests/test_real_panel_dryrun_commands.py
python3 -m pytest -q
python3 -m valideval decoupled-synthetic-preflight --dry-run
```

Final results:

- `ruff check .`: passed
- `tests/test_synthetic_harness_decoupling.py`: 7 passed
- `tests/test_real_panel_dryrun_commands.py`: 2 passed
- full test suite: 193 passed
- dry-run preflight: exited 0 and wrote manifest only

## 10. Remaining Blockers

- A decoupled flaw-agnostic synthetic validation run has not been performed.
- MMLU-Redux alignment remains structural rather than direct-id/hash confirmed.
- Real-panel diagnostic disagreement, ranking sensitivity, subject instability, and baseline comparisons remain `RESULT_REQUIRED`.
- Calibration remains blocked where confidence/logprob outputs are unavailable.
- No current artifact supports an MMLU detection-success claim.

## 11. Final Verdict

CIRCULAR_SYNTHETIC_EVIDENCE_DEMOTED_AND_DECOUPLED_SCAFFOLD_READY
