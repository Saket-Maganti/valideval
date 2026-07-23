# Static Confirmatory Synthetic Preflight Report

## 1. Executive Summary

The static confirmatory synthetic preflight passed. This was a no-run check only: no validation,
synthetic generation, model inference, downloads, metric recomputation, threshold tuning, or
evidence-state changes were performed.

The future-run surface is ready for later explicit execution approval from a static-file and
path-readiness perspective. Confirmatory execution remains deferred.

## 2. Command Run

```bash
python3 scripts/preflight_confirmatory_synthetic.py
```

Output was captured to:

```text
results/synthetic/preflight_confirmatory_synthetic/preflight_output.txt
```

## 3. Preflight Status

`PASS`

The preflight reported:

- preregistration and runbook docs: `OK`
- frozen validation configs: `OK`
- result report templates: `OK`
- future output directories: `OK`
- documented failure cases: `OK`
- blocked claims in ledgers: `OK`

## 4. Required Documents

Found all 5 documents checked by the preflight:

- `PREREGISTERED_CROSS_FLAW_HELDOUT_INVESTIGATION_PLAN.md`
- `PREREGISTRATION_REVIEW_AUDIT.md`
- `CONFIRMATORY_RUN_COMMAND_MANIFEST.md`
- `RUNBOOK_CONFIRMATORY_SYNTHETIC_VALIDATION.md`
- `paper/appendices/cross_flaw_heldout_preregistration_note.md`

## 5. Required Configs

Found both frozen configs:

- `configs/validation/synthetic_default.yaml`
- `configs/validation/heldout_default.yaml`

## 6. Required Templates

Found all 4 report templates:

- `templates/reports/CROSS_FLAW_CONFIRMATORY_REPORT_TEMPLATE.md`
- `templates/reports/HELDOUT_CONFIRMATORY_REPORT_TEMPLATE.md`
- `templates/reports/SYNTHETIC_CONFIRMATORY_CLAIM_STATUS_REPORT_TEMPLATE.md`
- `templates/reports/SYNTHETIC_CONFIRMATORY_REVIEWER_APPENDIX_TEMPLATE.md`

## 7. Output Path Writability

The preflight reported that both future output directories can be created under `results/synthetic`:

- `results/synthetic/cross_flaw_confirmatory`
- `results/synthetic/heldout_confirmatory`

The preflight did not create these future output directories.

## 8. Frozen Failure Cases

The preflight found the frozen failure-case IDs and current weak-status language:

- CF-01 through CF-07
- HO-01 through HO-03
- Cross-flaw specificity remains `WEAK`
- Held-out generator transfer remains `WEAK`

No failure case was removed or reclassified.

## 9. Blocked-Claim Language

The preflight found all 7 blocked claims in both claims ledgers:

- `CLAIMS_LEDGER_NEURIPS.md`
- `paper/CLAIMS_LEDGER.md`

Blocked claims remain blocked, including universal diagnostic generalization, real-benchmark
validity from synthetic evidence, solved cross-flaw specificity, solved held-out transfer, real
benchmark error detection, MMLU-Redux validation success, and broad GPQA evidence.

## 10. Future Commands Printed

The preflight printed these future commands as not executed:

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

These commands remain pending future explicit approval.

## 11. Evidence States

Evidence states remain unchanged:

- cross-flaw specificity: `WEAK`
- held-out generator transfer: `WEAK`
- numeric calibration: `BLOCKED`
- synthetic-to-real threshold validation: `NOT_RUN`
- confirmatory follow-up: `RESULT_REQUIRED`
- MMLU-Redux: weak/negative external validation
- GPQA: protocol/demo unless wide-panel evidence exists

## 12. Missing Items

None reported by the static preflight.

Limitations of this preflight:

- It verifies static readiness, not empirical outcomes.
- It does not run future validation commands.
- It does not create or inspect future confirmatory artifacts.

## 13. Ready Status

`STATIC_PREFLIGHT_PASS`

## 14. Next Step

Keep confirmatory execution deferred. The next safe action is reviewer/user review of the manifest,
runbook, templates, and captured preflight output. The validation commands should run only after a
new explicit approval for confirmatory execution.
