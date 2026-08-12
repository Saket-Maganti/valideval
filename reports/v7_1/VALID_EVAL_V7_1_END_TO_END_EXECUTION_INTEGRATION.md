# ValidEval V7.1 End-to-End Execution Integration

Status: `V7_1_END_TO_END_RUN_PACKAGE_INGEST_READY`

The production-shaped fixture test invokes `run_from_config` with the mock backend, 200 items, and
eight models. It then imports both the generated directory and deterministic ZIP through the same
V7.1 importer. A resumed run is packaged and imported through the same path.

## Canonical contract

- Manifest: `run_manifest.json`, schema `valideval.execution.v7.1`.
- Predictions: runner-native `parsed_output` and `is_correct` fields.
- Required package members include `predictions.jsonl`, `matrix.csv`, `run_manifest.json`, and
  checksums.
- Import verifies safe ZIP paths, exact run directory, schema, config hash, source commit,
  checkpoint revisions, item/model uniqueness, package membership, and every checksum.
- The analysis router emits `READY_TO_RUN` only for accepted evidence and retains fixture blocking.

## Negative-path proof

Tests cover a declared model failure, source mismatch, config mismatch, unsupported schema, mixed
checkpoint revisions, duplicate responses, checksum tampering, traversal, and rejection of the old
hand-built `manifest.json` format. Model-load and generation OOM exhaustion are recorded rather than
silently converted into ordinary empty generations.

This proves the local interface and failure behavior. It is not evidence that a real T4 run or any
benchmark panel has completed.
