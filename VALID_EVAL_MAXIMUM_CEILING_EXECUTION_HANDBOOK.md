# ValidEval Maximum-Ceiling Execution Handbook

Authoritative V5 continuation document for `/Users/saketmaganti/Projects/Valideval`.

This handbook replaces old prompt packs for execution. It intentionally stops before real
benchmark, human-label, or external-label work. A build gate is not an empirical or venue gate.

## A. Current verified state

### Existing evidence

- `REPRODUCED`: the public HELM-derived Study H matrix has 39 models, 14,042 MMLU items,
  57 subjects, 547,638 unique rows, zero missing cells, and exact equality between the active and
  reconstructed matrices. Primary matrix SHA-256:
  `f85a0a44f3203de2863d86bf13b2c81d8e934ae4c07b826193b5e93a3fc86e74`.
- `REPRODUCED`: aggregate accuracy spread is 0.580188; raw subject-conditioned rank ranges have
  historical median 19 and maximum 30. These are descriptive, not proof of invalidity.
- `REPRODUCED`: the V5 tie-aware 500-bootstrap/500-null analysis is null-sensitive. Additive and
  empirical-Bayes nulls do not show the same exceedance as simpler subject-size/permutation nulls.
- `REPRODUCED`: the proxy-weighted ranking remains close to aggregate accuracy
  (Spearman 0.99798, Kendall 0.97841, maximum rank delta 2).

### Existing non-evidence

- Panel-power and runtime CSVs are `PLANNED` design aids.
- Notebook, importer, scheduler, human, and synthetic tests use `NON_EVIDENCE_FIXTURE` inputs.
- The five pinned Study C model revisions are definitions, not reproduced executions.
- The 0-candidate local GPQA-versus-one-MMLU-subject overlap scan is partial and is not evidence
  that the controlled benchmarks do not overlap.

### Repaired components

- Claim/evidence ledger; Study H/Study C separation; exact checkpoint registry; full versioned
  MMLU/GSM8K/BBH contracts; leakage/gold/label guards; rank null/materiality analysis;
  minimum-matrix adequacy terminology; transparent subject-conditioned decomposition;
  Redux fail-closed linker; T4x2 scheduler/fixtures; secure V5 importer; receipt-driven V5 router;
  cross-benchmark gate/analysis scaffold; blinded human components; synthetic isolation; CLI,
  CI, paper, forensics, and deterministic release surfaces.

### Blocked components

- Production model/dataset/scoring runner behind the notebook stages.
- BBH few-shot examples/hash and upstream redistribution review.
- Exact S3 roster: 5 checkpoints/3 nominal families are frozen versus a planning target of
  32/8.
- Full controlled split/cross-benchmark overlap audit.
- Family-cluster/model bootstrap completion and fitted cross-benchmark hierarchical interaction.
- Confirmatory synthetic generator/grid; integrated human pilot; confirmed Redux item identity.
- Any controlled cross-benchmark, human, external-validation, repair-success, or venue-readiness
  claim.

Current overall gate: `PRE_EXECUTION_BUILD_PARTIAL`.

## B. Execution dependency graph

```text
environment preflight
  -> fixture validation
  -> implement/freeze production runner + BBH few-shot hash
  -> S1 smoke
  -> import smoke
  -> runtime recalibration
  -> S2 pilot
  -> panel decision
  -> controlled MMLU
  -> GSM8K
  -> BBH
  -> cross-benchmark analysis
  -> optional robustness
  -> human pilot
  -> human full study
  -> external validation (only after confirmed identity)
  -> final paper
```

No arrow may be skipped. Importer success is not analysis success; analysis success is not paper
eligibility; paper compilation is not empirical readiness.

## C. Run classification

| Class | Meaning | Maximum evidence state before promotion |
|---|---|---|
| `E0_LOCAL_CPU_BUILD` | install, lint, tests, fixtures, paper/release build | engineering only |
| `E1_LOCAL_CPU_ANALYSIS` | recomputation from frozen existing artifacts | protocol-scoped reproduced evidence |
| `E2_KAGGLE_GPU_ENGINEERING_SMOKE` | 2–5 pinned small models, 10–50 items/benchmark | engineering only |
| `E3_KAGGLE_GPU_PILOT` | 4–8 exact models, 100–500 items/subtasks | exploratory |
| `E4_KAGGLE_GPU_MINIMUM_SCIENTIFIC` | power-selected S3 exact panel | confirmatory only after all gates |
| `E5_KAGGLE_GPU_FULL_COMMON_PANEL` | S4 family/scale-diverse full panel | confirmatory only after all gates |
| `E6_KAGGLE_GPU_ROBUSTNESS` | prompt/scoring/quantization sensitivity | sensitivity, never silently pooled |
| `E7_HUMAN_VALIDATION` | blinded pilot/full review | human evidence only after import/adjudication |
| `E8_OPTIONAL_CEILING_EXTENSION` | confirmed external labels or confirmatory synthetic study | protocol-specific |

## D. Required run table

The two keyed tables jointly contain every required field. `BLOCKED_UNTIL_S1` is preferable to a
fabricated runtime.

### D1. Scope and compute

| run_id | priority | mandatory_or_optional | scientific_question | benchmark | study | panel_tier | exact_models | model_count | item_count | subtasks | prompt_config | scoring_config | hardware | cpu_or_gpu | runtime opt/expected/cons | expected_storage | download_size | notebook_or_command | resume_supported |
|---|---:|---|---|---|---|---|---|---:|---:|---|---|---|---|---|---|---|---|---|---|
| `E0-V5-LOCAL-BUILD` | 0 | mandatory | Do all local integrity surfaces pass? | all/fixture | build | S0 | deterministic fixtures | 2 fixture | tiny | fixture | fixture contracts | fixture scorers | local Mac | CPU | measured in command ledger | <1 GB excluding existing data/build caches | none | `python3 scripts/run_v5_local_validation.py` | yes |
| `E1-MMLU-REPRO` | 0 | mandatory | Can Study H be reconstructed exactly? | MMLU | H | historical | 39 HELM aliases | 39 | 14,042 | 57 | historical HELM | historical HELM | local Mac | CPU | current-machine command ledger | about 0.5 GB derived | none | `python3 scripts/reproduce_mmlu_evidence_v5.py` | deterministic rerun |
| `E1-LEAKAGE-FORENSICS` | 0 | mandatory | Are available leakage/release surfaces bounded? | local available | H/build | n/a | n/a | n/a | available only | partial | V5 hashes | n/a | local Mac | CPU | uncalibrated 1–15 min | reports/CSV/JSON | none | leakage + forensics scripts | deterministic rerun |
| `E1-RANK-MATERIALITY` | 0 | mandatory | Is rank variation material beyond stated nulls? | MMLU | H | historical | 39 HELM aliases | 39 | 14,042 | 57 | historical | V5 tie/null protocol | local Mac | CPU | current-machine command ledger | up to about 1 GB | none | `python3 scripts/run_mmlu_rank_materiality_v5.py ...` | deterministic seed |
| `E2-S1-COMMON-SMOKE` | 1 | mandatory after runner repair | Do pinned models load, shard, resume, extract, and package? | MMLU+GSM8K+BBH | C | S1 | five pinned revisions below | 5 | 50 each benchmark | selected smoke rows | V5 contract primary | V5 contract primary | Kaggle T4x2 | GPU | 1.71/3.51/7.93 h total incl one cached download; `PLANNED_UNMEASURED` | output-row proxy 0.0031 GB plus logs/cache | 22.10 GB unique weight proxy | notebooks 00–04, mode `smoke` | required |
| `E2-S1-IMPORT` | 1 | mandatory | Are S1 artifacts intact and idempotent? | each S1 ZIP | C | S1 | manifest-defined | 5 | 750 planned rows | as run | n/a | V5 importer | local Mac | CPU | uncalibrated 1–10 min/ZIP | copied ZIP + normalized cache | none | `valideval validate-run`, `import-kaggle`, `post-import` | idempotent |
| `E3-S2-PILOT` | 2 | mandatory | What are runtime, OOM, extraction, and ability-spread risks? | all three | C | S2 | exact roster chosen after S1 | 4–8 | 100–500/benchmark | preregistered subset | frozen V5 | frozen V5 | Kaggle T4x2 | GPU | `BLOCKED_UNTIL_S1_CALIBRATION` | measured after S1 | measured after S1 | notebooks 01–04, mode `pilot` | required |
| `E4-S3-MMLU` | 3 | mandatory | Controlled knowledge-ranking/diagnostic result? | MMLU | C | S3 | roster not frozen | target 32 | 14,042 | exact 57 | `mmlu_mcq_zero_shot_v5.0` | `mmlu_exact_choice_v5.0` | Kaggle T4x2 or justified equivalent | GPU | `BLOCKED_UNTIL_S1/S2` | formula-based only | roster dependent | notebook 01, mode `minimum_scientific` | required |
| `E4-S3-GSM8K` | 3 | mandatory | Controlled mathematical-reasoning result? | GSM8K | C | S3 | same exact S3 roster | target 32 | 1,319 | main | `gsm8k_zero_shot_reasoning_v5.0` | `gsm8k_numeric_exact_v5.0` | Kaggle T4x2 or justified equivalent | GPU | `BLOCKED_UNTIL_S1/S2` | formula-based only | shared cache | notebook 02, mode `minimum_scientific` | required |
| `E4-S3-BBH` | 3 | mandatory | Controlled task-specific reasoning result? | BBH | C | S3 | same exact S3 roster | target 32 | 6,511 | exact 27 | `bbh_task_specific_v5.0` after hash freeze | `bbh_task_aware_exact_v5.0` | Kaggle T4x2 or justified equivalent | GPU | `BLOCKED_UNTIL_S1/S2` | formula-based only | shared cache | notebook 03, mode `minimum_scientific` | required |
| `E5-S4-FULL` | 4 | optional strong path | Does transfer survive broader family/scale diversity? | all three | C | S4 | roster not frozen | target 40 | full | all | frozen primary | frozen primary | GPU pool | GPU | `BLOCKED_UNTIL_S3` | formula-based only | roster dependent | notebooks 01–04, mode `full_common_panel` | required |
| `E6-ROBUSTNESS` | 5 | optional | Are conclusions stable to predeclared protocol changes? | selected | C | S5 | exact condition-matched models | TBD | preregistered subset/full | selected | frozen variants | condition-specific | Kaggle T4x2 | GPU | `BLOCKED_UNTIL_PRIMARY` | TBD | shared cache | notebook 05, mode `robustness` | required |
| `E7-HUMAN-PILOT` | 4 | mandatory for human pillar | Is blinding/rubric/control design workable? | sampled items | C | pilot | n/a | n/a | 30 tasks | frozen strata | blinded rubric | adjudication rubric | offline reviewers | HUMAN | calendar time not estimated | private packet/labels | none | human V5 scripts | packet hashes |
| `E7-HUMAN-FULL` | 5 | optional ceiling | What precision/enrichment is supported? | sampled items | C | full | n/a | n/a | planned 200, power-refrozen | frozen strata | blinded rubric | adjudicated | offline reviewers | HUMAN | calendar time not estimated | private labels/audit | none | human V5 scripts | packet hashes |
| `E8-REDUX-RESCUE` | 5 | optional | Do diagnostics transfer to confirmed external issues? | MMLU-Redux | H/C explicit | n/a | n/a | n/a | only confirmed rows | n/a | confirmed-only metrics | CPU | CPU/HUMAN | `BLOCKED_ON_IDENTITY` | sanitized linkage only | none | `scripts/resolve_mmlu_redux_v5.py` | deterministic |
| `E8-SYNTH-CONFIRM` | 5 | optional ceiling | Do fixed diagnostics recover decoupled flaws? | synthetic | confirmatory | frozen config | simulator panel | 16 planned | 1,000/condition × 5 seeds | frozen grid | hidden generator | frozen metric/threshold | CPU/GPU TBD | TBD | `BLOCKED_ON_EXECUTOR` | TBD | none | synthetic V5 runner after implementation | required |

Pinned S1 checkpoint revisions:

- `Qwen/Qwen2.5-0.5B-Instruct@7ae557604adf67be50417f59c2c2f167def9a775`
- `Qwen/Qwen2.5-1.5B-Instruct@989aa7980e4cf806f80c7fef2b1adb7bc71aa306`
- `Qwen/Qwen2.5-3B-Instruct@aa8e72537993ba99e69dfaafa59ed015b17504d1`
- `microsoft/Phi-3-mini-4k-instruct@f39ac1d28e925b323eae81227eaba4464caced4e`
- `TinyLlama/TinyLlama-1.1B-Chat-v1.0@fe8a4ea1ffedaf415f4da2f062534de366a451e6`

### D2. Dependencies, gates, and claims

| run_id | dependencies | outputs | acceptance_gate | failure_conditions | fallback | analyses_unlocked | claims_unlocked | claims_not_unlocked |
|---|---|---|---|---|---|---|---|---|
| `E0-V5-LOCAL-BUILD` | current source | command ledger, paper PDF, releases, forensics | every command exit 0 | any failed test/lint/type/build/package gate | repair locally; never weaken gate | fixture plumbing | none empirical | all scientific claims |
| `E1-MMLU-REPRO` | frozen primary input hash | reproduction JSON/CSV/matrix | exact hashes/labels/values, no conflicts/missingness | hash drift, duplicates, coverage mismatch | stop and reconcile source | Study H descriptive analysis | protocol-scoped reproduction | global validity, controlled execution |
| `E1-LEAKAGE-FORENSICS` | local artifacts | leakage/forensic reports and queues | no unresolved release secret; all available guards pass | gold/label leakage, unsafe release member | repair code/artifact; rerun | local audit only | bounded implementation statements | no-contamination claim |
| `E1-RANK-MATERIALITY` | reproduced matrix/family map | rank/null/measurement artifacts | deterministic rerun; nulls and limitations reported | result drift, missing null, post-hoc threshold | block paper result | Study H rank profile | null-conditional wording | “severe,” global invalidity |
| `E2-S1-COMMON-SMOKE` | production runner, BBH hash, E0 | per-run manifest bundle + ZIPs | complete checksums/shards; ≥.95 extraction; full planned coverage; no identity drift | OOM, loader drift, retry/config mismatch, leakage | reduce batch/length only; record fallback; exclude failed model if identity preserved | runtime/extraction calibration | engineering only | accuracy/transfer/paper claims |
| `E2-S1-IMPORT` | S1 ZIP/hash | canonical receipts, dry-run route | adversarial validator pass; identical reimport idempotent | checksum/schema/count/conflict failure | repair runner and rerun S1 | S2 planning commands | none empirical | importer pass ≠ scientific pass |
| `E3-S2-PILOT` | accepted S1/recalibrated plan | pilot ZIPs/receipts/feasibility report | stable loading, acceptable failures/coverage, informative spread | repeated OOM, family collapse, extraction <.95 | change roster or preregister controlled quantization; rerun pilot | S3 roster decision | exploratory feasibility only | confirmatory transfer |
| `E4-S3-*` | accepted S2; exact 32/8 roster; prereg freeze | full benchmark matrices/receipts | complete exact panel, data integrity, overlap/leakage, uncertainty gates | missing model/item, identity/config drift, P0 leakage | rerun affected shards; do not impute silently | controlled within/cross analyses | benchmark-specific confirmatory claims after analysis | universal transfer/global validity |
| `E5-S4-FULL` | successful S3 | broader matrices/receipts | same gates plus family balance | same plus dominance/feasibility | retain S3 as primary; label S4 incomplete | stronger sensitivity | broader conditional claims | representativeness beyond roster |
| `E6-ROBUSTNESS` | frozen primary complete | condition-separated artifacts | no silent pooling; exact condition identity | condition drift/incomplete pairs | report missing sensitivity | robustness tables | sensitivity-qualified claims | replacement of primary result |
| `E7-HUMAN-PILOT` | licensed frozen frame/controls/ethics decision | private labels/control/agreement/adjudication | control threshold, ≥2 labels/task, hash/integrity, exclusions frozen | failed controls, unblinding, low expertise/agreement | repair rubric; new blinded pilot | full-study decision | protocol feasibility | benchmark issue prevalence/recall |
| `E7-HUMAN-FULL` | passed pilot/refrozen power | private adjudicated endpoints | ≥3 labels/task, controls, exclusions, uncertainty | integrity/control/adjudication failure | report blocked/inconclusive | human precision/enrichment | sample-supported endpoints | recall from high-score-only sample |
| `E8-REDUX-RESCUE` | canonical shared IDs/text and lawful use | confirmed linkage + metrics | confirmed-only rows, collision/manual review resolved | structural/index-only linkage | retire external pillar | external validation | issue-specific transfer if supported | current 0/370 claim |
| `E8-SYNTH-CONFIRM` | implemented frozen executor | all seeds/null/heldout/ablation artifacts | freeze hash, hidden boundary, all planned lanes and intervals | threshold leakage, missing seed/lane, truth exposure | invalidate and rerun from clean freeze | synthetic validation | fixed-protocol recovery if supported | real-benchmark validity |

## E. CPU runs

The local command ledger is now available, but the ranges below remain deliberately broad
`PLANNED_UNCALIBRATED` operator windows rather than portable performance claims or scientific
findings.

| CPU operation | Command/surface | Planning window | Promotion rule |
|---|---|---:|---|
| MMLU reproduction | `scripts/reproduce_mmlu_evidence_v5.py` | 0.1–5 min | exact hashes/matrix required |
| Leakage audit | `scripts/build_leakage_audit_v5.py` | 0.1–5 min | partial until full inputs exist |
| Duplicate/release scan | `scripts/build_repository_forensics_v5.py` | 0.5–15 min | no unresolved release-secret hit |
| Null simulations | rank script, 500 primary + robustness nulls | 1–20 min | all nulls reported |
| Bootstrap | rank script, 500 | 1–20 min | fixed seed/protocol |
| Hierarchical analysis | rank/measurement output | 0.1–10 min | exploratory only until held-out checks |
| Import | `valideval import-kaggle` | 0.1–10 min per S1 ZIP | integrity/coverage/identity pass |
| Cross-benchmark analysis | `valideval cross-benchmark --execute` | 0.1–30 min | exact-overlap gate first |
| Paper assets | `valideval build-paper-assets` | 0.1–2 min | placeholders preserved for blocked results |
| Paper compilation | BibTeX + three pdflatex passes | 0.1–3 min | exit 0; no undefined required input |
| Release build | `valideval build-release ... --build` | 0.1–10 min/profile | allowlist audit; no raw/cache/secret |

Use `results/v5_validation/command_ledger_v5.json` for actual current-machine durations after the
validation chain. Do not reuse those wall times as GPU throughput estimates.

## F. GPU runs

Current permission is **fixture only**. The following S1 plan becomes executable only after the
production runner and BBH few-shot freeze blockers are closed.

| Notebook | Mode | Models | Benchmark/items | Planned wall time incl one-cache download | Retry | Storage/download | Expected ZIP |
|---|---|---|---|---|---|---|---|
| 01 | `smoke` | pinned 5 | MMLU, 50 each | part of 1.71/3.51/7.93 h total | max 1/task | output proxy + shared 22.10 GB weights | `study-c-s1-mmlu-v5.zip` |
| 02 | `smoke` | pinned 5 | GSM8K, 50 each | same total | max 1/task | same shared cache | `study-c-s1-gsm8k-v5.zip` |
| 03 | `smoke` | pinned 5 | BBH, 50 each | same total | max 1/task | same shared cache | `study-c-s1-bbh-v5.zip` |
| 04 | `package_only` | n/a | completed S1 runs | CPU packaging only | none | deterministic ZIPs | names above |

The numeric range is `PLANNED/UNMEASURED_ASSUMPTIONS` from 15 model-benchmark scenarios using
20/12/6 tokens/s/GPU, 0.8 dual-GPU utilization, token proxies, and one cached model download.
Replace it immediately after S1. No S2–S5 wall time is defensible yet.

## G. Exact Kaggle instructions

### Current safe fixture validation

1. Create a Kaggle notebook and select **GPU T4 x2** under Accelerator.
2. Attach a source snapshot containing this repository. Do not attach raw private labels or
   secrets as ordinary datasets.
3. Internet may be on only for bounded package installation; no provider or paid API is used.
4. If the source is the working directory, set `VALIDEVAL_INSTALL_EDITABLE=1`. Install only
   `.[notebooks]`; do not use unbounded `pip install -U`.
5. Set:

   ```python
   import os
   os.environ["VALIDEVAL_EXECUTION_MODE"] = "fixture"
   os.environ["VALIDEVAL_NOTEBOOK_OUTPUT_ROOT"] = "/kaggle/working/kaggle_max_ceiling_outputs"
   os.environ["VALIDEVAL_INSTALL_EDITABLE"] = "1"
   ```

6. Run notebook 00, then 01, 02, 03, 04, and optionally 05 top-to-bottom. No source cell needs
   editing; change only environment configuration before imports.
7. Expect `KAGGLE_T4X2_FIXTURE_VALIDATED` and three fixture ZIPs under
   `kaggle_max_ceiling_outputs/packages/`. They are never evidence.

### Future S1 after the local repair gate

Do not follow this subsection until `run_notebook_stage` has a tested real path and the local
gate says `CONTROLLED_GPU_SMOKE_READY`.

1. Keep T4x2 selected. Attach/fetch the exact dataset revisions in the benchmark contracts and
   the five pinned public model revisions. Gemma is excluded.
2. Public models require no embedded token. If an HF token is later needed, store `HF_TOKEN` in
   Kaggle Secrets and read it from the environment; never paste it into a cell or output.
3. Set external tracking disabled. Do not enable `trust_remote_code` unless the registry entry is
   explicitly allowlisted and the code revision is recorded.
4. Set `VALIDEVAL_EXECUTION_MODE=smoke`, output root as above, and the frozen execution config
   path required by the repaired runner. Use 50 items per benchmark and the five pinned revisions.
5. Run 00 first; stop on package/version/device/cache failure. Run 01–03 independently. Run 04 in
   `validate_only`, then `package_only`. Notebook 05 is not part of S1.
6. Download the three ZIPs and their displayed SHA-256 values to:

   ```text
   /Users/saketmaganti/Projects/Valideval/kaggle_outputs/v5/
   ```

7. Never rename a ZIP without recording the original name/hash. Expected convention:
   `study-c-s1-{mmlu,gsm8k,bbh}-v5.zip`.

## H. Exact local import commands

Run from the repository root after copying S1 ZIPs:

```bash
python3 -m valideval validate-run kaggle_outputs/v5 --expected-study study-c-s1 --strict

python3 -m valideval import-kaggle \
  --input-dir kaggle_outputs/v5 \
  --output-root imported/v5 \
  --cache-root cache/v5 \
  --results-root results/imported_v5 \
  --expected-study study-c-s1 \
  --strict

python3 -m valideval post-import \
  --import-root imported/v5 \
  --output results/post_import_v5 \
  --minimum-extraction-reliability 0.95 \
  --minimum-coverage 1.0 \
  --strict
```

After all three exact controlled matrices and receipts pass:

```bash
python3 -m valideval cross-benchmark \
  --matrix mmlu=cache/v5/mmlu/matrix.csv \
  --matrix gsm8k=cache/v5/gsm8k/matrix.csv \
  --matrix bbh=cache/v5/bbh/matrix.csv \
  --metadata mmlu=imported/v5/mmlu/import_receipt_v5.json \
  --metadata gsm8k=imported/v5/gsm8k/import_receipt_v5.json \
  --metadata bbh=imported/v5/bbh/import_receipt_v5.json \
  --output results/cross_benchmark_v5 \
  --execute
```

Paper/reviewer/final validation:

```bash
python3 -m valideval build-evidence-ledger
python3 -m valideval build-paper-assets
(cd paper/v5 && pdflatex -interaction=nonstopmode -halt-on-error main.tex && \
  bibtex main && \
  pdflatex -interaction=nonstopmode -halt-on-error main.tex && \
  pdflatex -interaction=nonstopmode -halt-on-error main.tex)
python3 -m valideval build-release --profile reviewer --build
python3 scripts/run_v5_local_validation.py
```

Paths shown for imported matrices/receipts are the required convention for the production runner;
verify actual receipt paths before `--execute`. The cross command must fail closed if they differ.

## I. Stop/go gates

| Stage | Proceed when | Rerun/repair when | Abort evidence promotion when |
|---|---|---|---|
| E0 | all local commands exit 0 | code/docs/release drift | any integrity gate is weakened |
| S1 load | exact revision/config/hash match | transient download/load failure | checkpoint substitution or unrecorded remote code |
| S1 generation | all shards accounted for; resume idempotent | bounded task failure | gold/correctness reaches generation/retry |
| S1 extraction | reliability ≥0.95 and failures explicit | repair extractor and rerun all affected rows | gold-aware repair or failure silently scored wrong |
| S1 resources | no repeated OOM; fallbacks recorded | reduce batch/sequence length | silent quantization/dtype change |
| Import | checksums/schema/counts/identity/coverage pass | rebuild ZIP from same immutable run | conflict, traversal, tamper, partial coverage |
| S2 | runtime and spread support S3 decision | alter roster under a recorded new freeze | post-select models for favorable results |
| S3 | exact 32/8 target or newly justified preregistered target | rerun missing/failed shards | incomplete common panel or P0 overlap gap |
| Cross | exact-overlap gate passes | fix metadata/config mismatch | family name substituted for checkpoint identity |
| Human | blinding/controls/agreement/adjudication pass | revise rubric with new blinded pilot | unblinding, failed controls, fabricated/missing labels |
| External | stable/content identity confirmed | manual review collision queue | position-only linkage |
| Paper | each result maps to eligible artifact | replace placeholder after gate | build success used as evidence |

Panel reduction is allowed only for engineering feasibility and must create a new explicit tier or
protocol version. Quantization changes define a different condition; they are never silently pooled.

## J. Evidence promotion rules

| State | Required conditions |
|---|---|
| `ENGINEERING_ONLY` | Fixture or S1; manifest/checksum pass; no scientific estimand claimed. |
| `EXPLORATORY` | S2 or incomplete/non-preregistered analysis; exact limitations and selection history retained. |
| `CONFIRMATORY` | Frozen preregistration before execution; exact identities; complete intended sample; leakage/integrity/uncertainty/multiplicity gates; all planned outcomes reported. |
| `PAPER_ELIGIBLE` | Confirmatory or explicitly reproduced historical evidence; claim ledger row and hashes; allowed wording; analysis/release gates pass; no blocked dependency. |
| `RETIRED` | Identity invalid, method contradicted, unsupported threshold, or superseded protocol. Retained for provenance, excluded from current claims. |

No state is promoted because a wrapper exits 0. Promotion is derived from the primary artifacts.

## K. Expected total compute

### Calibrated boundary

Only S1 has a numeric planning range, and it is not calibrated: 1.71/3.51/7.93 aggregate T4x2
wall-hours including one cached download under explicit generic assumptions. S1 output-row proxy is
0.0031 GB; unique model-download proxy is 22.10 GB. These numbers are `PLANNED`, not measured.

### Scenario totals

| Scenario | Model-item work | GPU hours | CPU hours | Storage | Human effort |
|---|---:|---|---|---|---|
| Engineering S1 | 5 × 50 × 3 = 750 | 1.71/3.51/7.93 planned T4x2 wall-hours | local import/validation uncalibrated | 22.10 GB weight proxy + logs/ZIP | none |
| Minimum viable scientific path (S3) | 32 × (14,042 + 1,319 + 6,511) = 699,904 | `BLOCKED_UNTIL_S1/S2_CALIBRATION` | local analysis `BLOCKED_UNTIL_OUTPUTS` | row proxy ≈2.87 GB plus weights/raw logs; uncalibrated | optional 30×2=60 pilot labels; 200×3=600 full labels if human pillar used |
| Recommended strong path | S3 plus predeclared robustness and human pillar | `BLOCKED_UNTIL_PRIMARY` | blocked until outputs | primary storage plus condition-separated runs | 60 pilot + planned 600 full, exclusions/adjudication extra |
| Maximum-ceiling path (S4) | 40 × 21,872 = 874,880 primary model-items, plus robustness | `BLOCKED_UNTIL_S3` | blocked until outputs | roster/conditions dependent | full blinded human study plus external manual review if identity candidates exist |

The row-storage proxy uses 4,096 bytes per prediction and excludes raw generation text expansion,
model caches, checkpoints, and backups. Human calendar time and cost are intentionally not invented.

## One next action

Do not launch Kaggle yet. Implement and fixture-test the non-fixture benchmark runner behind
`run_notebook_stage`, freeze/hash BBH few-shot examples and package versions, and rerun
`python3 scripts/run_v5_local_validation.py`. Only if that produces
`CONTROLLED_GPU_SMOKE_READY` should the five-model S1 smoke begin.
