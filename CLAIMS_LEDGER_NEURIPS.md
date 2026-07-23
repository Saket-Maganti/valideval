# NeurIPS Claims Ledger — V5

This human-readable ledger mirrors the machine ledger at
`results/evidence/claim_evidence_ledger_v5.csv`. Evidence states are categorical; they must not be
collapsed into one validity score.

| Claim | Primary artifact | V5 state | Paper use |
|---|---|---|---|
| The public HELM-derived Study H panel has 39 models, 14,042 items, and 57 subjects. | `results/evidence/mmlu_reproduction_v5/mmlu_reproduction_v5.json` | `REPRODUCED` | Yes, with source and protocol scope. |
| Study H contains 547,638 unique model-item rows and zero missing cells, duplicate rows, contradictory duplicates, identity conflicts, or partial coverage. | Same reproduction manifest and normalized reconstruction | `REPRODUCED` | Yes, as panel-integrity evidence only. |
| The reconstructed matrix exactly equals `cache/mmlu/wide/matrix.csv`. | Matrix comparison plus matching SHA-256 `f85a0a44...86e74` | `REPRODUCED` | Yes. |
| Observed Study H aggregate accuracy spread is 0.580188. | Reproduction manifest | `REPRODUCED` | Yes, descriptive only. |
| Raw subject rank ranges have median 19 and maximum 30. | Reproduction manifest | `REPRODUCED` | Yes, descriptive and protocol-scoped. |
| Proxy diagnostic weighting remains close to accuracy ranking: Spearman 0.997976, Kendall 0.978408, maximum absolute rank delta 2. | Reproduction manifest | `REPRODUCED` | Yes, explicitly proxy-only. |
| A raw subject rank range of at least 10 is automatically severe or material. | No defensible primary threshold justification | `RETIRED` | No. Report effect sizes, uncertainty, nulls, and decision consequences instead. |
| The legacy eight-family table is a genuine diagnostic-family ablation. | Forensic comparison shows seven family columns reuse accuracy. | `CONTRADICTED` | No. It may be discussed only as a retired artifact defect. |
| MMLU-Redux confirms item-level ValidEval detection. | Structural linkage is weak and not direct/hash-confirmed; AUROC 0.539168, AUPRC 0.028908, precision@10 0. | `RETIRED` | Limitation/negative stress test only. |
| Exact-checkpoint transfer across controlled MMLU, GSM8K, and BBH runs is established. | Required Study C matrices and V5 receipts do not yet exist. | `BLOCKED` | Placeholder only. |
| Human review confirms flagged benchmark issues. | No imported V5 human labels. | `BLOCKED` | Placeholder only. |
| Decoupled synthetic sensitivity and specificity are established. | Preregistered protocol exists; confirmatory output does not. | `BLOCKED` | Protocol only. |

## Study separation

- **Study H** is historical public HELM-derived MMLU evidence. Its model aliases do not provide
  immutable checkpoint identity for controlled cross-benchmark claims.
- **Study C** is the planned exact-checkpoint common-panel study across MMLU, GSM8K, and BBH. It is
  not a continuation or relabeling of Study H.
- Fixture runs exercise schemas, sharding, import, and analysis plumbing and remain
  `NON_EVIDENCE_FIXTURE`.

## Prohibited claims

The following legacy claim guards remain exact and prohibited:

- All diagnostics generalize across flaw families.
- Synthetic validation proves real benchmark validity.
- Cross-flaw specificity is solved.
- Held-out transfer is solved.
- ValidEval detects real benchmark errors.
- MMLU-Redux validates the diagnostics.
- GPQA establishes broad validity evidence.

Also do not claim that one diagnostic proves contamination, that MMLU is globally invalid, that the
controlled common-panel transfer result exists, that the legacy synthetic AUCs independently validate
the diagnostics, or that any ranking is the true ranking.

Use `[RESULT REQUIRED: ...]` for Study C, human, and confirmatory synthetic results until their primary
artifacts pass the V5 gates.
