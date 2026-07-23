# ValidEval V5 Repair Changelog

## Scope accounting

The repository began this pass as an unborn Git worktree with no tracked baseline. Git therefore
cannot distinguish “added” from “modified.” The combined pass-scope count is `240` maintained files
since `2026-07-15 18:44:00` local time, excluding environments, caches, build/dist, package metadata,
`.DS_Store`, Python bytecode, and transient LaTeX auxiliaries. Known new V5 surfaces are listed
separately in the final handoff. No historical artifact was deleted to manufacture a clean state.

## P0 scientific repairs

1. Independently reconstructed the 39 × 14,042 public HELM-derived MMLU matrix from 547,638
   primary long-form rows and verified exact matrix equality, zero missing cells, and frozen
   input/output hashes.
2. Retired the post-hoc “severe rank range ≥10” interpretation. Replaced it with tie-aware rank
   uncertainty, practical reversals, top-k stability, four explicit null protocols, and
   family/subject sensitivity outputs. Richer additive nulls do not reproduce the old severity
   interpretation.
3. Marked the legacy eight-family ablation `CONTRADICTED`: seven named variants reuse
   accuracy-derived values rather than independently computed diagnostics.
4. Separated historical Study H from controlled Study C. Five public Study C checkpoint
   revisions and all three dataset revisions are now pinned; the S3 panel remains incomplete.
5. Re-ran MMLU-Redux identity resolution fail-closed. Zero of 370 rows are confirmed; the old
   item-level external-validation interpretation is retired.
6. Renamed the old panel-validity gate to minimum matrix adequacy and explicitly blocked
   psychometric-validity and unrestricted 2PL claims.
7. Added executable gold/label/isolation guards, a formal leakage audit, and preregistration
   freezes. The final P0 leakage gate remains closed until full controlled item snapshots and the
   BBH few-shot hash are available.

## Execution and integrity repairs

- Added the full normalized prediction schema, failure taxonomy, configuration hashing,
  per-worker T4x2 scheduler, atomic heartbeats/checkpoints, bounded retry, resume mismatch refusal,
  deterministic merge, and fixture packaging.
- Added six canonical `kaggle_max_ceiling` notebooks. They pass top-to-bottom fixture execution,
  but non-fixture model/dataset inference remains deliberately blocked rather than simulated.
- Added a hardened V5 ZIP importer with traversal/symlink/bomb/nested-archive defenses,
  checksum/manifest/schema/coverage validation, idempotence, and conflict refusal.
- Added a receipt-driven V5 post-import router. It revalidates artifacts and only recommends
  downstream commands whose prerequisites pass; it never routes the contradicted V4 ablation.
- Added exact-overlap cross-benchmark gates and predeclared analysis outputs. Real transfer
  remains `RESULT_REQUIRED`.
- Replaced three benchmark stubs with complete, immutable MMLU/GSM8K/BBH contracts. BBH license
  review and few-shot-example hash remain pre-S1 blockers.

## Validation-system repairs

- Added blinded human packet construction, private randomization/control mapping, strict import,
  nominal Krippendorff alpha, agreement/bootstrap components, and precision planning. No human
  evidence was created.
- Added decoupled synthetic public/private boundaries and a frozen experiment configuration.
  Fixture plumbing passes; confirmatory generators and the full grid remain unimplemented.
- Added panel power/identifiability and S1 runtime planners. Every output is explicitly
  `PLANNED`; full-run timing is blocked until imported S1 calibration.
- Added a transparent regularized subject-conditioned logit decomposition, additive comparison,
  recovery fixture, and assumption gates. It is not called a full mixed model or IRT validation.

## Engineering, paper, and release repairs

- Added V5 CLI aliases, type-check configuration, CI/build gates, safe cleanup, clean-environment
  validation, and Python 3.10-compatible string enums.
- Applied repository-wide Ruff formatting and preserved passing behavior.
- Added a compiling V5 paper scaffold whose unavailable results are explicit placeholders, plus
  current claims/evidence/limitations documentation.
- Added allowlist-only deterministic source/evidence/reviewer release builders and forensic
  secret/cache/raw-data exclusions.
- Marked `FINAL_V4_PRE_EXECUTION_GATE.md` `SUPERSEDED_BY_V5` without erasing the historical record.

## Retired, stale, or blocked surfaces

| Surface | V5 state |
|---|---|
| Legacy severe rank threshold | `RETIRED` |
| Legacy diagnostic-family ablation | `CONTRADICTED` |
| MMLU-Redux item-level validation | `RETIRED` |
| Historical “panel validity” wording | `STALE`; alias retained for compatibility |
| V4 generic-positive post-import/cross route | preserved historically; not used by V5 |
| Real Kaggle benchmark outputs | `BLOCKED` |
| Cross-benchmark transfer | `BLOCKED` |
| Human/external confirmation | `BLOCKED` |
| Confirmatory synthetic findings | `BLOCKED` |
| Benchmark-repair success | `BLOCKED` |

## Known remaining implementation gaps

- Connect production model/dataset/scoring runners to the notebook stages.
- Freeze BBH few-shot examples/hash and verify its redistribution terms.
- Expand the exact common panel from 5/3 models/families toward the planned S3 target of 32/8.
- Add family-cluster bootstrap and a justified model-bootstrap estimand.
- Replace descriptive cross-benchmark interaction decomposition with a preregistered fitted model.
- Implement confirmatory synthetic generators/grid and integrate the human pilot end to end.
- Create the first real Git commit/tag before any reproducibility claim tied to code revision.

The authoritative commands, gates, and continuation order are in
`VALID_EVAL_MAXIMUM_CEILING_EXECUTION_HANDBOOK.md` and
`VALID_EVAL_MAXIMUM_CEILING_PRE_EXECUTION_HANDOFF.md`.
