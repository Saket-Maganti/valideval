# Runbook: Confirmatory Synthetic Cross-Flaw and Held-Out Validation

This runbook is a build-only execution guide for a future approved phase. It must not be used to run
experiments until the user explicitly approves confirmatory execution.

## Before Running

Confirm that:

- The user has explicitly approved confirmatory execution.
- `PREREGISTRATION_REVIEW_AUDIT.md` still reports `YES_READY`.
- `CROSS_FLAW_AND_HELDOUT_FAILURE_CASES.md` still lists CF-01 through CF-07 and HO-01 through HO-03.
- No thresholds, generators, diagnostics, or output paths have been changed after seeing results.
- All `[RESULT REQUIRED]` placeholders remain placeholders until future artifacts exist.
- MMLU-Redux is still framed as weak/negative external validation.
- GPQA is still framed as protocol/demo unless wide-panel evidence exists.

## Required Files

- `PREREGISTERED_CROSS_FLAW_HELDOUT_INVESTIGATION_PLAN.md`
- `PREREGISTRATION_REVIEW_AUDIT.md`
- `CONFIRMATORY_RUN_COMMAND_MANIFEST.md`
- `CROSS_FLAW_AND_HELDOUT_FAILURE_CASES.md`
- `SYNTHETIC_EVIDENCE_STATUS_TABLE.md`
- `CLAIMS_LEDGER_NEURIPS.md`
- `paper/CLAIMS_LEDGER.md`
- `configs/validation/synthetic_default.yaml`
- `configs/validation/heldout_default.yaml`
- `templates/reports/CROSS_FLAW_CONFIRMATORY_REPORT_TEMPLATE.md`
- `templates/reports/HELDOUT_CONFIRMATORY_REPORT_TEMPLATE.md`
- `templates/reports/SYNTHETIC_CONFIRMATORY_CLAIM_STATUS_REPORT_TEMPLATE.md`
- `templates/reports/SYNTHETIC_CONFIRMATORY_REVIEWER_APPENDIX_TEMPLATE.md`

## Environment Checks

Run this static preflight before any future validation command:

```bash
python3 scripts/preflight_confirmatory_synthetic.py
```

The preflight checks required files, frozen configs, output-path writability, templates, documented
failure cases, and blocked-claim language. It prints future commands but does not execute them.

## Frozen Configs

- Cross-flaw config: `configs/validation/synthetic_default.yaml`
- Held-out config: `configs/validation/heldout_default.yaml`

Do not edit these configs after approval unless the run is re-preregistered and the evidence state is
kept unchanged.

## Command 1: Cross-Flaw Confirmatory Run

Future only:

```bash
python3 -m valideval validate-diagnostics-cross-flaw \
  --config configs/validation/synthetic_default.yaml \
  --output results/synthetic/cross_flaw_confirmatory
```

Expected future outputs:

- `results/synthetic/cross_flaw_confirmatory/cross_flaw_matrix.json`
- `results/synthetic/cross_flaw_confirmatory/cross_flaw_matrix.csv`
- `results/synthetic/cross_flaw_confirmatory/summary.md`

## Command 2: Held-Out Confirmatory Run

Future only:

```bash
python3 -m valideval validate-diagnostics-heldout \
  --config configs/validation/heldout_default.yaml \
  --output results/synthetic/heldout_confirmatory
```

Expected future outputs:

- `results/synthetic/heldout_confirmatory/heldout_transfer.json`
- `results/synthetic/heldout_confirmatory/heldout_transfer.csv`
- `results/synthetic/heldout_confirmatory/summary.md`

## Command 3: Claim-Status Report

After both future runs complete, fill a claim-status report from actual artifacts only:

```bash
# Future build step only, after approved confirmatory artifacts exist.
# Fill templates/reports/SYNTHETIC_CONFIRMATORY_CLAIM_STATUS_REPORT_TEMPLATE.md
# without inventing values or removing surviving failure cases.
```

No repository command is registered for this report yet. Until a real report is built from future
artifacts, keep `[RESULT REQUIRED]` markers in the templates and docs.

## Command 4: Static Checks

Allowed checks for the build/preflight surface:

```bash
ruff check .
python3 -m pytest -q tests/test_preflight_confirmatory_synthetic.py
```

Optional after broader code changes:

```bash
python3 -m pytest -q
```

These checks do not replace the confirmatory validation run and do not upgrade evidence states.

## How To Interpret Outcomes

- Passing all gates supports only diagnostic-specific synthetic claims under the exact frozen
  protocol.
- Any material off-target activation keeps cross-flaw specificity `WEAK` or blocks broad
  specificity claims.
- Any held-out AUC below 0.75, transfer drop above 0.25, or missing held-out artifact blocks
  generator-transfer claims for the affected diagnostic/family.
- Missing or malformed artifacts remain `RESULT_REQUIRED` or `BLOCKED`.
- A single favorable cell cannot upgrade an entire diagnostic family.
- Synthetic success does not establish real-benchmark validity.

## What To Do If A Gate Fails

- Preserve the failing row and compare it with the frozen CF/HO failure-case list.
- Record the failure in the claim-status report.
- Keep or downgrade the affected claim state.
- Use review-queue-only language where sensitivity exists but specificity or transfer fails.
- Do not tune thresholds, rerun with altered generators, or remove failures from denominators.
- Do not convert a failed gate into a success claim through post-hoc wording.

## What Not To Claim

- All diagnostics generalize across flaw families.
- Synthetic validation proves real benchmark validity.
- Cross-flaw specificity is solved.
- Held-out transfer is solved.
- ValidEval detects real benchmark errors.
- MMLU-Redux validates the diagnostics.
- GPQA establishes broad validity evidence.
- Numeric calibration exists without confidence/logprob outputs.
- Planned or template-only artifacts are empirical results.
