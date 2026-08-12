# ValidEval V7.1 Deep-Audit Repair Ledger

Date: 2026-08-12

Baseline: `b5970ed9c1109a7e4aefc1218b7aa956d4ce102b`

Boundary: this ledger records implementation and CPU evidence. It does not claim missing GPU,
human, or transport results.

## P0 closure

| Issue | Repair | Verification | State |
|---|---|---|---|
| Mutable or mismatched source identity | All V7 run configs pin the V7.1 source tag; runner manifests record required, expected, and actual commits and their match | config tests and source-resolution tests | closed in code; final tag recorded by the reseal |
| Runner/package/import mismatch | One runner-native `run_manifest.json` and prediction schema; `matrix.csv` is required; ZIP and directory imports use the same validator | real mock runner→ZIP→import and resume tests | closed |
| Generation OOM swallowed | Typed load/generation OOMs reach the scheduler; recovery is bounded and recorded | load, generation, fallback, exhaustion tests | closed |
| Threshold claim bug | Direction and decision threshold are explicit; equality does not license | exact-boundary tests | closed |
| Raw sample size used as independence | claim-specific inferential unit and dependence-aware `effective_n` are mandatory | missing/unit/minimum tests | closed |
| Marginal ranks labeled simultaneous | max-rank-deviation joint bootstrap sets added; marginal intervals are separately named | known-truth coverage and label tests | closed |
| Unadjusted all-pairs decisions | BH FDR is primary and Holm FWER is sensitivity; family metadata is retained | multiplicity tests and Study-H output | closed |
| Synthetic protocol overstatement | frozen V7 failure preserved; V7.1 controls are separate and generator-scoped | deterministic control suite | closed |
| Tie-dependent metrics | AUPRC evaluates complete score groups and precision@k uses expected random boundary ties | row-order/tie tests | closed |
| Power disconnected from estimands | eight declared estimands use active model, family, benchmark, item, dependence, and error inputs | sensitivity tests and 72-cell planning grid | closed |

## P1 closure and honest demotions

- Study H now reports canonical item weighting and balanced subject weighting separately.
- Seven nulls have machine-readable fixed/estimated/randomized/hypothesis contracts; misleading
  empirical-Bayes, random-effects, and fixed-margin labels were removed from the V7.1 report.
- Sensitivity sweeps use 100 Monte Carlo replicates with Monte Carlo SE and quantiles.
- Generalizability remains `GENERALIZABILITY_REMAINS_SUPPORTING_ONLY`.
- Measurement-regime work remains `MEASUREMENT_REGIME_SUPPORTING_ONLY`.
- Transport manifests distinguish `PLANNED` from `EXECUTED`; only executed folds with hashed data
  artifacts can license a claim. No executed fold exists in this closure.
- Cross-fitting partitions whole model families with zero family overlap.
- Human plans multiply all four strata and report unique items, raw labels, and adjudication.
- Forensics reports exact/normalized evidence available from frozen manifests and refuses a
  contamination conclusion.
- MMLU canonical-versus-deduplicated estimands were run; BBH is blocked by the missing exact
  response matrix.

## Remaining empirical blockers

Accepted S1/S2 artifacts, a T4 preflight, measured throughput, executed transport folds, human
annotations, and an exact BBH Study-C response matrix remain absent. These are evidence gaps, not
implementation failures, and none is represented as a positive finding.
