# ValidEval V6 Final Pre-S1 Handoff

## 1. Executive verdict

`CONTROLLED_GPU_SMOKE_READY`. The repository is ready for the first controlled Kaggle T4×2
engineering smoke. No real S1 inference was run. Remote T4 feasibility remains the intended subject
of S1, and all resulting artifacts remain `ENGINEERING_ONLY`.

## 2. Starting V5 state

V5 had reproduced the historical 39-model, 14,042-item, 57-subject MMLU matrix, corrected overclaims,
hardened historical import/release paths, and provided fixture notebooks. Study C remained blocked
because the notebooks had no real production runner and the S1 identities were not fully frozen.
The reviewed baseline is `f7bdfda1676995ffda356c15884a3d10cda6b80b`, tag
`valideval-v5-pre-execution`.

## 3. What V6 closed

V6 froze exact public model/tokenizer revisions, immutable datasets, 50-item subsets, prompt and
scoring contracts, BBH zero-shot/task policies, requirements, leakage hashes, and source identity.
It implemented the runner, two-process scheduler, model loader, gold boundary, atomic resume/merge,
deterministic packaging, notebooks, three-ZIP importer, acceptance gate, and runtime recalibration.

## 4. Production execution

The CLI is `python -m valideval run --config <frozen-yaml>`. Config/reference hashes and source tag
are validated before downloads. Two isolated processes receive deterministic LPT model assignments.
The exact checkpoint/tokenizer loads on `cuda:0` inside its restricted process; remote code and
`device_map="auto"` are not used.

Per-item records include raw/parsed/gold/scored stages, failure taxonomy, latency, load/generation/
extraction time, token counts, throughput, GPU, dtype, quantization, cache state, retries, resource
fallbacks, source/config/prompt/environment identity, and evidence class.

OOM recovery clears CUDA state and applies only recorded bounded resource reductions. This S1 does
not permit silent quantization or dtype changes. Checkpoint reuse requires exact identity; stale
partials fail closed.

## 5. Frozen panel and benchmarks

The exact model list and hashes are in `configs/panels/s1_smoke_exact_v6.yaml` and
`reports/v6/VALID_EVAL_V6_S1_MODEL_PANEL_FREEZE.md`. It has five checkpoints across three families,
so `scientific_panel_adequacy: false`.

MMLU uses 50 deterministic test items and controlled A-D answer generation. GSM8K uses 50
deterministic test items and an adversarially tested numeric parser. BBH uses 50 test items spanning
all 27 tasks with task-aware normalizers/scorers. BBH is explicitly zero-shot because the mirror did
not provide a sufficiently sealed few-shot provenance/license path.

## 6. Gold isolation and leakage

Only the scorer receives private gold. Renderer, generator, and extractor inputs are recursively
checked for gold-bearing fields. The locally testable leakage gate passed exact/normalized/
option-aware few-shot checks, unique IDs, cross-benchmark duplicate screening, prompt/config/path
label checks, and gold-boundary tests. This does not rule out model-pretraining contamination.

## 7. Merge, packaging, and acceptance

Every run emits:

```text
run_manifest.json
environment.json
models.json
benchmark_contract.json
config_snapshot.yaml
file_checksums.json
shard_status.json
failure_summary.csv
predictions.jsonl
matrix.csv
```

Merge rejects gaps, duplicates, contradictions, mixed benchmark/config/model/dataset identities,
and unexpected shards. ZIP creation rejects invalid manifests/checksums, secrets, caches, hidden or
temporary files, path traversal, and nested archives.

The importer requires the three exact ZIP names below and returns a single explicit acceptance or
rejection status. Accepted S1 is still `ENGINEERING_ONLY`.

## 8. Notebook validation

All six notebooks execute top-to-bottom in fixture mode. Mocked production traversed run, two-worker
scheduling, merge, package, resume, validate-only, and package-only. Real local preflight fails
before download without T4×2. The remote smoke was intentionally not simulated as an empirical
success.

## 9. Independent scientific closures

Historical rank materiality was rerun with 500 bootstraps, 500 additive-null simulations, and family
cluster sensitivity. The result is `RANK_MATERIALITY_ANALYSIS_READY`; interpretation remains
null-dependent, and no universal severity label was restored.

The regularized subject-conditioned measurement model passed held-out, baseline, calibration,
uncertainty, regularization, family-deduplicated, and synthetic-recovery checks. The result is
`MEASUREMENT_MODEL_PLAN_DEFENSIBLE`, with explicit limits on latent-trait and construct claims.

## 10. Provenance and validation

The final source ref is `valideval-v6-controlled-gpu-smoke-ready`. The runner resolves and records
its exact commit at execution. Full native and clean-environment command outcomes, warnings,
durations, environment details, staged-file audit, secret scan, build results, and any non-P0
limitations are in `reports/v6/VALID_EVAL_V6_VALIDATION_LEDGER.md` and
`VALID_EVAL_V6_MACHINE_STATE.json`.

## 11. Files

Added: V6 panels/contracts/run configs; freeze/leakage artifacts; runner/config/dataset/model/prompt/
worker/checkpoint/package/scoring/import/recalibration modules; notebook builder; rank/measurement
closure code and tests; requirements; twelve V6 reports; runbook; handoff; machine state.

Modified: CLI, execution exports/manifest/notebook/scheduler, measurement and rank utilities,
canonical notebooks, README, changelog, package version, ignore rules, and relevant tests.

## 12. Remaining non-P0 limitations

- Actual T4×2 load/throughput/disk behavior is unmeasured until S1.
- Model-pretraining contamination cannot be eliminated by these local guards.
- The BBH mirror does not declare a license; source redistribution remains hashes/metadata/output
  only pending independent terms confirmation.
- Five checkpoints across three families are not scientifically adequate.
- No S1 result has yet passed the importer.

## 13. Exact Kaggle handoff

Notebook order:

1. `00_valideval_t4x2_environment_and_preflight.ipynb`
2. `01_valideval_common_panel_mmlu_t4x2.ipynb`
3. `02_valideval_common_panel_gsm8k_t4x2.ipynb`
4. `03_valideval_common_panel_bbh_t4x2.ipynb`
5. `04_valideval_t4x2_merge_validate_package.ipynb`

Expected ZIPs:

```text
valideval_v6_s1_mmlu_s1-v6-mmlu.zip
valideval_v6_s1_gsm8k_s1-v6-gsm8k.zip
valideval_v6_s1_bbh_s1-v6-bbh.zip
```

Local commands:

```bash
python -m valideval accept-s1 \
  --input-dir kaggle_outputs/v6 \
  --output-root imported/v6
python -m valideval recalibrate-runtime \
  --input-root imported/v6 \
  --output results/planning/runtime_recalibration_v6.json
```

S2 is allowed only after an acceptance status, explicit failure review, and runtime recalibration.

## 14. Claims

Allowed after accepted S1: evidence consistent with this exact engineering pipeline loading,
generating, extracting, resuming, merging, and packaging on the recorded T4×2 condition.

Blocked after S1: scientific ranking, benchmark validity/invalidity, broad family comparison,
cross-benchmark construct equivalence, population generalization, and absence of contamination.

## 15. Final gates

```text
PROVENANCE_SEALED
PRODUCTION_RUNNER_READY
S1_EXACT_PANEL_FROZEN
S1_BENCHMARK_CONTRACTS_FROZEN
BBH_PROTOCOL_FROZEN
S1_LEAKAGE_GUARDS_COMPLETE
T4X2_SCHEDULER_READY
KAGGLE_NOTEBOOKS_PRODUCTION_PATH_VALIDATED
S1_IMPORT_AND_ACCEPTANCE_READY
RANK_MATERIALITY_ANALYSIS_READY
MEASUREMENT_MODEL_PLAN_DEFENSIBLE
CONTROLLED_GPU_SMOKE_READY
```

Exact next action: follow `VALID_EVAL_V6_CONTROLLED_GPU_SMOKE_RUNBOOK.md`, starting with notebook 00,
and return the three untouched ZIPs.
