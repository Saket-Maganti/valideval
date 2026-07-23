# Synthetic Confirmatory Reviewer Appendix Template

## Summary

[RESULT REQUIRED: concise reviewer-facing summary of future confirmatory synthetic cross-flaw and
held-out results.]

## Inputs

- Preregistration: `PREREGISTERED_CROSS_FLAW_HELDOUT_INVESTIGATION_PLAN.md`
- Review audit: `PREREGISTRATION_REVIEW_AUDIT.md`
- Failure cases: `CROSS_FLAW_AND_HELDOUT_FAILURE_CASES.md`
- Cross-flaw outputs: [RESULT REQUIRED]
- Held-out outputs: [RESULT REQUIRED]
- Claim-status report: [RESULT REQUIRED]

## Commands

```bash
# Future-only commands; include execution metadata only after explicit approval and completion.
python3 -m valideval validate-diagnostics-cross-flaw \
  --config configs/validation/synthetic_default.yaml \
  --output results/synthetic/cross_flaw_confirmatory

python3 -m valideval validate-diagnostics-heldout \
  --config configs/validation/heldout_default.yaml \
  --output results/synthetic/heldout_confirmatory
```

[RESULT REQUIRED: execution date, environment, artifact hashes, and static-check output.]

## Metrics

- Cross-flaw intended-flaw AUC range: [RESULT REQUIRED]
- Cross-flaw off-target activation count: [RESULT REQUIRED]
- Held-out family count: [RESULT REQUIRED]
- Held-out paper-eligible family count: [RESULT REQUIRED]
- Largest transfer drop: [RESULT REQUIRED]
- Clean/null control status: [RESULT REQUIRED]
- Materiality status: [RESULT REQUIRED]

## Failure Cases Before vs After

| Category | Before confirmatory run | After confirmatory run | Reviewer interpretation |
|---|---|---|---|
| Cross-flaw failures | 7 frozen off-target activations | [RESULT REQUIRED] | [RESULT REQUIRED] |
| Held-out failures | 3 frozen non-paper-eligible families | [RESULT REQUIRED] | [RESULT REQUIRED] |
| Evidence-state changes | None in build-only phase | [RESULT REQUIRED] | [RESULT REQUIRED] |

## Decision Rules

- Results are interpreted under the frozen gates only.
- Favorable results do not remove the need to report prior failure cases.
- Failed or missing rows block affected claims.
- Synthetic confirmatory evidence remains synthetic evidence, not real-benchmark validation.

## Claims Allowed

[RESULT REQUIRED: reviewer-safe claim wording backed by future artifacts.]

## Claims Blocked

- Universal diagnostic generalization.
- Real-benchmark validity conclusions from synthetic evidence alone.
- MMLU-Redux diagnostic-validation success.
- GPQA broad validity evidence.
- Numeric calibration without confidence/logprob outputs.
- Any claim based on missing `[RESULT REQUIRED]` rows.

## Reviewer-Risk Notes

[RESULT REQUIRED: summarize risk of generator coupling, off-target activation, materiality overread,
and synthetic-to-real overclaiming.]
