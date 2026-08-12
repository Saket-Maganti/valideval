# ValidEval V7.1 Repair Changelog

## Execution and provenance

- Unified V7.1 runner/package/import schemas and required `matrix.csv`.
- Added exact source/config/revision/checksum validation for directory and ZIP imports.
- Added typed model-load/generation OOM propagation and bounded recovery.
- Pinned every V7 execution config to the canonical V7.1 source tag.

## Claims and statistics

- Added explicit threshold direction, inferential units, effective N, dependence metadata, claim
  family metadata, and executed-fold transport evidence.
- Added joint max-deviation rank sets, separate marginal intervals, BH/Holm all-pairs adjustment,
  known-truth rank coverage, and claim calibration.
- Split Study-H score estimands, renamed nulls to match implementation, and converted sensitivity
  sweeps to replicated Monte Carlo analyses.

## Validation and planning

- Added a distinct V7.1 synthetic control suite and tie-invariant ranking metrics while preserving
  the frozen V7 failure.
- Rebuilt Study-C power around eight estimands and active family/model counts.
- Added grouped cross-fit, transport fold specifications, human cost accounting, manifest-bounded
  forensics, MMLU estimand comparison, and a throughput-dependent compute optimizer.

## Deliberate non-upgrades

- Generalizability and measurement-regime analyses are demoted to supporting-only.
- Transport, human validation, S1/S2 acceptance, BBH estimand comparison, and compute selection
  remain blocked by absent evidence.
