# Abstract

We present ValidEval, an offline-safe framework for validating benchmark-validity diagnostics before
using them to support benchmark claims. On a 39-model HELM MMLU panel with 14,042 scored items,
ValidEval produces artifact-backed panel-validity, proxy psychometric, ranking-sensitivity, and
baseline analyses. The strongest current real-panel finding is subject-level rank sensitivity; proxy
diagnostic-weighted rankings remain close to accuracy rankings.

The same artifact trail blocks stronger claims. Direct/hash MMLU-Redux alignment is unconfirmed,
structural MMLU-Redux validation remains weak/negative, decoupled synthetic validation and
second-benchmark evidence remain `RESULT_REQUIRED`, and full parametric 2PL has not run.
