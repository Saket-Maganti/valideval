# ValidEval V7.1 Claim Semantics and Effective N

Status: `CLAIM_SEMANTICS_READY` and `DEPENDENCE_AWARE_INFERENCE_READY`.

## Decision semantics

Threshold claims carry an explicit numeric `decision_threshold`, direction (`ABOVE` or `BELOW`),
and optional units. An above-threshold claim requires the lower confidence bound to be strictly
greater than the threshold; a below-threshold claim requires the upper bound to be strictly less.
Equality abstains. The point estimate alone never licenses the threshold claim.

## Dependence contract

Every inferential claim requires `estimand_unit`, `effective_n`, `independence_unit`, and a described
`dependence_structure`. Optional `raw_n` and `cluster_count` are recorded for audit. The legacy
`sample_size` field is readable for V7 ledgers but is ignored by V7.1 licensing.

Claim-specific units are enforced: items/subjects for pairwise and rank decisions, model families
for family and suspicious-item claims, subjects for instability, and benchmarks or model families
for transport/repair. Effective N must be positive, cannot exceed raw N when raw N is supplied, and
must clear the unit-specific policy minimum.

Multiplicity-dependent claims also require a hypothesis-family identifier and scope. Transport
requires an executed fold manifest with a hashed data artifact. The deterministic contract examples
are tests of gate behavior, not benchmark findings.
