# Changelog

## 0.4.2-v7.2.1-final-cpu-maxout — 2026-08-12

- Resealed canonical S1 provenance at a dynamically resolved V7.2.1 source tag and added a
  repository-wide source-coherence validator.
- Froze and confirmed claim-family-native known-truth policy simulations with Wilson rare-event
  bounds and multiplicity-aware critical strata; the truthful result is supporting-only because
  21 of 60 critical cells fail the simultaneous safety bound.
- Added historical MMLU weighting, jackknife, bootstrap, rank, pairwise-multiplicity, benchmark-
  dependence, finite-sample, materiality, human-planning, and scorer-differential CPU stress.
- Hardened current schemas, evidence transitions, invalidation propagation, failure/retry
  taxonomy, deterministic package validation, and adversarial ZIP import rejection.
- Added CPU replay, release validation, doctor support, structured claim/method/experiment
  registries, dependency locks, generated reports, and typed final machine state.
- No new real GPU evidence, human labels, held-out transport evidence, or held-out repair evidence
  was created. S1 remains engineering-only; S2-S4 remain blocked behind their prerequisites.

## 0.4.1-v7.1-scientific-closure — 2026-08-12

- Unified the V7.1 runner, deterministic package, and importer schema and added real
  runner-to-ZIP-to-import fixture tests, resume coverage, and fail-closed provenance checks.
- Propagated typed model-load and generation OOMs into bounded scheduler recovery.
- Repaired threshold direction, dependence-aware effective-N, simultaneous rank, pairwise
  multiplicity, claim-family, and executed transport-fold licensing semantics.
- Added versioned synthetic controls with tie-invariant metrics while preserving the failed frozen
  V7 primary result.
- Added known-truth claim calibration, rank-coverage simulations, family-dependence stress,
  primary-estimand power planning, grouped cross-fitting, null contracts, Study-H estimand
  sensitivity, human resource accounting, benchmark forensics, and canonical-versus-deduplicated
  analysis.
- Kept unavailable evidence blocked: no executed transport folds, human labels, accepted S1/S2,
  measured T4 throughput, or exact BBH response matrix were fabricated.

## 0.4.0-v7-icml2027-pre-execution — 2026-08-09

- Added explicit claim contracts with identity, leakage, sample-size, power, multiplicity,
  stability, external-validation, transport, and regret gates.
- Added family-aware inferential diagnostics, seven-null Study H analysis, outcome-specific
  generalizability, selective ranking, exact influence analyses, and measurement-regime studies.
- Froze and executed a decoupled confirmatory synthetic protocol; its failed acceptance criteria
  remain visible and block confirmatory diagnostic claims.
- Added six-estimand transport and balanced blinded human protocols without inventing missing
  cross-benchmark effects or human labels.
- Added frozen S2–S5 panels, public S4 fallback routes, ten T4×2 notebooks, option-log-likelihood
  MCQ scoring, strict answer parsing, secure ingestion, and deterministic evidence routing.
- Retired exact duplicate benchmark rows from scientific manifests and preserved the fail-closed
  MMLU-Redux retirement after the available artifacts could not support exact identity linkage.
- Added CPU/reviewer/source/evidence release profiles, artifact validation, checksums, reports,
  runtime and power planning, and an explicit partial pre-execution gate.

## 0.3.0 — 2026-07-23

- Added the frozen V6 S1 five-checkpoint panel and immutable MMLU, GSM8K, and BBH contracts.
- Added the configuration-driven production runner, isolated T4×2 scheduler, bounded OOM recovery,
  exact resume identity, gold-isolated parsing/scoring, deterministic packaging, and runtime fields.
- Upgraded the six canonical Kaggle notebooks to invoke the tested V6 package path.
- Added the fail-closed three-ZIP S1 importer/acceptance gate and runtime recalibration command.
- Added locally reproducible S1 leakage guards, family-cluster rank sensitivity, and held-out
  measurement-model validation.
- Preserved the boundary that S1 is `ENGINEERING_ONLY`, not a scientific common-panel study.

## 0.2.1-neurips-evidence-pivot - Unreleased

### Added

- NeurIPS evidence-pivot scaffolding for wide prediction imports, external issue-label
  validation, panel-validity gating, wide-matrix IRT reporting, and MMLU-Redux readiness.
- Prompt-pack documentation for feature freeze, claims governance, GPQA small-panel limits,
  execution order, paper scaffolding, related-work positioning, and reviewer packet assembly.

### Guardrails

- No new paid API dependency.
- No new local LLM generation path.
- No real benchmark claims are added; missing empirical sections remain explicit placeholders.

## 0.2.0 — 2026-06-09

### Added

- Offline TF-IDF semantic duplicate detection in data-forensics (`semantic_duplicates` signal).
- Working offline domain diagnostics for all eight domain packs:
  `agent_validity`, `code_validity`, `safety_validity`, `medical_validity`,
  `graph_fraud_validity`, `multimodal_validity`.
- `legendary` audit preset spanning core, psychometric, coverage, contamination, and external-validity diagnostics.
- `audit-summary` CLI for compact terminal audit overviews.
- Diagnostic overview SVG figures embedded in report cards.
- Local MMLU JSONL loader (`--benchmark mmlu --local-path ...`) with `examples/mmlu_subset.jsonl`.
- Predictive diagnostic support for `external_criterion_path` (model- or item-level JSONL).
- Goodhart diagnostic support for `intervention_path` (pre/post intervention JSONL).
- Coverage diagnostic balance score, singleton-tag reporting, and underrepresented-tag warnings.
- Example fixtures: `examples/external_criterion_mock.jsonl`, `examples/intervention_mock.jsonl`.
- Metadata-only `doctor` CLI for offline readiness, cache/artifact hygiene, and strict CI gating.
- Stronger preregistration scaffolds with artifact scope, panel, diagnostics, claim-to-evidence
  mapping, blocked-evidence handling, and no-overclaim reporting guardrails.
- `neurips-readiness` CLI and report generator for publication-readiness gates across paper
  placeholders, claims ledger, synthetic validation, bundle verification, reviewer-risk findings,
  real-benchmark go/no-go status, and public-release metadata.

### Changed

- Version bumped to 0.2.0.
- MMLU config promoted from scaffold-only to `local_export_required`.
