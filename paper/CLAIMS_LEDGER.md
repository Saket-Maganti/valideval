# Paper Claims Ledger — V5

The generated CSV ledger at `../results/evidence/claim_evidence_ledger_v5.csv` is authoritative. This
file records the prose boundary for the paper scaffold.

| Paper claim | State | Safe wording | Missing evidence |
|---|---|---|---|
| Study H panel integrity is reproducible. | `REPRODUCED` | Under the V5 reconstruction protocol, the HELM-derived MMLU matrix contains 39 models, 14,042 items, 57 subjects, and 547,638 complete unique responses. | None for those panel facts. |
| Study H has substantial descriptive subject-rank variation. | `REPRODUCED` | Raw subject rank ranges have median 19 and maximum 30 under this panel. | A preregistered materiality decision rule is still needed for any practical-severity claim. |
| Proxy diagnostic weighting changes the Study H ordering little. | `REPRODUCED` | The proxy comparison has Spearman 0.997976, Kendall 0.978408, and maximum absolute rank delta 2. | Full measurement-model validation; this result is not a true-ranking claim. |
| Rank range at least 10 means severe/material. | `RETIRED` | No fixed severity conclusion is licensed by raw rank range alone. | Effect-size, uncertainty, null, and decision-cost justification. |
| Legacy diagnostic-family ablation supports family contributions. | `CONTRADICTED` | The old table is not an ablation because seven columns reuse accuracy. | Recompute genuinely independent removals on eligible future evidence. |
| MMLU-Redux validates item detection. | `RETIRED` | Structural Redux linkage is a weak/negative, non-direct stress test. | Direct/hash-confirmed identity and stronger independent validation. |
| Exact-model transfer across MMLU, GSM8K, and BBH. | `BLOCKED` | `[RESULT REQUIRED: controlled Study C matrices and exact-overlap gate]` | Valid V5 runs, import receipts, exact checkpoint overlap, and preregistered analysis. |
| Human review validates diagnostic flags. | `BLOCKED` | `[RESULT REQUIRED: blinded human labels and agreement/adjudication artifacts]` | Actual labels. |
| Decoupled synthetic sensitivity/specificity. | `BLOCKED` | `[RESULT REQUIRED: confirmatory decoupled synthetic run]` | Actual preregistered outputs. |

Study H and Study C must remain separate. Fixture output is `NON_EVIDENCE_FIXTURE`, planning output is
`PLANNED`, and neither may populate empirical paper cells.

## Prohibited claim guards

- All diagnostics generalize across flaw families.
- Synthetic validation proves real benchmark validity.
- Cross-flaw specificity is solved.
- Held-out transfer is solved.
- ValidEval detects real benchmark errors.
- MMLU-Redux validates the diagnostics.
- GPQA establishes broad validity evidence.

Each sentence above names a blocked claim, not a finding.
