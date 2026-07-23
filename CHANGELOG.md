# Changelog

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
