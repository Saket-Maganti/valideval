# ValidEval V5 Kaggle T4×2 Notebook Audit

Audit date: 2026-07-16  
Evidence boundary: no Kaggle launch, no model download, no real benchmark inference  
Fixture state: `NON_EVIDENCE_FIXTURE`

## Verdict

`NOTEBOOK_FIXTURE_VALIDATED_REAL_EXECUTION_PATH_BLOCKED`

The six canonical notebooks are structurally valid and execute top-to-bottom in deterministic fixture mode. The shared scheduler, resume, merge, and fixture packaging paths are tested. They do not yet contain a real controlled model/dataset execution path, so `NOTEBOOK_PRODUCTION_READY` is not warranted.

## Canonical suite

| Notebook | Stage | Fixture result | Non-fixture behavior |
|---|---|---|---|
| `00_valideval_t4x2_environment_and_preflight.ipynb` | environment | Writes deterministic environment fixture | Writes a configuration-required preflight |
| `01_valideval_common_panel_mmlu_t4x2.ipynb` | MMLU | Builds a 2-model, 4-item fixture run | Writes a configuration-required preflight |
| `02_valideval_common_panel_gsm8k_t4x2.ipynb` | GSM8K | Builds a 2-model, 4-item fixture run | Writes a configuration-required preflight |
| `03_valideval_common_panel_bbh_t4x2.ipynb` | BBH | Builds a 2-model, 4-item fixture run | Writes a configuration-required preflight |
| `04_valideval_t4x2_merge_validate_package.ipynb` | merge/package | Builds deterministic fixture ZIPs | Can validate/package already completed run directories |
| `05_valideval_optional_robustness_runs_t4x2.ipynb` | robustness | Builds a labeled MMLU robustness fixture | Writes a configuration-required preflight |

Every notebook advertises the required modes: `fixture`, `smoke`, `pilot`, `minimum_scientific`, `full_common_panel`, `robustness`, `resume`, `validate_only`, and `package_only`. Outside fixture/validate/package modes, `run_notebook_stage` currently returns `CONTROLLED_GPU_EXECUTION_CONFIG_REQUIRED`; it does not load a benchmark, load a real checkpoint, generate outputs, or score them.

## Tested properties

- All six files parse as notebook v4 JSON.
- All code cells compile.
- With `nbclient` available, each notebook executes in a fresh kernel from the repository root in fixture mode.
- Fixture outputs are labeled `NON_EVIDENCE_FIXTURE`.
- No embedded token assignment, `trust_remote_code=True`, or `device_map="auto"` shortcut appears in notebook code.
- Deterministic shards are assigned round-robin to two explicit workers.
- The process-worker path creates isolated worker status directories.
- Heartbeats, bounded retry, resume idempotence, and configuration-mismatch refusal are tested.
- OOM fallback records batch-size or sequence-length changes and does not silently change dtype or quantization.
- Merge removes identical duplicates and rejects contradictory duplicates.
- Fixture packaging uses stable ordering, timestamps, modes, and SHA-256 output hashes.

Command and result:

```text
python3 -m pytest -q tests/test_kaggle_notebooks_v5.py tests/test_t4x2_scheduler_v5.py tests/test_notebook_fixture_execution_v5.py
11 passed in 0.75s
```

## Requirement matrix

| Requirement | State | Evidence/limitation |
|---|---|---|
| Valid JSON, ordered cells, no hidden fixture state | `VERIFIED_FROM_PRIMARY_ARTIFACT` | Notebook parse/compile/fresh-kernel tests pass. |
| True one-worker-per-GPU scheduler | `VERIFIED_FROM_PRIMARY_ARTIFACT` | Mock/process tests exercise GPU IDs `0` and `1`; no physical T4 was used. |
| Atomic checkpoints, heartbeats, resume, retries | `VERIFIED_FROM_PRIMARY_ARTIFACT` | Covered by scheduler tests. |
| Deterministic merge and package | `VERIFIED_FROM_PRIMARY_ARTIFACT` | Fixture merge/ZIP path tested. |
| Real MMLU/GSM8K/BBH loading and inference | `BLOCKED` | No real runner is connected to notebook stages. |
| Frozen package/model/dataset revisions | `PARTIAL` | Five public checkpoint revisions and all three dataset revisions are pinned; package versions, BBH few-shot hash, and real-loader verification remain blocked. |
| Resource profiles and quantization conditions | `PLANNED` | Scheduler records conditions; real profiles are not calibrated. |
| T4×2 smoke on Kaggle | `BLOCKED` | Out of scope and not executed. |
| `NOTEBOOK_PRODUCTION_READY` | `BLOCKED` | Fixture success is insufficient for this label. |

## Security and provenance notes

Authentication is not embedded. The execution layer records model revision, dtype, quantization, environment hash, code revision, and failure type in the normalized prediction schema. The remaining real runner must source optional credentials from Kaggle secrets/environment variables, default external tracking off, prefer safetensors, and fail closed on any unallowlisted remote-code requirement.

## Exact next action

Freeze the BBH few-shot artifact and supported package set, connect each benchmark notebook stage to a real V5 runner that writes the full manifest bundle, then run S1 on Kaggle T4×2 with the five pinned checkpoints. Import the S1 ZIP with the V5 importer and require checksum, coverage, extraction-reliability, resume, and configuration-hash gates before promoting the suite to `NOTEBOOK_PRODUCTION_READY`.
