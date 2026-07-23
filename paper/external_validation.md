# External Validation

The HELM MMLU / MMLU-Redux block is a weak/negative external-validation stress test, not the paper's
positive evidence centerpiece.

The current stress test joins sanitized matrix-derived diagnostic flags against structurally aligned
MMLU-Redux issue labels. Broad/proxy diagnostics did not strongly recover MMLU-Redux labels,
subject-normalized evidence weakened the raw label-error signal, and the remaining raw top-k signal is
only a preliminary review-queue cue.

Allowed interpretation: ValidEval can run external stress-test surfaces and block unsupported claims.
Blocked interpretation: MMLU error-detection success, MMLU-Redux label-validation success, or an
external-validation-success claim for proxy IRT flags as MMLU-error detectors.
