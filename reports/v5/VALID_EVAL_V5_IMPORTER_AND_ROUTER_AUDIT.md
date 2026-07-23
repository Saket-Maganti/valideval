# ValidEval V5 Importer and Router Audit

Audit date: 2026-07-16  
Empirical input state: no real V5 Kaggle ZIPs available

## Verdict

- Importer implementation: `IMPORTER_V5_ADVERSARIAL_VALIDATED`
- V5 post-import router: `POST_IMPORT_V5_DRY_RUN_ROUTER_VALIDATED`
- Imported scientific evidence: `BLOCKED`

The V5 importer is fail-closed and is adversarially validated with deterministic fixture archives. The new receipt-driven V5 router revalidates the canonical receipt, run manifest, configuration hash, and imported file checksums before emitting a dry-run analysis plan. No real archive was imported and no recommended scientific command was executed in this pass.

## Import security

`src/valideval/importers/kaggle_v5.py` validates archives before extraction and rejects or bounds:

- relative traversal, absolute POSIX/Windows paths, case-colliding members, and symlinks;
- nested archives by default and executable file types;
- excessive member counts, member sizes, total expansion, and compression ratios;
- missing required files and unsupported schema versions;
- malformed configuration snapshots and manifest/checksum disagreement;
- source ZIP hash disagreement when an expected or declared hash is supplied.

Extraction occurs only after validation into a destination derived from validated identifiers.

## Manifest and data integrity

The importer enforces the V5 run manifest, configuration hash, declared model list, benchmark contract, shard completeness, per-file SHA-256 hashes, normalized prediction schema, failure summary, and optional matrix agreement. Prediction validation checks exact run/study/benchmark identity, model revision consistency, allowed tasks/subtasks, unique model-item-attempt identity, conflicting duplicates, item collisions, declared row counts, usable-item coverage, extraction reliability, and evidence state.

The normalized schema keeps `extraction_status`, `generation_status`, and `failure_type` separate from `is_correct`; an extraction failure therefore cannot silently become an ordinary wrong answer.

## Idempotence and conflicts

An import ledger keys runs by `study_id::run_id` and stores the source ZIP hash. Reimporting the same archive returns `already_imported` without duplicating evidence. Reusing that run identity with different archive bytes raises `ImportConflictError`. Cache copies also fail on content conflicts.

## Router behavior

A successful import receipt contains:

- exact model IDs and model-family mapping;
- usable item count and extraction reliability;
- configuration class and study ID;
- data-integrity and evidence state.

`src/valideval/importers/post_import_v5.py` consumes only the canonical `import_receipt_v5.json` inside the validated import directory. Before routing it:

- requires the V5 importer schema, accepted import status, importer verdict, and valid source ZIP SHA-256;
- verifies receipt/run/study/benchmark/config/evidence identity;
- recomputes the configuration hash;
- rechecks every manifest file checksum to detect post-import tampering;
- verifies manifest, prediction, shard, matrix, and benchmark-contract counts/identities;
- refuses all routes if any supplied receipt is invalid.

The dry-run plan then exposes separate stages for feasibility, extraction reliability, coverage, model accuracy, subject/subtask analysis, ranking materiality, measurement models, cross-benchmark eligibility, and paper assets. Every stage records prerequisite reasons plus exactly one of `recommended_command` or `blocked_command`. Dependent stages require extraction and coverage gates; rank materiality and measurement additionally require non-fixture evidence and minimum panel/item/family conditions.

The planner never executes a recommended command. Paper generation remains blocked even when commands are recommended because a plan is not proof that the analysis artifacts exist or passed. This prevents import success from becoming paper readiness.

The contradicted V4 diagnostic-family ablation is explicitly retired and never appears in recommended commands. The V5 router does not call legacy `post-import-analysis` or generic-positive V4 cross routing.

## Cross-benchmark gate behavior

The separate V5 gate returns exactly one of:

- `CROSS_BENCHMARK_READY_EXACT_COMMON_PANEL`
- `CROSS_BENCHMARK_EXPLORATORY_FAMILY_LEVEL_ONLY`
- `CROSS_BENCHMARK_BLOCKED_INSUFFICIENT_MODEL_OVERLAP`
- `CROSS_BENCHMARK_BLOCKED_CONFIGURATION_MISMATCH`
- `CROSS_BENCHMARK_BLOCKED_DATA_INTEGRITY`

It checks usable items and extraction reliability before overlap, requires a common study/configuration class for exact analysis, validates family metadata consistency, and distinguishes exact-checkpoint from family-only overlap.

## Verification

```text
python3 -m pytest -q tests/test_kaggle_importer_adversarial_v5.py tests/test_cross_benchmark_gates_v5.py tests/test_cross_benchmark_analysis_v5.py
9 passed in 0.99s
```

Covered attacks include traversal, symlink, nested archive, high compression ratio, missing manifest, checksum tampering, same-archive idempotence, and different-hash run conflicts. The cross-benchmark tests cover exact pass, configuration mismatch, integrity failure, family-only routing, insufficient overlap, successful fixture analysis, and fail-closed analysis.

Router-focused verification:

```text
python3 -m pytest -q tests/test_post_import_router_v5.py
4 passed in 1.36s

ruff check src/valideval/importers/post_import_v5.py tests/test_post_import_router_v5.py
All checks passed

ruff format --check src/valideval/importers/post_import_v5.py tests/test_post_import_router_v5.py
2 files already formatted

mypy src/valideval/importers/post_import_v5.py
Success: no issues found in 1 source file
```

The router tests cover safe fixture-only routing, receipt/manifest mismatch refusal, low-extraction/low-coverage dependent-stage blocking, three-benchmark cross-gate failure, and absence of the contradicted V4 ablation from recommended commands.

The integrated CLI/route/import/gate check also passed:

```text
python3 -m pytest -q tests/test_post_import_router_v5.py tests/test_cli_v5.py tests/test_kaggle_importer_adversarial_v5.py tests/test_cross_benchmark_gates_v5.py
15 passed in 1.43s
```

`python3 -m valideval post-import --help` exposes the V5 receipt, import-root, output, extraction, coverage, and strict options while the V4 aliases remain available for historical compatibility only.

All accepted fixture imports remain `NON_EVIDENCE_FIXTURE`; passing these tests does not verify an external Kaggle artifact.

## Exact next action

Import the first S1 archive with explicit expected study/benchmark/config/ZIP hashes, verify idempotent reimport, and run the router in its default dry-run mode. Review `post_import_plan_v5.json`; invoke only commands present in `recommended_commands`; then rerun an artifact-aware gate before paper generation. Real evidence remains blocked until this sequence succeeds.
