# Decoupled Synthetic Preregistered Execution Manifest

## 1. Purpose

Define the future execution protocol for decoupled synthetic diagnostic validation without running it now. This manifest is a preregistration template only and does not create evidence.

## 2. Current Status

- Legacy synthetic AUCs: `DEMOTED_TO_WIRING_CHECK`
- Decoupled synthetic validation: `RESULT_REQUIRED`
- Current scaffold: dry-run/preflight only
- Current preflight purpose: API and leakage-guard inspection only
- Evidence-state impact: none

## 3. Frozen Inputs

Before any future run, freeze:

- generator versions and config hashes,
- item counts by flaw family,
- prompt variants,
- allowed public metadata keys,
- hidden-label schema,
- random seeds,
- train/validation/held-out generator split,
- output directories and manifest paths.

No inputs are frozen by this no-run pass.

## 4. Frozen Model Behavior

The future model must use `FlawAgnosticSyntheticModel.predict(item, variant="original")` or an equivalently guarded API. It must not accept `is_flawed`, `flaw_type`, `label`, `injected`, `ground_truth_flaw`, `synthetic_label`, or `oracle_flaw`.

Model behavior may depend on:

- prompt text,
- answer choices,
- answer when the future protocol explicitly permits answer-aware scoring,
- subject,
- public metadata after hidden-label stripping,
- declared prompt variant,
- frozen model configuration and seed.

## 5. Frozen Diagnostics

Diagnostics must be listed before execution. Each diagnostic must declare:

- input matrices or panel outputs,
- required prompt variants,
- expected output schema,
- whether it is diagnostic-specific or a shared readout,
- missing-data behavior.

No diagnostic may receive hidden target labels during scoring.

## 6. Frozen Readouts

The primary readout is a fixed item-level score produced before looking at flaw family labels. Any additional readout must be preregistered here before execution.

Readouts may not switch by:

- `flaw_type`,
- `is_flawed`,
- target flaw family,
- diagnostic/flaw pair,
- observed target-label performance.

## 7. Frozen Baselines

Future execution must include:

- random item ranking baseline,
- majority/difficulty baseline,
- prompt-length baseline,
- choice-length baseline,
- subject-only baseline,
- naive disagreement baseline,
- legacy wiring-only baseline as a negative control,
- ablation without hidden labels,
- held-out generator baseline.

## 8. Primary Metrics

Primary metrics for the future approved run:

- ROC AUC by preregistered target family,
- PR AUC by preregistered target family,
- Precision@k for frozen k values,
- clean/null false-positive rate,
- baseline-relative lift.

All metric values remain `[RESULT REQUIRED]`.

## 9. Secondary Metrics

Secondary metrics:

- score monotonicity over preregistered severity levels,
- calibration or reliability summary where valid outputs permit,
- held-out transfer drop,
- off-target activation rate,
- missing-output and invalid-output rates,
- sensitivity to threshold choice.

All values remain `[RESULT REQUIRED]`.

## 10. Thresholds and Sensitivity

Thresholds must be preregistered before execution or explicitly reported as `[RESULT REQUIRED: sensitivity analysis]`.

Default future reporting rule:

- do not tune thresholds after seeing labels,
- report fixed thresholds and sensitivity bands,
- report baseline comparisons for every thresholded claim,
- treat AUC alone as insufficient for practical materiality.

## 11. Held-Out Transfer Plan

Held-out generator transfer must use generator families not mirrored by detector-specific behavior. The same model API and fixed readout must be used for original and held-out families. Transfer claims require both successful intended-family performance and acceptable held-out transfer under preregistered gates.

## 12. Failure Criteria

Future execution fails the claim-upgrade gate if any of these occur:

- hidden-label guard is blocked,
- flaw-type guard is blocked,
- fixed-readout guard is blocked,
- model receives hidden labels,
- readout switches by flaw family,
- thresholds are tuned post hoc,
- baseline comparison is missing,
- held-out transfer result is missing,
- null/random baseline is missing,
- reviewer-facing audit is missing,
- any required artifact is malformed or absent.

## 13. Claim-Upgrade Criteria

Any future claim upgrade requires all of:

- non-circular guard pass,
- no hidden-label leakage,
- fixed readout,
- baseline comparison,
- held-out transfer result,
- null/random baseline,
- reviewer-facing audit,
- preregistered thresholds or sensitivity analysis,
- no unresolved blocker in the claim ledger.

Even after a future run, allowed language should remain protocol-scoped: "Evidence consistent with..." and "Under this diagnostic/protocol..."

## 14. Commands To Run Later

Do not run these commands in this no-run pass. They are placeholders for a separately approved evidence run.

```bash
python3 -m valideval decoupled-synthetic-preflight --dry-run
[RESULT REQUIRED: approved decoupled synthetic generation command]
[RESULT REQUIRED: approved flaw-agnostic model output command]
[RESULT REQUIRED: approved fixed-readout scoring command]
[RESULT REQUIRED: approved baseline comparison command]
[RESULT REQUIRED: approved held-out transfer command]
[RESULT REQUIRED: reviewer-facing audit command]
```

## 15. Commands Not To Run Yet

Do not run:

```bash
python3 -m valideval validate-diagnostics
python3 -m valideval validate-diagnostics-cross-flaw
python3 -m valideval validate-diagnostics-heldout
python3 -m valideval mmlu-redux-issue-validation
```

Do not run any synthetic generation, model inference, metric recomputation, AUC computation, threshold tuning, download, or real-panel analysis command under this manifest.

## 16. Evidence-State Rules

- Keep decoupled synthetic validation as `RESULT_REQUIRED` until an approved run produces complete artifacts.
- Keep legacy synthetic AUCs as `DEMOTED_TO_WIRING_CHECK`.
- Keep MMLU-Redux as weak/negative under the current protocol.
- Keep real-panel disagreement and ranking sensitivity as `RESULT_REQUIRED`.
- Do not replace `[RESULT REQUIRED]` placeholders with unrun values.
