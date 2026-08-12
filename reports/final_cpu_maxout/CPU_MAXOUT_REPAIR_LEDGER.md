# CPU Max-Out Repair Ledger

Generated from structured artifacts. It is an engineering/scientific audit record, not a final paper claim.

## Structured sources

- `results/final_cpu_maxout/replay/cpu_replay.json`
- `results/final_cpu_maxout/extraction/summary.json`

## Closed correctness and safety defects

- Canonical source provenance now resolves the immutable source tag dynamically.
- Rare-event safety uses Wilson bounds, including nonzero upper risk for zero events.
- Archive import rejects traversal, symlinks, duplicates, excessive members, oversized members, encryption, and extreme compression ratios.
- Operational failures have bounded, typed retry policy; deterministic provenance and scoring failures are not retried.
- Evidence invalidation propagates through an acyclic provenance graph.
- The MMLU answer parser now requires an answer-token boundary; differential fixtures report 1.000 agreement.
- Odd-sized tied model panels no longer trigger rank-simulation broadcasting failure.

Frozen historical outcomes were not rewritten.
