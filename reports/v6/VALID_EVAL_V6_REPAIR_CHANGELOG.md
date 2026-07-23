# ValidEval V6 Repair Changelog

## Provenance and distribution

- Created the reviewed V5 baseline commit/tag from an unborn repository.
- Expanded ignore rules for raw data, caches, environments, generated outputs, and archives.
- Added staged-file, oversized-file, secret, and raw-redistribution audits.
- Bound production execution to the final V6 tag and runtime-resolved commit.

## Frozen S1 condition

- Verified and pinned five public model and tokenizer revisions.
- Recorded licenses, architectures, dtype, remote-code policy, chat-template hashes, and bytes.
- Froze immutable MMLU, GSM8K, and 27-task BBH revisions and deterministic 50-item subsets.
- Selected an explicit BBH zero-shot policy rather than reconstructing unsealed few-shot examples.
- Added prompt, subset, panel, requirements, and config hashes.

## Production path

- Added strict V6 configuration, dataset resolution, prompt rendering, exact model loading, workers,
  checkpoint identities, runner lifecycle, and deterministic packaging.
- Added isolated T4×2 LPT scheduling, heartbeats, bounded retries, crash/OOM/timeout
  classification, exact resume, and collision-free worker outputs.
- Made OOM input-length fallbacks effective in generation and recorded them per row and manifest.
- Added gold-blind MMLU/GSM8K/BBH extraction and task-aware scoring.
- Added the fail-closed S1 three-ZIP importer and post-import runtime recalibration.

## Notebooks and validation

- Rebuilt all six canonical notebooks as thin package clients with deterministic cell IDs.
- Validated fixture and mocked production run/resume/validate/package paths.
- Added environment, registry/config, scoring, gold isolation, scheduler, packaging, notebook, and
  S1 acceptance adversarial tests.
- Added a clean/native validation ledger, critical-module mypy pass, package build, paper build, and
  release dry run.

## Scientific closure

- Added family-cluster rank bootstrap and documented rejection of naive model bootstrap for fixed
  checkpoint ranks.
- Added held-out measurement validation, aggregate/additive baselines, calibration, uncertainty,
  regularization, family-deduplicated sensitivity, and synthetic recovery.
- Preserved null-dependent rank interpretation and the multidimensional validity profile.

No real S1 model inference, paid API call, or empirical result fabrication occurred.
