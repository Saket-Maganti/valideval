# ValidEval V7.1 Transport-Fold Provenance

Protocol status: `TRANSPORT_FOLD_SPECIFICATION_READY`.

Empirical status: `BLOCKED_PENDING_EXECUTED_FOLDS`.

V7.1 defines hashed leave-one-benchmark-out and leave-one-family-out fold manifests. Each carries
training and held-out benchmarks/families, training and evaluation model IDs, discovery and
evaluation item identities, source commit, config hash, execution state, and canonical fold hash.
Family holdouts reject any model overlap; every fold rejects discovery/evaluation item overlap.

The generator produced three benchmark specifications and nine family specifications from the
eleven-model, nine-family S3 panel. They are marked `PLANNED`, not `EXECUTED`. An executed manifest
must include at least one SHA-256-addressed data artifact. Both transport analysis and claim
licensing reject planned folds.

No cross-benchmark effect is estimated in this report. Transport remains blocked until the planned
folds are executed and the effect, direction, heterogeneity, overlap, and family gates all pass.
