# Preregistration Review Audit

## 1. Executive Summary

The preregistered cross-flaw and held-out transfer plan is now reviewer-defensible as a no-run
planning artifact. The review found that the existing plan already preserved the 7 cross-flaw
off-target activations, the 3 non-paper-eligible held-out transfer families, and the current `WEAK`
evidence states. Minor clarity fixes were needed before a confirmatory run: primary versus secondary
hypotheses, family-level/multiple-comparison rules, explicit state-change conditions, and synchronized
blocked-claim language.

No experiments were run, no metrics were recomputed, no thresholds were tuned, and no evidence states
were upgraded.

## 2. Files Reviewed

- `PREREGISTERED_CROSS_FLAW_HELDOUT_INVESTIGATION_PLAN.md`
- `CROSS_FLAW_AND_HELDOUT_FAILURE_CASES.md`
- `paper/appendices/cross_flaw_heldout_preregistration_note.md`
- `SYNTHETIC_VALIDATION_ARTIFACT_INVENTORY.md`
- `SYNTHETIC_EVIDENCE_STATUS_TABLE.md`
- `SYNTHETIC_VALIDATION_NARRATIVE_AUDIT.md`
- `paper/diagnostic_validation.md`
- `paper/experiments.md`
- `paper/claims.md`
- `paper/limitations.md`
- `CLAIMS_LEDGER_NEURIPS.md`
- `paper/CLAIMS_LEDGER.md`

Static source inspection was used only to confirm the future command surfaces and existing gate
definitions. No validation command was executed.

## 3. Reviewer-Defensibility Checklist

| Check | Status After Review | Notes |
|---|---|---|
| Primary hypotheses | Clear | H3 and H4 are now marked as primary claim-status hypotheses. |
| Secondary hypotheses | Clear | H1, H2, and H5 are now marked as secondary explanatory hypotheses. |
| Primary metrics | Clear | Intended-flaw AUC, off-target AUC, held-out AUC, transfer drop, clean FPR, and paper-eligibility flag remain specified. |
| Secondary metrics | Clear | PR AUC, specificity, materiality, null/FPR status, downgrade reason, and review-queue-only eligibility remain specified. |
| Minimum passing thresholds | Clear | AUC, transfer-drop, and FPR gates are explicit. |
| Failure thresholds | Clear | Gate-failure conditions are now tabulated. |
| Stopping rules | Clear | One frozen cross-flaw run and one frozen held-out run; partial/malformed artifacts are reported rather than repaired silently. |
| Multiple-comparison handling | Clear | A diagnostic cannot be upgraded from one favorable cell; family-level consistency across gates is required. |
| False-positive/null controls | Clear | Clean FPR gate remains explicit. |
| Materiality thresholds | Clear with caveat | Materiality must use emitted/frozen materiality status; missing threshold remains `RESULT_REQUIRED` or `WEAK`. |
| Held-out generator criteria | Clear | Held-out AUC >= 0.75 and transfer drop <= 0.25. |
| Off-target activation criteria | Clear | Off-target AUC >= 0.80 is material for this plan. |
| Exact future commands | Clear | Future-only commands are listed; they were not run in this phase. |
| Expected output files | Clear | Cross-flaw and held-out JSON, CSV, summary Markdown, and claim-status report are specified. |
| Claim-upgrade rules | Clear | Upgrade requires intended sensitivity, specificity, held-out transfer, and null/FPR gates. |
| Claim-blocking rules | Clear | Failures keep claims `WEAK`/`BLOCKED` and block specificity/transfer/generalization claims. |
| Anti-tuning guardrails | Clear | Fixed configs, fixed gates, fixed output paths, and visible failure reporting are specified. |
| Reviewer-visible failure reporting | Clear | Prior failures must be reported side by side with confirmatory outcomes. |

## 4. Ambiguities Found

- The original hypothesis section listed H1-H5 without distinguishing primary claim-status
  hypotheses from secondary explanatory hypotheses.
- The original plan could be read as allowing one favorable diagnostic/flaw cell to support a broad
  upgrade.
- Multiple-comparison/family-level interpretation was implicit rather than reviewer-visible.
- State-change conditions were spread across decision rules instead of summarized in a reviewer-facing
  table.
- The reviewer note and claims ledgers did not all carry the exact same blocked-claim language.

## 5. Edits Made

- Split hypotheses into primary claim-status hypotheses and secondary explanatory hypotheses.
- Added minimum passing and failure threshold table to the preregistration plan.
- Added explicit multiple-comparison and family-level claim-upgrade language.
- Added `What Would Change the Evidence State?` table.
- Added exact `Do not claim` block to the preregistration plan.
- Added the same `Do not claim` block to the reviewer-facing note.
- Added the same blocked-claim language to `paper/claims.md`, `CLAIMS_LEDGER_NEURIPS.md`, and
  `paper/CLAIMS_LEDGER.md`.

## 6. Remaining Risks

- The confirmatory cross-flaw and held-out runs have not been executed.
- Cross-flaw specificity and held-out generator transfer remain `WEAK`.
- Two held-out cases remain near chance-level in the existing artifacts.
- Synthetic-to-real threshold validation remains `NOT_RUN`.
- Numeric calibration remains `BLOCKED` without confidence/logprob outputs.
- A future confirmatory run may preserve or worsen the observed failures; that outcome must remain
  visible rather than tuned away.

## 7. Claims Allowed

- ValidEval provides a diagnostic-validation harness for controlled synthetic flaw families.
- Some diagnostics show controlled sensitivity under implemented synthetic flaw generators.
- Existing cross-flaw and held-out artifacts expose specificity and transfer risks.
- The cross-flaw and held-out investigation is preregistered before confirmatory execution.
- Failure cases are scientifically useful for claim gating and diagnostic downgrades.

## 8. Claims Blocked

- All diagnostics generalize across flaw families.
- Synthetic validation proves real benchmark validity.
- Cross-flaw specificity is solved.
- Held-out transfer is solved.
- ValidEval detects real benchmark errors.
- MMLU-Redux validates the diagnostics.
- GPQA establishes broad validity evidence.

## 9. Ready for Confirmatory Run?

YES_READY

This means the no-run preregistration artifact is ready to govern a later approved confirmatory run.
It does not mean that the confirmatory run has been executed or that any `WEAK` evidence state has
been upgraded.

## 10. Next Recommended Command

No validation command should be run in this review phase. In a future approved execution phase, run
the frozen commands from `PREREGISTERED_CROSS_FLAW_HELDOUT_INVESTIGATION_PLAN.md`, beginning with:

```bash
# Future only - do not run in this review phase.
python3 -m valideval validate-diagnostics-cross-flaw \
  --config configs/validation/synthetic_default.yaml \
  --output results/synthetic/cross_flaw_confirmatory
```
