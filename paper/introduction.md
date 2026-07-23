# Introduction

Validity is not accuracy. A benchmark score can be high while the benchmark measures shortcuts,
contamination, scoring artifacts, saturation, or low-discrimination items rather than the claimed
construct.

ValidEval treats benchmark-validity diagnostics as measurement instruments. A diagnostic should
support a claim only after it has evidence about sensitivity, false-positive behavior, specificity,
uncertainty, and materiality under a documented protocol.

The current empirical spine is the 39-model HELM MMLU wide matrix. ValidEval runs panel-validity,
proxy IRT diagnostics, ranking/subject-instability analyses, and baselines on cached local artifacts.
The resulting paper-usable finding is subject-level rank sensitivity under this panel.

The HELM MMLU / MMLU-Redux case is not an error-detection success case. MMLU-Redux remains a
weak/negative external-validation stress test: direct/hash alignment is unconfirmed, broad
matrix-derived diagnostics did not strongly recover structurally aligned labels, and the claims
ledger blocks detection-success claims.

Contributions:

1. A measurement-validity framework for benchmark diagnostics with explicit evidence states:
   supported, weak, blocked, or not run.
2. Artifact-backed real-panel analyses of a public 39-model HELM MMLU matrix.
3. A claims-ledger and evidence-gating workflow that prevents unsupported validity claims.
4. A MMLU-Redux stress test showing that broad proxy diagnostics do not automatically validate
   against structurally aligned external issue labels.
5. An offline-safe toolkit and reproducible audit artifact format for benchmark authors and
   evaluators.
