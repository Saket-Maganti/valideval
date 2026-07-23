# Synthetic Validation Narrative Audit

## 1. Executive Summary

The synthetic diagnostic-validation narrative is now demoted. A deeper circularity audit found that
the legacy controlled synthetic harness branches on injected flaw metadata and uses flaw-specific
readout. Current synthetic AUCs are therefore retained only as historical wiring/sanity-check
artifacts, not as independent diagnostic-validation evidence. Cross-flaw specificity and held-out
generator transfer artifacts remain useful evidence-gating context, but they are not diagnostic-
validation success evidence.

No new validation experiments, model inference, downloads, or synthetic generators were run.

## 2. Files Reviewed

- `validation_reports/diagnostic_validation_summary.md`
- `validation_reports/diagnostic_validation_summary.json`
- `results/neurips_small_runs/cross_flaw_confusion/summary.md`
- `results/neurips_small_runs/cross_flaw_confusion/cross_flaw_matrix.json`
- `results/neurips_small_runs/heldout_generators/summary.md`
- `results/neurips_small_runs/heldout_generators/heldout_transfer.json`
- `configs/validation/synthetic_default.yaml`
- `configs/validation/heldout_default.yaml`
- `configs/diagnostics/calibration.yaml`
- `configs/diagnostics/power.yaml`
- `results/toy_mcq/mock/calibration.json`
- `results/toy_mcq/mock/power.json`
- `paper/diagnostic_validation.md`
- `paper/experiments.md`
- `CLAIMS_LEDGER_NEURIPS.md`
- `paper/CLAIMS_LEDGER.md`
- `paper/claims.md`
- `paper/limitations.md`
- `SYNTHETIC_HARNESS_CIRCULARITY_AUDIT.md`
- `DECOUPLED_SYNTHETIC_HARNESS_DESIGN.md`

## 3. Local Artifacts Used

- Legacy controlled synthetic validation: `validation_reports/diagnostic_validation_summary.md` and
  `.json`, now demoted to wiring/sanity-check status.
- Cross-flaw specificity: `results/neurips_small_runs/cross_flaw_confusion/summary.md` and
  `cross_flaw_matrix.json`.
- Held-out generator transfer: `results/neurips_small_runs/heldout_generators/summary.md` and
  `heldout_transfer.json`.
- Calibration/power caveats: `results/toy_mcq/mock/calibration.json`,
  `results/toy_mcq/mock/power.json`, `configs/diagnostics/calibration.yaml`, and
  `configs/diagnostics/power.yaml`.

## 4. Paper Sections Updated

- `paper/diagnostic_validation.md`
- `paper/experiments.md`
- `paper/claims.md`
- `paper/CLAIMS_LEDGER.md`
- `paper/limitations.md`
- `CLAIMS_LEDGER_NEURIPS.md`
- `SYNTHETIC_EVIDENCE_STATUS_TABLE.md`
- `NO_RUN_RULES_AND_EVIDENCE_STATE_LOCK.md`

## 5. Claims Allowed

- ValidEval provides a legacy controlled synthetic wiring/sanity-check harness.
- Current synthetic AUCs are historical artifacts only and are not independent diagnostic-validation
  evidence.
- Clean/null behavior and FPR can be reported for the legacy synthetic harness only as sanity-check
  context.
- Cross-flaw and held-out artifacts exist and identify diagnostic-specificity and transfer risks.
- Materiality labels can qualify detector separability.
- The claims ledger blocks unsupported diagnostic claims.

## 6. Claims Blocked

- Universal diagnostic generalization.
- Current synthetic AUCs as independent diagnostic-validation evidence.
- Real-benchmark validity conclusions from synthetic evidence alone.
- Real benchmark error-detection claims.
- MMLU-Redux diagnostic-validation success claims.
- GPQA establishes real benchmark validity.
- Numeric calibration is available without confidence/logprob outputs.
- Synthetic-harness power analysis is complete.

## 7. Remaining [RESULT REQUIRED] Placeholders

- `[RESULT REQUIRED: synthetic-harness power analysis]`
- `[RESULT REQUIRED: decoupled flaw-agnostic synthetic diagnostic-validation harness]`
- `[RESULT REQUIRED: numeric calibration with confidence/logprob outputs]`
- `[RESULT REQUIRED: human-reviewed real-benchmark threshold calibration]`

## 8. Missing Positive Evidence

- Cross-flaw specificity is not uniformly clean: 7 strong off-target activations remain.
- Held-out transfer is not uniformly strong: only 3 of 6 families are paper-eligible.
- Calibration is blocked for numeric metrics by missing confidence/logprob outputs.
- Power evidence exists for the toy lane but not as a synthetic diagnostic-validation power result.
- Synthetic-to-real transfer remains unvalidated.

## 9. Recommended Next Experiment Run

The next best methodology block is an approved decoupled synthetic harness implementation whose
model behavior cannot branch on injected labels and whose readout is fixed before seeing flaw
family. Do not run this without explicit approval.
