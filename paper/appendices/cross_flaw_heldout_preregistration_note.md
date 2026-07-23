# Reviewer Note: Cross-Flaw and Held-Out Transfer Preregistration

## What We Observed

The current synthetic evidence is mixed. Controlled synthetic flaw detection is strongest, but the
cross-flaw matrix contains 7 strong off-target activations and held-out generator transfer contains 3
non-paper-eligible families.

## Why We Do Not Overclaim

These failures mean controlled synthetic sensitivity does not automatically imply diagnostic
specificity, held-out transfer, or real-benchmark validity. We therefore keep cross-flaw specificity
and held-out transfer labeled `WEAK`.

Do not claim:

- All diagnostics generalize across flaw families.
- Synthetic validation proves real benchmark validity.
- Cross-flaw specificity is solved.
- Held-out transfer is solved.
- ValidEval detects real benchmark errors.
- MMLU-Redux validates the diagnostics.
- GPQA establishes broad validity evidence.

## What We Preregister Before Running More Experiments

Before any confirmatory rerun, we freeze the failure-case list, primary metrics, decision rules,
stopping rules, and output paths in `PREREGISTERED_CROSS_FLAW_HELDOUT_INVESTIGATION_PLAN.md`.

## How This Protects Against Tuning

The plan fixes the gates before results are regenerated: intended-flaw AUC >= 0.80, off-target AUC <
0.80, held-out AUC >= 0.75, transfer drop <= 0.25, and clean FPR <= 0.10 unless a stricter
diagnostic-specific gate is preregistered. Failure cases must remain visible even if later runs
improve.

## What Evidence Would Upgrade a Diagnostic Claim

A diagnostic can move from `WEAK` to `SUPPORTED` only if it passes intended-flaw sensitivity,
cross-flaw specificity, held-out transfer, and null/FPR control under the preregistered protocol.
Otherwise it may remain useful as an exploratory review-queue heuristic, but not as claim-supporting
evidence.
