# Held-Out Confirmatory Report Template

## Summary

[RESULT REQUIRED: summarize the future held-out confirmatory run outcome without upgrading claims
unless preregistered gates pass.]

## Inputs

- Config: `configs/validation/heldout_default.yaml`
- Preregistration: `PREREGISTERED_CROSS_FLAW_HELDOUT_INVESTIGATION_PLAN.md`
- Frozen failure cases: `CROSS_FLAW_AND_HELDOUT_FAILURE_CASES.md`
- Output directory: `results/synthetic/heldout_confirmatory`

## Commands

```bash
# Future command that produced this report, if and only if the run was approved.
python3 -m valideval validate-diagnostics-heldout \
  --config configs/validation/heldout_default.yaml \
  --output results/synthetic/heldout_confirmatory
```

[RESULT REQUIRED: command execution timestamp, environment, and artifact hashes.]

## Metrics

- Original ROC AUC: [RESULT REQUIRED]
- Held-out ROC AUC: [RESULT REQUIRED]
- Transfer drop: [RESULT REQUIRED]
- Clean false-positive rate, if emitted: [RESULT REQUIRED]
- Paper-eligibility flag: [RESULT REQUIRED]
- Diagnostic downgrade reason, if emitted: [RESULT REQUIRED]

## Failure Cases Before vs After

| ID | Frozen before-run case | Confirmatory result | Gate status | Interpretation |
|---|---|---|---|---|
| HO-01 | `shortcut`, `shortcut_signal` to `keyword_artifact`, AUC drop 0.4281684027777778 | [RESULT REQUIRED] | [RESULT REQUIRED] | [RESULT REQUIRED] |
| HO-02 | `distractor_quality`, `dead_distractors` to `answer_length_artifact`, AUC drop 0.1410590277777778 | [RESULT REQUIRED] | [RESULT REQUIRED] | [RESULT REQUIRED] |
| HO-03 | `redundancy`, `redundancy` to `context_leakage`, AUC drop 0.48958333333333337 | [RESULT REQUIRED] | [RESULT REQUIRED] | [RESULT REQUIRED] |

## Decision Rules

- Held-out transfer passes only if held-out AUC >= 0.75 and transfer drop <= 0.25.
- Missing held-out artifacts are `RESULT_REQUIRED` or `BLOCKED`, not implicit passes.
- A paper-eligible held-out row supports only that diagnostic/family under the frozen protocol.
- Failed held-out transfer blocks generalization claims for the affected diagnostic/family.

## Claims Allowed

[RESULT REQUIRED: list only detector-specific held-out transfer claims supported by the future
artifact and frozen gates.]

## Claims Blocked

- Universal held-out generator transfer.
- Held-out transfer is solved for all diagnostics.
- Real-benchmark validity conclusions from synthetic evidence alone.
- Any upgrade based on a favorable non-representative generator.
- Any claim whose supporting metric remains [RESULT REQUIRED].

## Reviewer-Risk Notes

[RESULT REQUIRED: describe surviving transfer drops, generator-detector coupling risks, and whether
the future evidence remains review-queue-only.]
