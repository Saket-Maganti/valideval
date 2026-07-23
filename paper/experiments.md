# Experiments

## Experiment 1: Legacy Controlled Synthetic Wiring Check

Legacy wiring/sanity-check surface only. Existing local artifacts report 12 controlled synthetic
diagnostic/flaw experiments. Ten were historically marked `credible_under_synthetic_harness`, two are
marked `prototype_only`, and none are quarantined. The controlled summary includes ROC AUC, PR AUC,
clean FPR, monotonicity, and materiality labels, but those values are not treated as independent
diagnostic-validation evidence because the legacy harness couples injected flaw labels, controlled
model behavior, and flaw-specific readout.

Diagnostic-validation evidence remains `[RESULT REQUIRED]` pending a decoupled flaw-agnostic
synthetic harness or stronger real external validation.

## Experiment 2: Cross-Flaw Specificity

Tests whether diagnostics fire only on intended threat families rather than becoming generic
benchmark-error indicators. The existing cross-flaw matrix covers 64 diagnostic/flaw pairings and
reports 7 strong off-target activations, so the result is useful but mixed.

Follow-up is preregistered in `PREREGISTERED_CROSS_FLAW_HELDOUT_INVESTIGATION_PLAN.md`; it has not
been run, so this evidence remains `WEAK`.

## Experiment 3: Held-Out Generator Validation

Tests whether diagnostics generalize beyond generator-detector mirroring. Existing held-out artifacts
cover 6 families and mark 3 as paper-eligible. Under the circularity audit, these remain legacy
synthetic transfer artifacts, not primary validation evidence. Large transfer drops for the other
families should be reported as detector-specificity limitations.

Follow-up is preregistered in `PREREGISTERED_CROSS_FLAW_HELDOUT_INVESTIGATION_PLAN.md`; it has not
been run, so this evidence remains `WEAK`.

## Experiment 4: HELM MMLU / MMLU-Redux External Stress Test

Current strongest real stress test. The active HELM MMLU wide matrix has 39 models and 14,042 items,
and the panel-size blocker is cleared for this matrix. Historical 3-model files are provenance only.
Proxy IRT artifacts exist for the active panel; full Rasch/1PL and full parametric 2PL have not run.

Real-panel ranking/disagreement artifacts now exist. Subject-level rank sensitivity is artifact-backed
with max subject rank range 30 and all 39 models showing subject rank range at least 3. Proxy
diagnostic-weighted ranking remains close to accuracy ranking, with Spearman 0.9979757085020243 and
max absolute rank delta 2.

Broad Redux validation on the 39-model HELM MMLU matrix is weak under structural alignment.
Issue-type-specific validation showed a narrow raw `label_error` review-queue signal for
`correct_answer_rarely_selected`, but subject-normalized validation weakened the raw signal. A focused
1000-iteration subject-matched null for label-error diagnostics found limited top-k review-queue
hints, not detection-success evidence. Direct/hash MMLU-Redux alignment remains unconfirmed.

The current MMLU-Redux evidence should be treated as a limitation and evidence-gating example, not a
success case. Final appendix:
`paper/appendices/mmlu_redux_evidence_appendix.md`.

## Experiment 5: GPQA Protocol Case Study

Protocol/demo case, not broad validity evidence. Small local GPQA panels remain protocol-only unless
a future wide, non-chance panel clears the relevant readiness gates.

All MMLU-Redux reporting must remain sanitized: no raw MMLU question text or answer choices.

## Experiment 6: Deferred Real-Panel and Transfer Evidence

Direct/hash MMLU-Redux alignment, decoupled synthetic validation, and second-benchmark evidence
remain `[RESULT REQUIRED]`. No MMLU error-detection, second-benchmark transfer, full 2PL, or NeurIPS
readiness claim is made from the current artifact set.
