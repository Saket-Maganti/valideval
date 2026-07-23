# Results — V5 Evidence-Aware Scaffold

## Study H: reproduced historical MMLU panel

Independent reconstruction of the public HELM-derived source produced 547,638 unique model-item
responses spanning 39 models, 14,042 items, and 57 subjects. The reconstructed matrix exactly matches
the active matrix by labels, values, and SHA-256. No missing cells, duplicate rows, contradictory
duplicates, identity conflicts, invalid correctness values, or partial coverage were observed.

Observed aggregate accuracy spread is 0.580188. Raw subject rank ranges have median 19 and maximum
30. The proxy diagnostic-weighted ordering remains close to the aggregate-accuracy ordering
(Spearman 0.997976; Kendall 0.978408; maximum absolute rank delta 2). These are panel-specific
descriptive results under the V5 protocol, not a global validity or true-ranking conclusion.

The former threshold declaring a raw rank range of at least 10 “severe” is retired. The V5 analysis
reports continuous effect sizes, uncertainty, null comparisons, confidence sets, pairwise outranking,
leave-one-subject-out sensitivity, and family-aware summaries instead of converting one raw range
into an unsupported severity label.

## Negative/retired validation paths

The legacy diagnostic-family ablation is contradicted because seven purported family removals reuse
accuracy. MMLU-Redux is retained only as a weak structural stress test: its mapping is not
direct/hash-confirmed and its reported AUROC 0.539168, AUPRC 0.028908, and precision@10 0 do not
support positive item-detection claims.

## Study C and confirmatory placeholders

- `[RESULT REQUIRED: controlled exact-checkpoint MMLU result]`
- `[RESULT REQUIRED: controlled exact-checkpoint GSM8K result]`
- `[RESULT REQUIRED: controlled exact-checkpoint BBH result]`
- `[RESULT REQUIRED: exact-overlap cross-benchmark analysis]`
- `[RESULT REQUIRED: blinded human validation]`
- `[RESULT REQUIRED: decoupled confirmatory synthetic validation]`

No planned, fixture, or blocked value may populate these cells.
