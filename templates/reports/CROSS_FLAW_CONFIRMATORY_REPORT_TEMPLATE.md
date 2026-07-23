# Cross-Flaw Confirmatory Report Template

## Summary

[RESULT REQUIRED: summarize the future cross-flaw confirmatory run outcome without upgrading claims
unless preregistered gates pass.]

## Inputs

- Config: `configs/validation/synthetic_default.yaml`
- Preregistration: `PREREGISTERED_CROSS_FLAW_HELDOUT_INVESTIGATION_PLAN.md`
- Frozen failure cases: `CROSS_FLAW_AND_HELDOUT_FAILURE_CASES.md`
- Output directory: `results/synthetic/cross_flaw_confirmatory`

## Commands

```bash
# Future command that produced this report, if and only if the run was approved.
python3 -m valideval validate-diagnostics-cross-flaw \
  --config configs/validation/synthetic_default.yaml \
  --output results/synthetic/cross_flaw_confirmatory
```

[RESULT REQUIRED: command execution timestamp, environment, and artifact hashes.]

## Metrics

- Intended-flaw ROC AUC: [RESULT REQUIRED]
- Off-target ROC AUC: [RESULT REQUIRED]
- Clean false-positive rate: [RESULT REQUIRED]
- Specificity: [RESULT REQUIRED]
- Paper-eligibility flag: [RESULT REQUIRED]
- Materiality status, if emitted: [RESULT REQUIRED]

## Failure Cases Before vs After

| ID | Frozen before-run case | Confirmatory result | Gate status | Interpretation |
|---|---|---|---|---|
| CF-01 | `shortcut` on off-target `too_easy_saturation`, AUC 1.0 | [RESULT REQUIRED] | [RESULT REQUIRED] | [RESULT REQUIRED] |
| CF-02 | `distractor_quality` on off-target `prompt_format_fragility`, AUC 0.9928385416666666 | [RESULT REQUIRED] | [RESULT REQUIRED] | [RESULT REQUIRED] |
| CF-03 | `distractor_quality` on off-target `too_easy_saturation`, AUC 0.9694010416666666 | [RESULT REQUIRED] | [RESULT REQUIRED] | [RESULT REQUIRED] |
| CF-04 | `redundancy` on off-target `shortcut_signal`, AUC 0.9791666666666666 | [RESULT REQUIRED] | [RESULT REQUIRED] | [RESULT REQUIRED] |
| CF-05 | `saturation` on off-target `shortcut_signal`, AUC 0.875 | [RESULT REQUIRED] | [RESULT REQUIRED] | [RESULT REQUIRED] |
| CF-06 | `saturation` on off-target `prompt_format_fragility`, AUC 0.875 | [RESULT REQUIRED] | [RESULT REQUIRED] | [RESULT REQUIRED] |
| CF-07 | `saturation` on off-target `extraction_ambiguity`, AUC 0.875 | [RESULT REQUIRED] | [RESULT REQUIRED] | [RESULT REQUIRED] |

## Decision Rules

- Intended-flaw sensitivity passes only if intended-flaw AUC >= 0.80.
- Cross-flaw specificity passes only if no material off-target activation remains.
- Material off-target activation is off-target AUC >= 0.80.
- Null/FPR control passes only if clean FPR <= 0.10 unless a stricter preregistered diagnostic gate
  applies.
- Missing artifacts are `RESULT_REQUIRED` or `BLOCKED`, not implicit passes.

## Claims Allowed

[RESULT REQUIRED: list only diagnostic-specific claims supported by the future artifact and frozen
gates.]

## Claims Blocked

- Universal diagnostic specificity.
- Cross-flaw specificity is solved for all diagnostics.
- Real-benchmark validity conclusions from synthetic evidence alone.
- Any upgrade based on one favorable cell.
- Any claim whose supporting metric remains [RESULT REQUIRED].

## Reviewer-Risk Notes

[RESULT REQUIRED: describe surviving off-target activations, possible shared latent flaw structure,
generator artifact risk, and denominator preservation.]
