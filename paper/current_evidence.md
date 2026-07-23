# Current Evidence — V5

## Reproduced Study H evidence

The public HELM-derived MMLU source was normalized and reconstructed independently. The primary
input has SHA-256 `38485dc89aa44f44cd5f8078df246d76aad3570ce15295559fa0a72d6f9379c6`.
The reconstructed and active matrices both have SHA-256
`f85a0a44f3203de2863d86bf13b2c81d8e934ae4c07b826193b5e93a3fc86e74` and exactly equal labels
and values.

The reproduced panel has 39 models, 14,042 items, 57 subjects, 547,638 unique response rows, and no
missing cells, duplicate rows, contradictory duplicates, identity conflicts, invalid correctness
values, or partial item/model coverage. Observed aggregate accuracy spread is 0.580188. Raw subject
rank ranges have median 19 and maximum 30. The proxy diagnostic-weighted comparison has Spearman
0.997976, Kendall 0.978408, and maximum absolute rank delta 2.

These statements are `REPRODUCED` under this protocol. They do not establish construct validity,
contamination, a true model ranking, or a general materiality threshold.

## Retired or contradicted evidence

- The legacy rule “subject rank range >=10 is severe/material” is `RETIRED`.
- The legacy eight-family diagnostic ablation is `CONTRADICTED`; seven family columns reuse
  accuracy instead of independently removing diagnostics.
- Positive item-level MMLU-Redux validation is `RETIRED`. Structural linkage is weak and not
  direct/hash-confirmed (AUROC 0.539168, AUPRC 0.028908, precision@10 0).

## Evidence still blocked

Controlled Study C exact-checkpoint results for MMLU, GSM8K, and BBH; cross-benchmark transfer;
human-validation labels; and decoupled confirmatory synthetic results remain `BLOCKED`. Their
notebooks, schemas, fixtures, and preregistrations establish execution readiness only.
