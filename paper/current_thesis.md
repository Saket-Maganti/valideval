# Current Thesis

Benchmark-validity diagnostics are often treated as if they license benchmark-quality claims, but
their own validity is rarely tested. ValidEval provides a disciplined audit framework and, in its
current strongest real stress test, matrix-derived diagnostics on the active 39-model HELM MMLU
panel do not robustly recover structurally aligned MMLU-Redux issue labels. Diagnostic claims must
be gated, externally validated, and separated from software sanity checks.

## Current Framing

ValidEval should be framed as a measurement-science and claim-gating paper, not as a generic toolkit
success story. The central contribution is a conservative evidence discipline:

- validity is a multidimensional evidence profile, not a single scalar score;
- the active MMLU substrate is the 39-model HELM MMLU wide matrix;
- the older 3-model MMLU files are historical/provenance only;
- proxy IRT artifacts exist, but full 2PL has not run;
- MMLU-Redux remains weak/negative under structural alignment;
- legacy synthetic AUCs are wiring/sanity-check artifacts only;
- future validation claims require approved, artifact-backed runs.

## Paper Posture

The paper should emphasize the cautionary result and the evidence gates. It should not claim MMLU
error detection, MMLU validity or invalidity, ranking flips, second-benchmark transfer, full 2PL, or
NeurIPS readiness.
