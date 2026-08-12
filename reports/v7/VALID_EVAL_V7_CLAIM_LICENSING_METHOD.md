# ValidEval V7 Claim-Licensing Method

Gate: `CLAIM_LICENSING_METHOD_READY` (method implementation only).

Validity is represented as a profile, never a scalar. The V7 contract separates model-comparison,
top-k, item-suspicion, transport, repair, and benchmark-validity claims. Each claim fails closed on
applicable identity, leakage, sample-size, power, uncertainty/materiality, multiplicity, bootstrap
stability, external/held-out validation, transport heterogeneity, and decision-regret gates.

The executable state machine returns `LICENSED`, `LICENSED_WITH_SCOPE`, or a named blocking state.
The contract tests exercise both successful and failed paths. This validates software behavior; it
does not license a real benchmark-quality claim. The V7 evidence ledger currently blocks item
suspicion, transfer, human-validation, and repair claims. The synthetic detector also failed its
frozen acceptance gates (median AUPRC 0.113, median FDR
0.966).

Primary implementation: `src/valideval/claims/`. Backing artifact:
`results/v7/evidence/claim_evidence_ledger_v7.csv`.
