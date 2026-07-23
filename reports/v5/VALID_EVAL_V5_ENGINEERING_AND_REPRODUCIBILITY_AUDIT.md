# ValidEval V5 Engineering and Reproducibility Audit

Audit date: 2026-07-16  
Scope: local-safe verification; no private data, network inference, Kaggle, or human study

## Verdict

`LOCAL_VALIDATION_PASS_V5_FIXTURE_EXECUTION_READY_PRODUCTION_BLOCKED`

The complete clean-environment validation ledger passes all 30 commands. The V5 execution,
importer/router, cross-benchmark, human, synthetic, paper, release, and forensic surfaces pass their
local integrity gates. Scientific execution is still blocked because the notebook stages have no
production model/dataset/scoring runner, the exact common panel is incomplete, and the empirical
inputs required by the P0 leakage and controlled-study gates do not exist.

## Environment and packaging design

- Build backend: `setuptools.build_meta`.
- Supported Python: 3.10 and newer; local verification used Python 3.11.
- Minimal runtime dependencies are separated from optional dataset, acquisition, Parquet, Ollama, notebook, and development groups.
- Development notebook validation includes a pinned-major Python kernel dependency; runtime
  notebook requirements use bounded major-version ranges rather than unbounded upgrades.
- The console entry point is `valideval = valideval.cli:main`.
- Package discovery is rooted at `src`; package data includes domain JSON.
- The Makefile provides install, test, lint, format, targeted typecheck, build, offline toy/audit, V5 evidence/planning, and allowlist release targets.
- `clean` removes caches/build products rather than touching evidence/data trees.

## CI design

The GitHub Actions workflow uses Python 3.11 and runs editable dev installation, Ruff lint, format check, full pytest, package build, source-release build, and CLI help. It does not require a model service, private dataset, GPU, paid API, or benchmark download.

The release builder is allowlist-driven and separately defines source, evidence, and reviewer profiles. Companion release tests check deterministic ZIP behavior and exclusion of raw/cache/secret/nested-archive content.

## Verification results

Full suite:

```text
python3 -m pytest -q
305 passed, 2 warnings in 10.44s

.venv-v5/bin/python -m pytest -q
305 passed, 2 warnings in 35.97s
```

The warnings are `ConstantInputWarning` from two calls in the legacy V4 post-import tiny-matrix test; no test failed or skipped.

Execution/protocol subset:

```text
python3 -m pytest -q \
  tests/test_kaggle_notebooks_v5.py \
  tests/test_t4x2_scheduler_v5.py \
  tests/test_notebook_fixture_execution_v5.py \
  tests/test_kaggle_importer_adversarial_v5.py \
  tests/test_cross_benchmark_gates_v5.py \
  tests/test_cross_benchmark_analysis_v5.py \
  tests/test_human_validation_v5.py \
  tests/test_confirmatory_synthetic_v5.py \
  tests/test_synthetic_decoupling_v5.py \
  tests/test_gold_answer_isolation_v5.py
39 passed in 1.62s
```

Critical-module quality checks from the final ledger:

```text
python3 -m ruff check .
All checks passed

python3 -m ruff format --check .
328 files already formatted

python3 -m mypy <V5 evidence/execution/import/cross/planning/statistics/measurement/leakage/synthetic/external/human modules>
Success: no issues found in 40 source files
```

Packaging, paper, release, and forensic gates:

```text
python3 -m build                                      exit 0
pdflatex/bibtex/pdflatex/pdflatex paper/v5/main.tex  all exit 0
source/evidence release dry runs                     both exit 0
reviewer deterministic ZIP build                    exit 0
repository forensic inventory                       exit 0
```

The authoritative lossless record is `results/v5_validation/command_ledger_v5.json`: status
`PASS`, 30 commands passed, and zero failed.

## Reproducibility strengths

- Canonical JSON and stable SHA-256 configuration/file hashes.
- Atomic manifest/status writes and configuration-mismatch refusal on resume.
- Full normalized prediction provenance, explicit failure taxonomy, and separate extraction/generation/correctness fields.
- Deterministic shards, fixture scheduler, merge ordering, and ZIP metadata.
- Import ledger idempotence and same-run/different-hash conflict detection.
- Exact checkpoint/config/family/coverage gates before cross-benchmark analysis.
- Human packet hashing and physical public/private separation.
- Synthetic public/private recursive isolation.
- Fixture artifacts are explicitly non-evidence.

## Residual engineering blockers

- The benchmark contracts and dataset revisions are frozen, but the BBH few-shot content/hash and
  redistribution review are not.
- The Kaggle notebooks do not yet call a production model/dataset/scoring runner.
- The exact Study C roster is only five checkpoints across three nominal families, below the
  planned S3 target of 32/8.
- Full controlled split and cross-benchmark overlap inputs do not exist, so P0 leakage remains.
- Family-cluster bootstrap and a justified model-bootstrap estimand are missing.
- The cross-benchmark interaction summary is descriptive, not hierarchical.
- The V5 human components pass fixtures, but the licensed sampling frame and integrated pilot do
  not exist.
- The confirmatory synthetic generator/sweep executor is absent.
- The repository remains in unborn Git state, so no immutable code revision or tag exists.

## Exact next action

Do not launch Kaggle. Implement and fixture-test the configuration-driven production runner behind
`run_notebook_stage`, freeze/hash the BBH few-shot artifact and package environment, and rerun the
canonical clean validation. Only a resulting `CONTROLLED_GPU_SMOKE_READY` gate may authorize the
five-checkpoint S1 engineering smoke.
