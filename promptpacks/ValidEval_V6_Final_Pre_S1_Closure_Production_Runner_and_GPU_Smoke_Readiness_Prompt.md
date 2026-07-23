# ValidEval V6 — Final Pre-S1 Closure, Production Runner, Leakage Seal, and Kaggle T4×2 Smoke-Readiness Master Prompt

## Mission

You are completing the **final pre-execution closure pass** on the ValidEval repository.

This is not another broad audit, paper-writing pass, or prompt-pack generation task. V5 already completed the historical evidence reconstruction, scientific claim cleanup, importer hardening, fixture notebooks, planning system, and execution handbook. Your job is to close every remaining blocker that prevents the first real controlled Kaggle T4×2 smoke run.

Work directly in the repository. Implement the missing production execution path, freeze the exact S1 protocol, close all locally testable leakage paths, validate the complete notebook-to-ZIP-to-import chain, repair the remaining rank and measurement-model gaps, seal provenance, and issue an honest final gate.

The only successful endpoint is:

```text
CONTROLLED_GPU_SMOKE_READY
```

If any mandatory condition remains unmet, the only acceptable endpoint is:

```text
CONTROLLED_GPU_SMOKE_BLOCKED
```

Do not invent intermediate success labels.

---

## Repository

Expected repository root:

```text
/Users/saketmaganti/Projects/Valideval
```

Read before modifying:

```text
VALID_EVAL_MAXIMUM_CEILING_PRE_EXECUTION_HANDOFF.md
VALID_EVAL_MAXIMUM_CEILING_EXECUTION_HANDBOOK.md
VALID_EVAL_V5_MACHINE_STATE.json
VALID_EVAL_V5_REPAIR_CHANGELOG.md
reports/v5/
configs/
src/valideval/
tests/
kaggle_max_ceiling/
paper/
```

Treat the live repository, primary artifacts, test outputs, exact configs, and immutable hashes as the sources of truth.

---

# 1. Known starting state to verify

Independently verify every item below before relying on it:

1. Historical HELM-derived MMLU matrix:
   - 39 models;
   - 14,042 items;
   - 57 subjects;
   - 547,638 rows;
   - zero missing model-item cells;
   - zero contradictory duplicates;
   - byte-identical reconstructed matrix.

2. The old `rank range >= 10 = severe` interpretation is retired.

3. The legacy diagnostic-family “ablation” is contradicted because variants reused accuracy-derived values and must not be restored.

4. MMLU-Redux item-level validation is retired unless item identity is later confirmed.

5. V5 reportedly achieved:
   - 305 passed;
   - 0 failed;
   - 0 skipped;
   - two known constant-input warnings;
   - Ruff lint/format pass;
   - targeted MyPy pass;
   - package build pass;
   - paper build pass;
   - release validation pass.

6. Notebook fixture execution requires installing the package first.

7. The real production runner is absent or intentionally blocked in non-fixture modes.

8. The exact controlled S1 panel currently contains five public checkpoints across three nominal families and is engineering-only.

9. BBH few-shot content and hash are not fully frozen.

10. The S1 leakage gate is open because the real generation, extraction, scoring, and frozen-data path is not sealed.

11. Git provenance may still be unborn or incomplete.

12. Current overall state is:

```text
PRE_EXECUTION_BUILD_PARTIAL
```

Record any contradiction.

---

# 2. Hard boundaries

## 2.1 Do not run the real study

Do not execute:

- full controlled MMLU;
- full GSM8K;
- full BBH;
- S2 pilot;
- S3 minimum scientific panel;
- S4 full common panel;
- paid APIs;
- provider APIs;
- human annotation;
- external-label validation;
- confirmatory synthetic evidence;
- unapproved cloud jobs.

The user will run the S1 smoke after this pass.

Tiny deterministic fixtures and mocked model adapters are allowed. They must be labeled:

```text
NON_EVIDENCE_FIXTURE
```

## 2.2 Real production code is mandatory

The canonical notebooks must be able to call a real configuration-driven runner that can:

- load frozen benchmark data;
- load exact public model checkpoints;
- use two T4 GPUs through isolated workers;
- render prompts;
- generate or score outputs;
- parse answers without gold leakage;
- score correctness;
- record failures;
- checkpoint atomically;
- resume safely;
- merge shards;
- validate outputs;
- create manifests and checksums;
- package deterministic ZIPs.

Non-fixture modes must not remain placeholder returns such as:

```text
CONTROLLED_GPU_EXECUTION_CONFIG_REQUIRED
```

## 2.3 Never fake completion

Never:

- fabricate predictions;
- mix fixtures into real output paths;
- mark mocks as real inference;
- fabricate runtime measurements;
- replace failures with zero-valued answers;
- hide extraction failures as ordinary wrong answers;
- silently switch checkpoint, prompt, dtype, quantization, or dataset revision;
- close leakage gates based only on documentation;
- claim S1 is scientific evidence.

## 2.4 Preserve V5 scientific corrections

Do not restore:

- arbitrary “severe” rank labels;
- invalid legacy ablation claims;
- unconfirmed Redux validation;
- generic positive cross-benchmark gates;
- “panel validity” wording when the implementation only checks structural feasibility.

---

# 3. Exact required endpoint

The project must support this real sequence:

```text
clean checkout
→ clean environment install
→ local fixture validation
→ mocked production-path integration
→ notebook fixture execution
→ S1 config freeze
→ Kaggle T4×2 preflight
→ user executes five-checkpoint S1 smoke
→ deterministic output ZIP
→ local V6 import and acceptance
→ runtime recalibration
→ S2 go/no-go
```

Every step before remote inference must be complete, tested, documented, and fail-closed.

---

# 4. Phase A — Seal Git provenance

## 4.1 Inspect repository state

Record:

- `.git` presence;
- whether `HEAD` resolves;
- branch;
- commit SHA;
- dirty state;
- untracked files;
- ignored files;
- oversized files;
- secrets;
- raw-data redistribution risks.

## 4.2 If Git is unborn

Review `.gitignore` before staging. Exclude at minimum:

```text
.venv/
venv/
__pycache__/
.pytest_cache/
.mypy_cache/
.ruff_cache/
.DS_Store
.ipynb_checkpoints/
*.egg-info/
dist/
build/
model caches
Hugging Face caches
Kaggle working directories
secrets and token files
temporary ZIPs
large transient caches
```

Do not use `git add .` blindly.

Create a staged-file audit and secret scan. If safe, create:

```bash
git commit -m "Seal ValidEval V5 pre-execution baseline"
git tag valideval-v5-pre-execution
```

If Git identity is unavailable, write exact commands and mark provenance partial; continue all independent work.

## 4.3 V6 completion commit

After all V6 gates pass, create:

```text
Complete ValidEval V6 controlled GPU smoke readiness
```

and tag:

```text
valideval-v6-controlled-gpu-smoke-ready
```

Do not create the success tag if the final gate is blocked.

Record the final SHA in frozen configs, manifests, machine state, and runbook.

Create:

```text
reports/v6/VALID_EVAL_V6_REPOSITORY_AND_PROVENANCE_SEAL.md
```

---

# 5. Phase B — Clean installation and Kaggle environment

Make this canonical local path pass:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
python -m pytest -q
```

Create or repair:

```text
requirements-kaggle-t4x2-v6.txt
```

Pin or constrain compatible versions for:

- PyTorch;
- Transformers;
- Accelerate;
- Datasets;
- Tokenizers;
- Safetensors;
- SentencePiece;
- BitsAndBytes if used;
- NumPy;
- Pandas;
- PyArrow;
- Pydantic;
- TQDM;
- notebook execution tools.

Avoid unbounded `pip install -U`.

The notebooks must support a reproducible package path:

1. preferred: install the local source bundle uploaded as a Kaggle dataset or ZIP;
2. fallback: clone/download an immutable commit and install it.

Every notebook preflight must verify:

- package import;
- source commit;
- schema version;
- config hash;
- CUDA availability;
- visible GPU count;
- disk space;
- dependency versions.

Fail before model downloads when invalid.

---

# 6. Phase C — Freeze the exact S1 model panel

Verify every proposed model against its official source:

- repository exists;
- public access;
- immutable revision;
- tokenizer and model files available;
- architecture supported;
- license recorded;
- `trust_remote_code` requirement;
- T4 feasibility;
- dtype;
- quantization fallback;
- chat template;
- estimated download size.

Expected candidates may include:

```text
Qwen2.5-0.5B-Instruct
Qwen2.5-1.5B-Instruct
Qwen2.5-3B-Instruct
Phi-3-mini-4k-instruct
TinyLlama-1.1B-Chat
```

Do not assume names or revisions are correct. Verify them.

Exclude gated checkpoints from S1.

Create:

```text
configs/panels/s1_smoke_exact_v6.yaml
results/freeze/s1_model_registry_hash_v6.json
reports/v6/VALID_EVAL_V6_S1_MODEL_PANEL_FREEZE.md
```

Required panel fields:

```text
panel_id
study_id
evidence_class
scientific_panel_adequacy
canonical_model_id
repository
revision
family
parameter_count
dtype
quantization
quantization_fallback
max_memory
trust_remote_code
chat_template_policy
license
expected_t4_feasibility
expected_download_size
```

Required declarations:

```text
evidence_class: ENGINEERING_ONLY
scientific_panel_adequacy: false
```

Hash the frozen panel config.

---

# 7. Phase D — Freeze benchmark, subset, prompt, and scoring contracts

Create complete S1 contracts for MMLU, GSM8K, and BBH.

## 7.1 MMLU

Freeze:

- dataset source;
- immutable revision;
- split;
- deterministic stratified S1 subset;
- represented subjects;
- item-ID construction;
- prompt template;
- option ordering;
- zero-shot/few-shot policy;
- scoring method;
- extraction version;
- expected item count.

Do not select the first N rows. Use a deterministic stratified sample.

Ensure no target item appears in few-shot material.

## 7.2 GSM8K

Freeze:

- dataset source and revision;
- split;
- deterministic S1 subset;
- zero-shot/few-shot policy;
- chain-of-thought/rationale policy;
- generation limits;
- final-answer parser;
- numeric normalization;
- invalid-output policy.

Parser tests must cover:

- integers;
- negatives;
- commas;
- decimals;
- fractions where valid;
- currency symbols;
- units;
- multiple numbers;
- boxed answers;
- common final-answer phrases;
- refusal;
- empty output;
- truncation.

The parser must not receive gold.

## 7.3 BBH

Resolve the incomplete BBH protocol.

Freeze:

- exact task list;
- dataset revision;
- deterministic S1 subset per task;
- task-specific prompts;
- few-shot examples or an explicitly versioned zero-shot policy;
- few-shot source and provenance;
- few-shot IDs;
- target/few-shot exclusion checks;
- few-shot content hash;
- scoring rules;
- subtask-preserving item IDs;
- expected counts.

If few-shot licensing or provenance cannot be resolved, use a defensible zero-shot S1 protocol. Do not leave a partially frozen few-shot condition.

## 7.4 Required files

Create:

```text
configs/benchmarks/mmlu_s1_v6.yaml
configs/benchmarks/gsm8k_s1_v6.yaml
configs/benchmarks/bbh_s1_v6.yaml
results/freeze/s1_prompt_and_dataset_hashes_v6.json
reports/v6/VALID_EVAL_V6_BENCHMARK_AND_PROMPT_FREEZE.md
```

Every prompt condition must be reproducible from a versioned template and config.

---

# 8. Phase E — Implement the production runner

Replace the current production-mode blocker with a real configuration-driven execution system.

Provide a canonical entry point, preferably:

```bash
python -m valideval run --config configs/runs/<run>.yaml
```

Support modes:

```text
fixture
smoke
pilot
minimum_scientific
full_common_panel
robustness
resume
validate_only
package_only
```

## 8.1 Required lifecycle

The runner must:

1. parse and validate config;
2. resolve exact model identities;
3. resolve benchmark contracts;
4. verify source commit and config hash;
5. create the run directory atomically;
6. write frozen config snapshots;
7. build deterministic shards;
8. launch one worker per visible GPU;
9. assign model-shard jobs;
10. load pinned model revisions;
11. load pinned dataset revisions;
12. render prompts;
13. generate or score outputs;
14. parse predictions without gold access;
15. score with a separate gold-aware scorer;
16. record latency, tokens, and failures;
17. write atomic shard outputs;
18. update heartbeats/status;
19. resume only exact matching configurations;
20. apply bounded retries;
21. merge shards deterministically;
22. validate coverage and integrity;
23. write manifests/checksums;
24. package deterministic ZIP;
25. return a precise terminal state.

## 8.2 Required terminal states

At minimum:

```text
RUN_COMPLETE
RUN_COMPLETE_WITH_RECORDED_FAILURES
RUN_INCOMPLETE_RETRYABLE
RUN_INCOMPLETE_FATAL
CONFIG_MISMATCH
DATASET_RESOLUTION_FAILURE
MODEL_RESOLUTION_FAILURE
INSUFFICIENT_DISK
INSUFFICIENT_GPU
PACKAGE_VALIDATION_FAILURE
```

## 8.3 Suggested modules

Use existing V5 modules where possible. Add or consolidate only as needed:

```text
src/valideval/execution/runner.py
src/valideval/execution/config.py
src/valideval/execution/models.py
src/valideval/execution/datasets.py
src/valideval/execution/prompts.py
src/valideval/execution/workers.py
src/valideval/execution/checkpoints.py
src/valideval/execution/packaging.py
src/valideval/benchmarks/mmlu_runner.py
src/valideval/benchmarks/gsm8k_runner.py
src/valideval/benchmarks/bbh_runner.py
src/valideval/scoring/mmlu.py
src/valideval/scoring/gsm8k.py
src/valideval/scoring/bbh.py
```

Avoid duplicate architectures.

Create:

```text
reports/v6/VALID_EVAL_V6_PRODUCTION_RUNNER_IMPLEMENTATION.md
```

---

# 9. Phase F — True T4×2 scheduler

Implement one isolated process per GPU:

```text
worker 0 → CUDA_VISIBLE_DEVICES=0
worker 1 → CUDA_VISIBLE_DEVICES=1
```

Do not rely on `device_map="auto"` as the only parallelism mechanism.

Support:

- model-level jobs;
- shard-level jobs;
- deterministic assignment;
- longest-estimated-job-first where useful;
- isolated worker output directories;
- no concurrent file collisions;
- worker heartbeats;
- bounded retries;
- coordinator restart recovery;
- single-GPU fallback only when allowed by config.

Each worker must record:

```text
worker_id
gpu_id
current_job
start_time
heartbeat
last_completed_item
retry_count
memory_failure
exit_state
```

Adversarially test:

- two healthy workers;
- one worker crash;
- OOM;
- stale heartbeat;
- duplicate assignment;
- coordinator interruption;
- resume;
- single-GPU fallback;
- output collision prevention.

Create:

```text
reports/v6/VALID_EVAL_V6_T4X2_SCHEDULER_VALIDATION.md
```

---

# 10. Phase G — Model loading and OOM safety

Load exact revisions.

Default:

```text
trust_remote_code: false
```

Allow only registry-approved exceptions.

Record:

- revision;
- dtype;
- quantization;
- tokenizer revision;
- device;
- model cache path;
- remote-code status.

Before download:

- estimate required disk;
- inspect free space;
- fail early when insufficient.

Bounded OOM fallback:

1. reduce batch size;
2. unload and clear cache;
3. retry once;
4. use configured quantization fallback when allowed;
5. otherwise record OOM and continue remaining jobs.

Every fallback must change or be represented in the run condition/config hash. Never silently compare altered conditions as identical.

---

# 11. Phase H — Gold-isolated generation, extraction, and scoring

Enforce separate stages:

```text
public inference input
raw model output
parsed prediction
private gold answer
scoring result
```

API requirements:

- prompt renderer receives no gold;
- generator receives no gold;
- parser/extractor receives no gold;
- only scorer receives parsed prediction plus gold.

Add tests that intentionally attempt to leak gold and fail.

Failure taxonomy must distinguish:

```text
SUCCESS
MODEL_LOAD_FAILURE
OOM
TIMEOUT
GENERATION_FAILURE
EMPTY_OUTPUT
TRUNCATED_OUTPUT
EXTRACTION_FAILURE
INVALID_FORMAT
SCORING_FAILURE
DATASET_FAILURE
UNKNOWN_FAILURE
```

A parsed but incorrect answer is not an extraction failure.

## MMLU

Freeze one S1 scoring method:

- controlled answer generation; or
- option log-likelihood.

Document exact tokenization, option normalization, and parser behavior.

## GSM8K

Use a gold-blind numeric parser with adversarial tests.

## BBH

Use task-specific scorers. Do not reduce all BBH tasks to a single naive exact-match rule without task review.

---

# 12. Phase I — Atomic checkpointing, resume, merge, and packaging

## 12.1 Atomic outputs

Write temporary shard files and atomically rename only after complete flush and validation.

## 12.2 Resume

Resume only when all match:

- run ID;
- config hash;
- source commit;
- model revision;
- dataset revision;
- prompt hash;
- scorer version;
- extractor version;
- shard definition.

Refuse stale partial outputs.

## 12.3 Merge

Reject:

- missing shard;
- duplicate shard;
- contradictory row;
- mixed benchmark;
- mixed config hash;
- mixed model revision;
- mixed dataset revision;
- coverage gap;
- unexpected extra shard.

## 12.4 Required run artifacts

Every run must emit:

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
matrix.csv when applicable
```

## 12.5 Packaging

Create ZIP only when:

- all declared jobs have terminal states;
- coverage satisfies the S1 contract or allowed failures are explicit;
- manifests validate;
- checksums validate;
- no secret, model cache, nested archive, or temporary file is included.

Create deterministic descriptive names:

```text
valideval_v6_s1_mmlu_<run_id>.zip
valideval_v6_s1_gsm8k_<run_id>.zip
valideval_v6_s1_bbh_<run_id>.zip
```

---

# 13. Phase J — Canonical Kaggle notebooks

Update:

```text
kaggle_max_ceiling/00_valideval_t4x2_environment_and_preflight.ipynb
kaggle_max_ceiling/01_valideval_common_panel_mmlu_t4x2.ipynb
kaggle_max_ceiling/02_valideval_common_panel_gsm8k_t4x2.ipynb
kaggle_max_ceiling/03_valideval_common_panel_bbh_t4x2.ipynb
kaggle_max_ceiling/04_valideval_t4x2_merge_validate_package.ipynb
kaggle_max_ceiling/05_valideval_optional_robustness_runs_t4x2.ipynb
```

Each notebook must:

- install or locate the exact package;
- run environment preflight;
- print commit and package version;
- select a versioned config;
- validate frozen hashes;
- invoke tested package code;
- show dual-worker status;
- support resume;
- validate output;
- show exact ZIP path;
- print exact local import command.

Do not embed a second independent implementation in notebook cells.

Required validation:

- valid notebook JSON;
- no hidden-state dependency;
- top-to-bottom fixture execution;
- mocked production-mode integration;
- resume mode;
- validate-only mode;
- package-only mode;
- local real-mode preflight up to model download/inference.

Create:

```text
reports/v6/VALID_EVAL_V6_NOTEBOOK_PRODUCTION_VALIDATION.md
```

---

# 14. Phase K — Seal S1 leakage guards

Run and record:

- target/few-shot exact hash overlap;
- normalized text overlap;
- option-aware overlap;
- item-ID collision checks;
- cross-benchmark exact duplicate checks;
- near-duplicate candidate generation;
- prompt contamination checks;
- gold-boundary tests;
- output-path label leakage tests;
- config-field label leakage tests.

Create:

```text
results/leakage/s1_leakage_checks_v6.json
results/leakage/s1_overlap_candidates_v6.csv
reports/v6/VALID_EVAL_V6_S1_LEAKAGE_SEAL.md
```

Do not claim absence of model pretraining contamination. Record that as an unresolved external-validity limitation.

S1 leakage can pass only when all locally testable paths are closed.

---

# 15. Phase L — Close rank-materiality gaps

Do not rerun the whole V5 research program. Close only the remaining methodological gaps.

Implement or formally resolve:

- family-cluster bootstrap;
- model-bootstrap estimand or documented rejection;
- held-out evaluation of the subject-conditioned model;
- comparison against aggregate and additive baselines;
- family-deduplicated sensitivity;
- calibration;
- regularization sensitivity.

Preserve the conclusion that rank interpretation is null-dependent.

Do not restore an arbitrary universal severity label.

Create:

```text
reports/v6/MMLU_V6_RANK_MATERIALITY_CLOSURE.md
```

Issue one:

```text
RANK_MATERIALITY_ANALYSIS_READY
RANK_ANALYSIS_REQUIRES_REPAIR
RANK_FINDING_NOT_DEFENSIBLE
```

This work is scientifically independent of S1 but must be completed unless technically impossible.

---

# 16. Phase M — Measurement-model closure

Validate the selected subject-conditioned or hierarchical response model using:

- held-out performance;
- synthetic recovery;
- family-deduplicated sensitivity;
- regularization sensitivity;
- uncertainty;
- calibration;
- comparison with simple baselines.

Do not force a full 2PL merely for scope.

Issue one:

```text
MEASUREMENT_MODEL_PLAN_DEFENSIBLE
MEASUREMENT_MODEL_PLAN_LIMITED
MEASUREMENT_MODEL_REDESIGN_REQUIRED
```

Create:

```text
reports/v6/VALID_EVAL_V6_MEASUREMENT_MODEL_CLOSURE.md
```

---

# 17. Phase N — S1 importer and acceptance gate

Extend the V5 importer with S1-specific acceptance.

Require:

- expected five exact models or explicit allowed failures;
- expected benchmark and subset;
- matching config hash;
- matching source commit;
- matching model revisions;
- matching prompt hashes;
- valid checksums;
- no duplicates;
- no contradictory rows;
- failure summaries;
- declared coverage.

Return exactly one:

```text
S1_SMOKE_ACCEPTED
S1_SMOKE_ACCEPTED_WITH_RECORDED_MODEL_FAILURES
S1_SMOKE_REQUIRES_RERUN
S1_SMOKE_REJECTED_CONFIGURATION_MISMATCH
S1_SMOKE_REJECTED_DATA_INTEGRITY
S1_SMOKE_REJECTED_EXTRACTION_FAILURE
S1_SMOKE_REJECTED_INSUFFICIENT_COVERAGE
```

An accepted S1 remains:

```text
ENGINEERING_ONLY
```

Create:

```text
reports/v6/VALID_EVAL_V6_S1_IMPORT_ACCEPTANCE.md
```

---

# 18. Phase O — Runtime recalibration hook

Ensure S1 outputs record:

- model load time;
- examples per second;
- input tokens;
- output tokens;
- generation/scoring time;
- extraction time;
- GPU;
- dtype;
- quantization;
- retries;
- cache hit/miss.

Add a post-import command that recalibrates S2–S4 runtime ranges from S1.

Do not claim exact runtime before S1 measurements.

---

# 19. Phase P — Required adversarial tests

Add tests for all of the following.

## Environment

- package absent;
- wrong version;
- missing dependency;
- wrong schema;
- wrong commit;
- insufficient disk;
- zero GPU;
- one GPU;
- two GPUs.

## Registry/model

- unknown model;
- missing revision;
- gated model;
- unsafe remote code;
- unsupported architecture;
- tokenizer mismatch;
- OOM fallback.

## Dataset/protocol

- wrong revision;
- missing split;
- duplicate item ID;
- target/few-shot overlap;
- subtask collision;
- prompt hash mismatch.

## Execution

- two healthy workers;
- worker crash;
- coordinator crash;
- OOM;
- timeout;
- empty output;
- truncation;
- extraction failure;
- retry exhaustion;
- stale heartbeat.

## Resume

- exact match;
- config mismatch;
- commit mismatch;
- model revision mismatch;
- prompt mismatch;
- stale partial output;
- completed shard reuse.

## Merge/package

- missing shard;
- duplicate shard;
- contradictory row;
- mixed benchmark;
- mixed config;
- mixed revision;
- coverage gap;
- missing manifest;
- checksum mismatch;
- secret file;
- nested ZIP;
- model cache accidentally included;
- deterministic member list.

## Leakage

- gold passed to renderer;
- gold passed to extractor;
- target/few-shot overlap;
- diagnostic label exposed;
- path leaks class.

## Notebook

- fixture;
- mocked production;
- resume;
- validate-only;
- package-only.

---

# 20. Phase Q — Full validation chain

Run all applicable commands in both the native environment and at least one clean environment.

At minimum:

```bash
python -m pip install -e ".[dev]"
python -m pytest -q
ruff check .
ruff format --check .
mypy <critical V6 modules>
python -m build
python -m valideval doctor
python -m valideval --help
```

Also run:

- V5 evidence reproduction;
- V6 S1 leakage seal;
- S1 panel validation;
- benchmark contract validation;
- notebook JSON validation;
- fixture notebook execution;
- mocked production integration;
- scheduler adversarial tests;
- importer adversarial tests;
- S1 acceptance tests;
- deterministic package test;
- paper build;
- release dry run;
- secret scan;
- staged-file audit;
- machine-state generation.

Report:

- passed;
- failed;
- skipped;
- xfailed;
- warnings;
- duration;
- environment.

Do not report only a pass count.

---

# 21. Frozen V6 configs and artifacts

Create at minimum:

```text
configs/panels/s1_smoke_exact_v6.yaml
configs/benchmarks/mmlu_s1_v6.yaml
configs/benchmarks/gsm8k_s1_v6.yaml
configs/benchmarks/bbh_s1_v6.yaml
configs/runs/mmlu_s1_v6.yaml
configs/runs/gsm8k_s1_v6.yaml
configs/runs/bbh_s1_v6.yaml
requirements-kaggle-t4x2-v6.txt
results/freeze/s1_prompt_and_dataset_hashes_v6.json
results/freeze/s1_model_registry_hash_v6.json
results/freeze/s1_environment_hash_v6.json
```

Create reports:

```text
reports/v6/VALID_EVAL_V6_REPOSITORY_AND_PROVENANCE_SEAL.md
reports/v6/VALID_EVAL_V6_PRODUCTION_RUNNER_IMPLEMENTATION.md
reports/v6/VALID_EVAL_V6_S1_MODEL_PANEL_FREEZE.md
reports/v6/VALID_EVAL_V6_BENCHMARK_AND_PROMPT_FREEZE.md
reports/v6/VALID_EVAL_V6_S1_LEAKAGE_SEAL.md
reports/v6/VALID_EVAL_V6_T4X2_SCHEDULER_VALIDATION.md
reports/v6/VALID_EVAL_V6_NOTEBOOK_PRODUCTION_VALIDATION.md
reports/v6/VALID_EVAL_V6_S1_IMPORT_ACCEPTANCE.md
reports/v6/MMLU_V6_RANK_MATERIALITY_CLOSURE.md
reports/v6/VALID_EVAL_V6_MEASUREMENT_MODEL_CLOSURE.md
reports/v6/VALID_EVAL_V6_VALIDATION_LEDGER.md
reports/v6/VALID_EVAL_V6_REPAIR_CHANGELOG.md
```

Create final documents:

```text
VALID_EVAL_V6_CONTROLLED_GPU_SMOKE_RUNBOOK.md
VALID_EVAL_V6_FINAL_PRE_S1_HANDOFF.md
VALID_EVAL_V6_MACHINE_STATE.json
```

---

# 22. Controlled GPU smoke runbook

`VALID_EVAL_V6_CONTROLLED_GPU_SMOKE_RUNBOOK.md` must be copy-pasteable and self-contained.

Required sections:

1. Purpose and `ENGINEERING_ONLY` classification.
2. Required commit and tag.
3. Kaggle T4×2 selection.
4. Internet setting.
5. Required secrets—preferably none.
6. Package upload/install method.
7. Exact notebook order.
8. Exact run configs.
9. Exact five model revisions.
10. Exact frozen benchmark subsets.
11. Expected directories and ZIP names.
12. Runtime ranges with assumptions.
13. Download and disk ranges.
14. Resume instructions.
15. OOM fallback rules.
16. Failure interpretation.
17. Exact local download locations.
18. Exact local V6 import commands.
19. S1 acceptance commands.
20. Runtime recalibration command.
21. Stop/go rules for S2.
22. Claims not unlocked by S1.

---

# 23. Machine-readable state

Create:

```text
VALID_EVAL_V6_MACHINE_STATE.json
```

Required fields:

```text
generated_at
repository_root
baseline_commit
final_commit
baseline_tag
final_tag
git_dirty
environment
package_install
tests
lint
format
type_check
package_build
paper_build
notebook_fixture_execution
notebook_mocked_production_execution
production_runner
t4x2_scheduler
s1_model_panel
benchmark_contracts
bbh_protocol
gold_isolation
leakage_gate
importer_gate
s1_acceptance_gate
rank_materiality_gate
measurement_model_gate
controlled_gpu_smoke_gate
remaining_blockers
exact_next_commands
```

Use `null` rather than invented values.

---

# 24. Final gates

Issue every gate separately.

## Provenance

```text
PROVENANCE_SEALED
PROVENANCE_PARTIAL
PROVENANCE_BLOCKED
```

## Production runner

```text
PRODUCTION_RUNNER_READY
PRODUCTION_RUNNER_PARTIAL
PRODUCTION_RUNNER_BLOCKED
```

## S1 panel

```text
S1_EXACT_PANEL_FROZEN
S1_PANEL_PARTIAL
S1_PANEL_BLOCKED
```

## Benchmark contracts

```text
S1_BENCHMARK_CONTRACTS_FROZEN
S1_BENCHMARK_CONTRACTS_PARTIAL
S1_BENCHMARK_CONTRACTS_BLOCKED
```

## BBH

```text
BBH_PROTOCOL_FROZEN
BBH_PROTOCOL_PARTIAL
BBH_PROTOCOL_BLOCKED
```

## Leakage

```text
S1_LEAKAGE_GUARDS_COMPLETE
S1_LEAKAGE_GUARDS_PARTIAL
P0_LEAKAGE_REMAINS
```

## Scheduler

```text
T4X2_SCHEDULER_READY
T4X2_SCHEDULER_PARTIAL
T4X2_SCHEDULER_BLOCKED
```

## Notebooks

```text
KAGGLE_NOTEBOOKS_PRODUCTION_PATH_VALIDATED
KAGGLE_NOTEBOOKS_FIXTURE_ONLY
KAGGLE_NOTEBOOKS_BLOCKED
```

## Importer

```text
S1_IMPORT_AND_ACCEPTANCE_READY
S1_IMPORT_PARTIAL
S1_IMPORT_BLOCKED
```

## Rank analysis

```text
RANK_MATERIALITY_ANALYSIS_READY
RANK_ANALYSIS_REQUIRES_REPAIR
RANK_FINDING_NOT_DEFENSIBLE
```

## Measurement model

```text
MEASUREMENT_MODEL_PLAN_DEFENSIBLE
MEASUREMENT_MODEL_PLAN_LIMITED
MEASUREMENT_MODEL_REDESIGN_REQUIRED
```

## Final gate

Choose exactly one:

```text
CONTROLLED_GPU_SMOKE_READY
CONTROLLED_GPU_SMOKE_BLOCKED
```

`CONTROLLED_GPU_SMOKE_READY` requires all:

- production runner ready;
- exact public S1 panel frozen;
- all three benchmark contracts frozen;
- BBH protocol frozen;
- gold-isolation tests pass;
- S1 leakage guards complete;
- T4×2 scheduler ready;
- notebook production path validated through mocked integration;
- importer and S1 acceptance ready;
- clean install passes;
- complete tests pass;
- lint/format/build pass;
- provenance sealed, or a narrowly justified non-code blocker with exact commands;
- no P0 execution blocker remains.

---

# 25. Final handoff

Create:

```text
VALID_EVAL_V6_FINAL_PRE_S1_HANDOFF.md
```

Required structure:

1. Executive verdict.
2. Starting V5 state.
3. What V6 closed.
4. Production runner.
5. Exact S1 model panel.
6. MMLU contract.
7. GSM8K contract.
8. BBH protocol and few-shot decision.
9. Gold isolation.
10. Leakage seal.
11. T4×2 scheduling.
12. Model loading and OOM behavior.
13. Checkpoint, resume, and recovery.
14. Merge and packaging.
15. Notebook validation.
16. Import and S1 acceptance.
17. Rank-materiality closure.
18. Measurement-model closure.
19. Git provenance.
20. Tests, lint, type, and builds.
21. Files added and modified.
22. Remaining non-P0 limitations.
23. Exact Kaggle notebook order.
24. Exact ZIP names.
25. Exact local import commands.
26. S1 acceptance criteria.
27. S2 decision criteria.
28. Allowed claims.
29. Blocked claims.
30. Final gates.
31. Exact next action.

---

# 26. Final Codex response

Do not reply only with “finished.”

Report exactly:

```text
FINAL_VERDICT:
STARTING_GATE:
FINAL_GATE:
PRODUCTION_RUNNER_STATUS:
S1_EXACT_PANEL_STATUS:
MMLU_CONTRACT_STATUS:
GSM8K_CONTRACT_STATUS:
BBH_CONTRACT_STATUS:
BBH_FEWSHOT_STATUS:
GOLD_ISOLATION_STATUS:
LEAKAGE_STATUS:
T4X2_SCHEDULER_STATUS:
NOTEBOOK_STATUS:
IMPORTER_AND_S1_ACCEPTANCE_STATUS:
RANK_MATERIALITY_STATUS:
MEASUREMENT_MODEL_STATUS:
PROVENANCE_STATUS:
BASELINE_COMMIT:
FINAL_COMMIT:
TESTS:
LINT:
FORMAT:
TYPE_CHECK:
PACKAGE_BUILD:
PAPER_BUILD:
FILES_ADDED:
FILES_MODIFIED:
PRIMARY_REMAINING_LIMITATION:
SMOKE_RUNBOOK:
FINAL_HANDOFF:
MACHINE_STATE:
SHOULD_USER_LAUNCH_KAGGLE_NOW:
FIRST_NOTEBOOK:
EXPECTED_ZIP_FILES:
EXACT_NEXT_ACTION:
```

State plainly:

- whether the user should launch Kaggle now;
- the first notebook to run;
- the exact ZIP files to return;
- what S1 proves;
- what S1 does not prove.

---

# 27. Quality standard

The request is to fix the remaining issues “perfectly without mistakes.” Absolute perfection cannot be guaranteed in software or remote GPU environments.

Interpret the requirement as:

- no known unaddressed P0 defect;
- no silent fallback;
- no fabricated evidence;
- no hidden notebook state;
- no stale resume;
- no gold leakage;
- no S1 identity ambiguity;
- complete adversarial testing;
- exact versioning and hashing;
- conservative fail-closed gates;
- exact reproduction and continuation instructions.

Do not claim perfection. Demonstrate reliability through implementation, tests, provenance, and explicit failure behavior.

The task is complete only when the project is genuinely ready for the user’s first controlled five-checkpoint Kaggle T4×2 engineering smoke run.
