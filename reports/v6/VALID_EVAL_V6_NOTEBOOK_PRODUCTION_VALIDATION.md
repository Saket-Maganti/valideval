# ValidEval V6 Notebook Production Validation

Gate: `KAGGLE_NOTEBOOKS_PRODUCTION_PATH_VALIDATED`

All six canonical notebooks are valid nbformat 4 documents with deterministic cell IDs and no saved
outputs or execution counts. Each locates or installs the tagged package, selects versioned config,
delegates to `run_notebook_stage`, prints package/config/source/status information, reports expected
ZIP paths, and prints local acceptance and runtime-recalibration commands.

Top-to-bottom fixture execution passed for all six notebooks. A mocked production integration
traversed the real runner, two-worker scheduler, 250-row merge, manifest/checksum validation,
deterministic package, exact resume, validate-only, and package-only paths. Mocked inputs are
accepted only when the config is both backend `mock` and `NON_EVIDENCE_FIXTURE`; injection into the
real Transformers backend fails closed.

Local real-mode preflight resolves exact hashes and stops on the absence of two CUDA devices before
any model download. Remote Kaggle T4×2 execution itself remains the next action, not a claimed
validation result.
