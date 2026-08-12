# ValidEval V7.1 Synthetic Control Completion

Status: `V7_1_SYNTHETIC_CONTROL_SUITE_COMPLETE`.

The separate V7.1 suite produced 45 rows across eight requested control classes: label permutation,
no flaw, unseen flaw, held-out generator family, mixed flaws, diagnostic ablation,
family-dependence stress, and a difficulty-conditioned negative control. No-flaw rows correctly
leave positive-class metrics undefined rather than inventing a value.

The normalized results hash is
`4197a50279184d7e624820af991800b473484ebedd0abdaefecca1339abfefbe` after declared 12-decimal
normalization. Repeated execution produced the same hash. Mean metrics vary materially by control;
for example, mixed-flaw AUPRC was 0.495 and held-out-generator-family AUPRC was 0.143. These are
generator-scoped diagnostic observations, not confirmatory success criteria.
