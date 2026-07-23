# Build-Only Polish Audit

## 1. Executive Summary

Phase 43A is a build-only polish pass around the future confirmatory synthetic cross-flaw and
held-out validation run. It creates reviewer-safe execution scaffolding without running
experiments, generating synthetic data, invoking model inference, downloading artifacts,
recomputing metrics, tuning thresholds, changing empirical values, or upgrading evidence states.

The preregistered plan remains the controlling artifact, and `PREREGISTRATION_REVIEW_AUDIT.md`
continues to define readiness as `YES_READY` for a later approved execution phase only.

## 2. What Was Built

- Future-command manifest: `CONFIRMATORY_RUN_COMMAND_MANIFEST.md`
- Reviewer-safe runbook: `RUNBOOK_CONFIRMATORY_SYNTHETIC_VALIDATION.md`
- Static no-run preflight checker: `scripts/preflight_confirmatory_synthetic.py`
- Focused preflight tests: `tests/test_preflight_confirmatory_synthetic.py`
- Future report templates under `templates/reports/`
- Public docs and claims-ledger notes that confirm execution is intentionally deferred

## 3. What Was Not Run

- No confirmatory cross-flaw validation.
- No confirmatory held-out validation.
- No validation command of any kind.
- No synthetic generation.
- No model inference.
- No downloads.
- No metric recomputation.
- No threshold tuning.
- No evidence-state upgrade.

## 4. Evidence States After This Phase

- Controlled synthetic flaw detection: unchanged, `SUPPORTED` only for already documented
  generator-scoped sensitivity.
- Cross-flaw specificity: unchanged, `WEAK`.
- Held-out generator transfer: unchanged, `WEAK`.
- Materiality thresholding: unchanged, `WEAK`.
- Numeric calibration: unchanged, `BLOCKED`.
- Synthetic-to-real threshold validation: unchanged, `NOT_RUN`.
- Confirmatory cross-flaw / held-out follow-up: unchanged, `RESULT_REQUIRED`.
- MMLU-Redux: unchanged, weak/negative external validation.
- GPQA: unchanged, protocol/demo unless wide-panel evidence exists.

## 5. Confirmatory Run Readiness

The future run surface is build-ready:

- Frozen configs are named.
- Expected inputs and outputs are documented.
- Runtime estimate is documented as operational planning only.
- Failure handling preserves missing, malformed, and failed gates.
- Templates preserve `[RESULT REQUIRED]` markers.
- The preflight checker can be run before future execution to verify static readiness.

## 6. Remaining Placeholders

- `[RESULT REQUIRED: confirmatory cross-flaw metrics]`
- `[RESULT REQUIRED: confirmatory held-out transfer metrics]`
- `[RESULT REQUIRED: synthetic confirmatory claim-status report]`
- `[RESULT REQUIRED: synthetic-harness power analysis]`
- `[RESULT REQUIRED: numeric calibration with confidence/logprob outputs]`
- `[RESULT REQUIRED: human-reviewed real-benchmark threshold calibration]`

## 7. Files Created/Modified

Created:

- `CONFIRMATORY_RUN_COMMAND_MANIFEST.md`
- `RUNBOOK_CONFIRMATORY_SYNTHETIC_VALIDATION.md`
- `BUILD_ONLY_POLISH_AUDIT.md`
- `scripts/preflight_confirmatory_synthetic.py`
- `tests/test_preflight_confirmatory_synthetic.py`
- `templates/reports/CROSS_FLAW_CONFIRMATORY_REPORT_TEMPLATE.md`
- `templates/reports/HELDOUT_CONFIRMATORY_REPORT_TEMPLATE.md`
- `templates/reports/SYNTHETIC_CONFIRMATORY_CLAIM_STATUS_REPORT_TEMPLATE.md`
- `templates/reports/SYNTHETIC_CONFIRMATORY_REVIEWER_APPENDIX_TEMPLATE.md`

Modified:

- `README.md`
- `paper/NEURIPS_SUBMISSION_PLAN.md`
- `SYNTHETIC_EVIDENCE_STATUS_TABLE.md`
- `CLAIMS_LEDGER_NEURIPS.md`
- `paper/CLAIMS_LEDGER.md`

## 8. Next Run Commands

Static preflight now:

```bash
python3 scripts/preflight_confirmatory_synthetic.py
```

Future confirmatory commands only after explicit approval:

```bash
python3 -m valideval validate-diagnostics-cross-flaw \
  --config configs/validation/synthetic_default.yaml \
  --output results/synthetic/cross_flaw_confirmatory
```

```bash
python3 -m valideval validate-diagnostics-heldout \
  --config configs/validation/heldout_default.yaml \
  --output results/synthetic/heldout_confirmatory
```

## 9. Recommendation

Treat this phase as `DRYRUN_READY` for future execution setup, not as empirical progress. The next
best action is to run the static preflight and review the command manifest. Confirmatory validation
should remain pending until the user explicitly authorizes execution.
