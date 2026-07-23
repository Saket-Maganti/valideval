# Synthetic Confirmatory Claim-Status Report Template

## Summary

[RESULT REQUIRED: state whether the future confirmatory artifacts change any claim status under the
frozen preregistered gates.]

## Inputs

- Cross-flaw artifact: `results/synthetic/cross_flaw_confirmatory/cross_flaw_matrix.json`
- Held-out artifact: `results/synthetic/heldout_confirmatory/heldout_transfer.json`
- Cross-flaw report: [RESULT REQUIRED]
- Held-out report: [RESULT REQUIRED]
- Frozen claim ledgers: `CLAIMS_LEDGER_NEURIPS.md`, `paper/CLAIMS_LEDGER.md`

## Commands

```bash
# Future-only source commands; do not list them as executed unless approved artifacts exist.
python3 -m valideval validate-diagnostics-cross-flaw \
  --config configs/validation/synthetic_default.yaml \
  --output results/synthetic/cross_flaw_confirmatory

python3 -m valideval validate-diagnostics-heldout \
  --config configs/validation/heldout_default.yaml \
  --output results/synthetic/heldout_confirmatory
```

[RESULT REQUIRED: exact approved command log and artifact hashes.]

## Metrics

| Evidence block | Current status before run | Future artifact metric | Gate result | Status after run |
|---|---|---|---|---|
| Cross-flaw specificity | `WEAK` | [RESULT REQUIRED] | [RESULT REQUIRED] | [RESULT REQUIRED] |
| Held-out generator transfer | `WEAK` | [RESULT REQUIRED] | [RESULT REQUIRED] | [RESULT REQUIRED] |
| Null/FPR control | `SUPPORTED` under synthetic generators | [RESULT REQUIRED] | [RESULT REQUIRED] | [RESULT REQUIRED] |
| Materiality thresholding | `WEAK` | [RESULT REQUIRED] | [RESULT REQUIRED] | [RESULT REQUIRED] |
| Synthetic-to-real threshold validation | `NOT_RUN` | [RESULT REQUIRED] | [RESULT REQUIRED] | [RESULT REQUIRED] |

## Failure Cases Before vs After

| Failure family | Frozen before-run count | Future surviving count | Notes |
|---|---:|---:|---|
| Cross-flaw off-target activations | 7 | [RESULT REQUIRED] | [RESULT REQUIRED] |
| Non-paper-eligible held-out transfer families | 3 | [RESULT REQUIRED] | [RESULT REQUIRED] |

## Decision Rules

- Upgrade only when intended sensitivity, cross-flaw specificity, held-out transfer, and null/FPR
  gates all pass for the exact diagnostic/family.
- Keep `WEAK` when sensitivity exists but specificity or transfer fails.
- Mark `BLOCKED` when required artifacts are missing, malformed, or fail preregistered gates.
- Keep `RESULT_REQUIRED` where future evidence has not been produced.
- Never upgrade MMLU-Redux or GPQA based on synthetic confirmatory results.

## Claims Allowed

[RESULT REQUIRED: exact allowed wording after future artifact review.]

## Claims Blocked

- All diagnostics generalize across flaw families.
- Synthetic validation proves real benchmark validity.
- Cross-flaw specificity is solved unless all relevant preregistered gates pass.
- Held-out transfer is solved unless all relevant preregistered gates pass.
- ValidEval detects real benchmark errors.
- MMLU-Redux validates the diagnostics.
- GPQA establishes broad validity evidence.

## Reviewer-Risk Notes

[RESULT REQUIRED: describe claim changes, non-changes, surviving caveats, and any evidence-state
downgrades.]
