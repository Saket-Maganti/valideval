# valideval

**Validity is not accuracy.** `valideval` is a psychometric validity-auditing toolkit for asking what AI benchmarks actually measure.

A high benchmark score is evidence of something. This project treats benchmark-validity diagnostics
as measurement instruments: before a diagnostic licenses a benchmark-validity claim, it needs
evidence about sensitivity, false-positive behavior, specificity, uncertainty, materiality, and
transfer. The authoritative historical-evidence boundary remains the V5 claim ledger at
`results/evidence/claim_evidence_ledger_v5.csv`; older V4/no-run documents are historical snapshots.

## V7.2.1 final pre-GPU CPU closure

V7.2.1 is the canonical engineering source for the next Kaggle S1 smoke. It dynamically resolves
`valideval-v7.2.1-icml2027-kaggle-s1-ready`, adds claim-family-native known-truth confirmation,
rare-event safety intervals, statistical stress, secure package import, typed failure/retry and
evidence-state contracts, CPU replay, and a structured pre-GPU handoff. The native claim-policy
result is `CLAIM_POLICY_CONFIRMATION_SUPPORTING_ONLY`: aggregate family checks pass, but 21 of 60
prespecified critical cells fail their simultaneous safety bound. This result was not retuned.
Clean-checkout replay uses the versioned, hash-checked historical matrix at
`data/replay/v7_2_1/historical_mmlu_matrix.csv`; mutable local caches are not required.

No new real GPU, human, held-out transport, or held-out repair evidence is present. S1 remains an
engineering smoke, S2 is a draft pending accepted S1, and S3/S4 remain blocked. Start with
`VALID_EVAL_ICML2027_CANONICAL_EXECUTION_HANDBOOK.md` and
`VALID_EVAL_FINAL_CPU_MAXOUT_HANDOFF.md`. Reproduce the registered CPU state with:

```bash
python3 -m valideval replay-cpu-evidence
python3 -m valideval validate-release
```

## V7.1 scientific-integrity closure

V7.1 repairs the execution and inferential contracts without changing the frozen V7 empirical
result. Runner output, ZIP packaging, and import now use one schema; source identity and checksums
are verified fail-closed; model-load and generation OOMs propagate into bounded scheduler recovery;
and resume/package imports have end-to-end fixture coverage. Claim licenses now require an explicit
inferential unit, dependence-aware effective sample size, decision threshold direction, true
simultaneous rank interval type, and multiplicity-family metadata where applicable.

The closure does not turn missing evidence into findings. The frozen V7 synthetic grid remains
failed, transport folds are planned but not executed, human results remain planning-only, the
generalizability and measurement-regime analyses remain supporting-only, and the current Study-C
design grid is underpowered for all declared primary estimands. Start with
`VALID_EVAL_V7_1_FINAL_SCIENTIFIC_EXECUTION_HANDOFF.md` and `reports/v7_1/`.

Reproduce the new CPU closure artifacts with:

```bash
python3 scripts/run_claim_calibration_v7_1.py
python3 scripts/run_rank_coverage_v7_1.py
python3 scripts/run_synthetic_controls_v7_1.py
python3 scripts/run_study_h_v7.py
python3 scripts/run_study_c_power_v7_1.py
python3 scripts/run_transport_folds_v7_1.py
python3 scripts/run_estimand_conditions_v7_1.py
```

## V7 ICML 2027 pre-execution build

V7 adds multidimensional, fail-closed claim licensing; family-aware inference and multiplicity;
generalizability, decision-materiality, influence, measurement-regime, transport, human-study, and
benchmark-forensics protocols; and frozen S2–S5 controlled GPU contracts. The CPU studies and a
frozen confirmatory synthetic study have been executed from cached or generated data. The final
gate is `ICML2027_STRONG_PRE_EXECUTION_BUILD_PARTIAL`: this is a reproducible pre-execution build,
not a completed empirical paper.

The main limitations are substantive. The frozen synthetic detector missed its acceptance criteria,
Study H conclusions vary across null generators, the planned panels do not reach 0.80 power for a
0.01 paired difference, and controlled GPU, human-label, cross-benchmark transport, and held-out
repair evidence have not been collected. No result licenses a global benchmark-validity claim.

Start with `VALID_EVAL_V7_FINAL_MAXIMUM_PRE_EXECUTION_HANDOFF.md` and
`VALID_EVAL_ICML2027_EXECUTION_PLAN.md`. Reproduce the CPU evidence with:

```bash
python3 -m pip install -r requirements-cpu-v7.txt
python3 scripts/run_diagnostic_inference_v7.py
python3 scripts/run_study_h_v7.py
python3 scripts/run_confirmatory_synthetic_v7.py
python3 scripts/build_evidence_ledger_v7.py
python3 scripts/validate_v7_artifacts.py
```

The ten notebooks in `kaggle_v7/` are the GPU handoff. Every returned ZIP must enter through the
same fail-closed route:

```bash
python3 -m valideval ingest-and-analyze --input <zip-or-directory>
```

The S4 fallback panels are public and frozen in advance. They may be selected only for a recorded
feasibility failure, never after looking at benchmark scores.

## V6 Controlled GPU Smoke Readiness

V6 adds a fail-closed production execution path for the first controlled five-checkpoint Kaggle
T4×2 engineering smoke. The exact public checkpoints, immutable dataset revisions,
50-item-per-benchmark subsets, zero-shot prompt/scoring contracts, source tag, configuration hashes,
two-worker scheduler, gold-isolated scoring, deterministic packaging, and three-ZIP acceptance gate
are frozen. The smoke remains `ENGINEERING_ONLY` and the five-checkpoint panel is explicitly not
scientifically adequate.

Start with `VALID_EVAL_V6_CONTROLLED_GPU_SMOKE_RUNBOOK.md`. The local execution surface is:

```bash
python -m valideval run --config configs/runs/mmlu_s1_v6.yaml
python -m valideval run --config configs/runs/gsm8k_s1_v6.yaml
python -m valideval run --config configs/runs/bbh_s1_v6.yaml
python -m valideval accept-s1 --input-dir kaggle_outputs/v6 --output-root imported/v6
python -m valideval recalibrate-runtime --input-root imported/v6
```

No real S1 inference is included in this repository state. Fixture and mocked-production artifacts
are `NON_EVIDENCE_FIXTURE`; they cannot pass the S1 acceptance gate.

## V5 Evidence Boundary

V5 independently reconstructed the public HELM-derived MMLU Study H matrix from
`data/external/mmlu/prediction_details_wide.jsonl`. The reconstruction contains 547,638 unique rows,
39 models, 14,042 items, and 57 subjects, with zero missing cells, duplicate rows, contradictory
duplicates, or identity conflicts. Its values and labels are byte-for-byte equivalent to the active
matrix (`f85a0a44f3203de2863d86bf13b2c81d8e934ae4c07b826193b5e93a3fc86e74`). These are
`REPRODUCED` panel facts, not evidence that MMLU or any diagnostic is globally valid.

The reproduced descriptive results include an observed accuracy spread of 0.580188, a median raw
subject rank range of 19, a maximum of 30, and a proxy diagnostic-weighted comparison with Spearman
0.997976, Kendall 0.978408, and maximum absolute rank delta 2. Raw rank range is descriptive: the
legacy claim that a range of at least 10 is automatically a severe or material effect is `RETIRED`.
The legacy “diagnostic-family ablation” is `CONTRADICTED` because its seven family columns reuse
accuracy rather than independently computed diagnostic removals. MMLU-Redux item-level validation is
also `RETIRED`; the available structural linkage remains weak and is not direct/hash-confirmed.

Study C is separate from historical Study H. The controlled MMLU/GSM8K/BBH exact-checkpoint run,
human labels, and decoupled confirmatory synthetic evidence remain `BLOCKED` until real artifacts pass
their V5 import and analysis gates. Fixture outputs are always `NON_EVIDENCE_FIXTURE`.

## What Works Now

The first working milestone is an offline toy audit:

- Typed benchmark, prediction, response-matrix, diagnostic, and validity-profile schemas
- Synthetic toy MCQ benchmark with controlled artifacts
- Deterministic eight-model mock panel
- Cached prediction JSONL files and response matrices
- Heuristic baseline zoo and Dumb Baseline Gap
- Answer-distribution and distractor-quality diagnostics
- Shortcut diagnostic
- Prompt-sensitivity and extraction-robustness diagnostics
- IRT v2 diagnostic with proxy/Rasch fallback, uncertainty, multidimensional tag profiles, and subset modes
- Saturation, power, DIF, calibration/abstention, redundancy, and ranking-uncertainty diagnostics
- Reliability diagnostic across prompt variants with v2 stability fields
- Data-forensics diagnostics for local corpus overlap, internal duplicates, split leakage, temporal warnings, provenance completeness, and deterministic audit hashes
- Advisory benchmark repair engine with item-forensics tables, repair diffs, validity cards, audit-completeness evidence profiles, author checklists, and claim-to-evidence matrices
- Diagnostic-sensitive ranking views, flip detection, ranking significance, audit registry, benchmark atlas, static dashboard site, dashboard exports, audit diffs, and per-dimension health badges
- Synthetic diagnostic-validation harness with flaw sweeps, detector metrics, null thresholds, multiplicity correction, materiality labels, and validation reports
- GPQA Diamond first-audit setup with a local JSONL adapter, construct spec, prompt templates, synthetic fixture dry-run, and pre-registration draft
- Human-validation and judge-reliability studio for annotation packets, annotation import, agreement metrics, deterministic judge variants, scoring ambiguity, adjudication queues, and a static annotation viewer
- Domain-specific validity packs for RAG, abstention, agents, medical/segmentation, graph/fraud, code, safety, and multimodal metadata; all eight packs now include working offline diagnostics driven by item metadata
- Offline TF-IDF semantic duplicate detection in data-forensics
- Predictive and Goodhart diagnostics with optional external criterion and intervention datasets
- `legendary` audit preset, `audit-summary` CLI, and embedded diagnostic overview figures in report cards
- Local MMLU JSONL loader with an example subset fixture
- Adoption tooling for plugin registration, standard JSON schemas, quickstart audits, external-output imports, benchmark scaffolding, design-assistant artifacts, metadata-only readiness doctor reports, preregistration scaffolds, and benchmark-selection advice
- Paper/release tooling for scaffolded LaTeX sections, claims ledger, result-derived figures/tables, reproducibility bundles, environment capture, bundle verification, reviewer-risk audits, and NeurIPS-readiness gates
- Markdown validity report card
- CLI, configs, tests, docs, and paper scaffold

## Quickstart

```bash
python3 -m pip install -e ".[dev]"
python3 -m pytest
python3 -m valideval toy
python3 -m valideval doctor --benchmark toy_mcq --panel mock
python3 -m valideval matrices --benchmark toy_mcq --panel mock
python3 -m valideval audit --benchmark toy_mcq --panel mock --diagnostics all-core
python3 -m valideval audit --benchmark toy_mcq --panel mock --diagnostics legendary
python3 -m valideval audit-summary --benchmark toy_mcq --panel mock
python3 -m valideval report --benchmark toy_mcq --panel mock
```

Use `python` instead of `python3` if that is the Python executable exposed by your environment.

## Historical pre-V7 confirmatory synthetic status

The following section describes the historical V5 build-only surface. V7 supersedes it with a
separately frozen protocol and recorded negative acceptance result under `results/v7/synthetic/`:

- `CONFIRMATORY_RUN_COMMAND_MANIFEST.md`
- `RUNBOOK_CONFIRMATORY_SYNTHETIC_VALIDATION.md`
- `BUILD_ONLY_POLISH_AUDIT.md`
- `templates/reports/*CONFIRMATORY*_TEMPLATE.md`
- `scripts/preflight_confirmatory_synthetic.py`

Run the static no-run preflight with:

```bash
python3 scripts/preflight_confirmatory_synthetic.py
```

The preflight checks files, configs, templates, output-path writability, documented failure cases,
and blocked-claim language. It prints future commands only; it does not run validation, generate
synthetic data, perform inference, download artifacts, recompute metrics, tune thresholds, or upgrade
evidence states.

Legacy cross-flaw and held-out artifacts retain their historical `WEAK` labels as wiring/stress-test
context. In the V5 ledger, the independent decoupled confirmatory claim is `BLOCKED`; numeric
calibration is also blocked, MMLU-Redux is a retired positive-validation path, and GPQA remains
protocol/demo unless future wide-panel evidence exists.

Current MMLU evidence reconciliation: the active all-subject MMLU panel is the 39-model public
HELM-derived matrix at `cache/mmlu/wide/matrix.csv`; the older 3-model files are
historical/provenance only. Study H reproduction and the V5 rank-materiality pipeline are local
artifact analyses. They do not substitute for the blocked Study C controlled common-panel run,
direct/hash Redux linkage, human validation, or decoupled confirmatory synthetic execution.

## Historical Real-Panel and Later-Run Preflights

V5 reproduced the Study H rank summaries described above. The older commands below remain
build-only compatibility preflights for other finding paths; they do not compute metrics, contact
model services, download data, or upgrade Study C claims:

```bash
python3 -m valideval real-panel-ranking-audit --dry-run --matrix PATH --predictions PATH --mmlu-redux PATH
python3 -m valideval diagnostic-disagreement-audit --dry-run --matrix PATH --predictions PATH --mmlu-redux PATH
python3 -m valideval subject-instability-audit --dry-run --matrix PATH --predictions PATH --mmlu-redux PATH
python3 -m valideval real-panel-baselines-preflight --dry-run
python3 -m valideval panel-preflight --dry-run
python3 -m valideval benchmark-preflight --dry-run
python3 -m valideval calibration-preflight --dry-run
python3 -m valideval power-materiality-preflight --dry-run
python3 -m valideval mmlu-redux-alignment-preflight --dry-run --predictions PATH --redux PATH
```

Later empirical work must follow `MASTER_LATER_RUN_PLAN.md` and `LATER_RUN_APPROVAL_CHECKLIST.md`.
The NeurIPS readiness gate also checks `NO_RUN_RULES_AND_EVIDENCE_STATE_LOCK.md` by default so
blocked/weak evidence states stay visible in release review:

```bash
python3 -m valideval neurips-readiness --benchmark toy_mcq --panel mock --strict
```

Generated artifacts:

```text
cache/toy_mcq/mock/predictions_full.jsonl
cache/toy_mcq/mock/matrix_full.csv
results/toy_mcq/mock/shortcut.json
results/toy_mcq/mock/baselines.json
results/toy_mcq/mock/answer_distribution.json
results/toy_mcq/mock/distractor_quality.json
results/toy_mcq/mock/distractor_quality.csv
results/toy_mcq/mock/prompt_sensitivity.json
results/toy_mcq/mock/extraction_robustness.json
results/toy_mcq/mock/irt.json
results/toy_mcq/mock/reliability.json
results/toy_mcq/mock/saturation.json
results/toy_mcq/mock/power.json
results/toy_mcq/mock/data_forensics.json
results/toy_mcq/mock/item_forensics.csv
results/toy_mcq/mock/repair_report.md
results/toy_mcq/mock/repair_diff.json
results/toy_mcq/mock/validity_card.json
results/toy_mcq/mock/validity_card.md
results/toy_mcq/mock/validity_certificate.json
results/toy_mcq/mock/validity_certificate.md
results/toy_mcq/mock/ranking_views.json
results/toy_mcq/mock/ranking_flips.json
results/toy_mcq/mock/ranking_significance.json
results/toy_mcq/mock/health_badges.json
results/toy_mcq/mock/human/items.jsonl
results/toy_mcq/mock/human/agreement_report.json
results/toy_mcq/mock/human/judge_reliability.json
results/toy_mcq/mock/human/scoring_ambiguity.csv
results/toy_mcq/mock/human/adjudication_queue.jsonl
results/toy_mcq/mock/rag_validity.json
results/toy_mcq/mock/abstention_validity.json
leaderboard/benchmark_atlas.json
leaderboard/benchmark_atlas.md
dashboard_data/benchmark_profiles.json
site/index.html
registry/audits.json
results/toy_mcq/manifest.json
reportcards/toy_mcq_mock.md
reportcards/toy_mcq_mock.manifest.json
```

## Why Validity Is Not Accuracy

Accuracy answers: how often did a model match the scoring rule?

Validity asks: does that score support the claim we want to make? A model may score well because it uses construct-relevant reasoning, or because of answer priors, leaked items, weak item discrimination, unstable scoring, or a benchmark that covers only part of the construct.

`valideval` reports diagnostic profiles, not a single validity score.

## CLI

The V6 production execution and V5 release surfaces are fail-closed. The old
`import-kaggle-outputs`, `post-import-analysis`, and `cross-benchmark-analysis` commands remain for
historical compatibility. V7 controlled artifacts use `ingest-and-analyze`; the following V5
commands remain available for their frozen release surface:

```bash
python3 -m valideval validate-run kaggle_outputs_v5 --strict
python3 -m valideval import-kaggle --input-dir kaggle_outputs_v5 --strict
python3 -m valideval post-import --strict
python3 -m valideval cross-benchmark
python3 -m valideval build-evidence-ledger
python3 -m valideval build-paper-assets
python3 -m valideval build-release --profile reviewer --build
```

`post-import` writes a gated route from V5 import receipts; it does not execute the retired V4
diagnostic-family ablation. `cross-benchmark` remains `BLOCKED` until all declared matrices and exact
checkpoint metadata are present. A non-strict dry run records blockers without turning them into
evidence.

```bash
python3 -m valideval info
python3 -m valideval toy
python3 -m valideval doctor --benchmark toy_mcq --panel mock
python3 -m valideval doctor --benchmark toy_mcq --panel mock --strict
python3 -m valideval matrices --benchmark toy_mcq --panel mock
python3 -m valideval baselines --benchmark toy_mcq
python3 -m valideval diagnostics answer-distribution --benchmark toy_mcq
python3 -m valideval diagnostics distractors --benchmark toy_mcq
python3 -m valideval diagnostics prompt-sensitivity --benchmark toy_mcq --panel mock
python3 -m valideval diagnostics extraction-robustness --benchmark toy_mcq --panel mock
python3 -m valideval diagnostics data-forensics --benchmark toy_mcq --panel mock
python3 -m valideval forensics overlap --benchmark toy_mcq --corpus examples/toy_corpus/
python3 -m valideval psychometrics irt --benchmark toy_mcq --panel mock
python3 -m valideval psychometrics saturation --benchmark toy_mcq --panel mock
python3 -m valideval psychometrics power --benchmark toy_mcq --panel mock
python3 -m valideval psychometrics dif --benchmark toy_mcq --panel mock
python3 -m valideval psychometrics calibration --benchmark toy_mcq --panel mock
python3 -m valideval psychometrics all --benchmark toy_mcq --panel mock
python3 -m valideval audit --benchmark toy_mcq --panel mock --diagnostics all-core
python3 -m valideval audit --benchmark toy_mcq --panel mock --diagnostics shortcut irt reliability
python3 -m valideval repair --benchmark toy_mcq --panel mock --policy conservative
python3 -m valideval card render --benchmark toy_mcq --panel mock
python3 -m valideval certificate issue --benchmark toy_mcq --panel mock
python3 -m valideval checklist --benchmark toy_mcq --panel mock
python3 -m valideval evidence-matrix --benchmark toy_mcq --panel mock
python3 -m valideval leaderboard --benchmark toy_mcq --panel mock
python3 -m valideval registry validate
python3 -m valideval registry list
python3 -m valideval registry add --benchmark toy_mcq --panel mock
python3 -m valideval atlas --benchmark toy_mcq --panel mock
python3 -m valideval dashboard export --benchmark toy_mcq --panel mock
python3 -m valideval site build
python3 -m valideval badges --benchmark toy_mcq --panel mock
python3 -m valideval audit-diff results/toy_mcq/mock results/toy_mcq/mock
python3 -m valideval human packet --benchmark toy_mcq --panel mock --sample-size 288
python3 -m valideval human import --benchmark toy_mcq --panel mock --path examples/toy_human_annotations.csv
python3 -m valideval human agreement --benchmark toy_mcq --panel mock
python3 -m valideval human judge --benchmark toy_mcq --panel mock
python3 -m valideval human ambiguity --benchmark toy_mcq --panel mock
python3 -m valideval human adjudication --benchmark toy_mcq --panel mock
python3 -m valideval human ui --benchmark toy_mcq --panel mock
python3 -m valideval domain list
python3 -m valideval domain describe rag
python3 -m valideval audit --benchmark toy_mcq --panel mock --domain rag
python3 -m valideval audit --benchmark toy_mcq --panel mock --domain abstention
python3 -m valideval plugins list
python3 -m valideval schema export all --output docs/schemas
python3 -m valideval schema validate benchmark --path items.jsonl
python3 -m valideval import-outputs --input model_outputs.csv --output normalized_outputs.jsonl --adapter generic-csv
python3 -m valideval export-gpqa-diamond --source-file data/raw/gpqa_source.csv --output data/gpqa/gpqa_diamond.jsonl
python3 -m valideval check-panel --panel gpqa_open_local
python3 -m valideval generate-outputs --benchmark gpqa_diamond --items data/gpqa/gpqa_diamond.jsonl --panel gpqa_open_local --prompt-variant full --output-dir local_outputs/gpqa/full
python3 -m valideval matrix-from-predictions --benchmark gpqa_diamond --panel gpqa_open_local --variant full
python3 -m valideval quickstart-audit --items items.jsonl --outputs model_outputs.jsonl --benchmark-card benchmark_card.md
python3 -m valideval init-benchmark my_benchmark
python3 -m valideval validate-benchmark my_benchmark/
python3 -m valideval generate-card my_benchmark/
python3 -m valideval audit my_benchmark/
python3 -m valideval design-assistant --noninteractive --benchmark-id rag_eval --construct "RAG faithfulness under supplied evidence" --domain rag
python3 -m valideval preregister --benchmark rag_eval --goal "evaluate RAG faithfulness" --domain rag --panel mock --artifact-scope dry_run
python3 -m valideval advisor --goal "evaluate RAG faithfulness"
python3 -m valideval paper-assets --benchmark toy_mcq --panel mock
python3 -m valideval bundle --benchmark toy_mcq --panel mock
python3 -m valideval verify-bundle bundles/toy_mcq_mock_bundle
python3 -m valideval reviewer-risk --report reportcards/toy_mcq_mock.md
python3 -m valideval environment --output environment.json
python3 -m valideval neurips-readiness --benchmark toy_mcq --panel mock
python3 -m valideval real-panel-baselines-preflight --dry-run
python3 -m valideval panel-preflight --dry-run
python3 -m valideval benchmark-preflight --dry-run
python3 -m valideval calibration-preflight --dry-run
python3 -m valideval power-materiality-preflight --dry-run
python3 -m valideval validate-diagnostics --config configs/validation/all_sweeps.yaml
python3 -m valideval validation-summary
python3 -m valideval report --benchmark toy_mcq --panel mock
python3 -m valideval ranking --benchmark toy_mcq --panel mock
python3 -m valideval validate-config configs/default.yaml
python3 -m valideval audit --benchmark gpqa_diamond_tiny_fixture --panel mock --config configs/audits/gpqa_diamond_preregistered.yaml --diagnostics answer_distribution distractor_quality irt reliability extraction_robustness saturation shortcut prompt_sensitivity --dry-run
```

The core/dev install is enough for the offline toy audit and tests. Public-artifact acquisition
scripts such as HELM/MMLU discovery use optional network dependencies and should be installed
explicitly with `python3 -m pip install -e ".[acquisition]"` only when an approved acquisition pass
is intended.

## Architecture

```text
src/valideval/
  schemas.py              typed audit objects
  baselines/              shallow heuristic baseline probes
  benchmarks/             benchmark adapters and prompt variants
  models/                 mock and optional local model runners
  scoring/                exact-match and MCQ scoring
  io/                     JSONL and matrix cache utilities
  diagnostics/            validity diagnostics
  validation/             synthetic detector-validation harness
  forensics/              local overlap, duplicates, leakage, temporal, provenance, and hashes
  repair/                 item forensics, repair policies, cards, certificates, and evidence matrix
  leaderboard/            ranking views, flips, registry, atlas, dashboard exports, site, badges
  human/                  annotation packets, agreement, judge reliability, ambiguity, adjudication
  domains/                domain packs, threat library, schemas, RAG and abstention diagnostics
  adoption/               schemas, importers, quickstart audit, author toolkit, doctor, design/prereg helpers
  plugins.py              extension-point decorators and registries
  release/                paper assets, environment capture, bundles, verification, reviewer-risk and NeurIPS-readiness modes
  psychometrics/          bootstrap, reliability, IRT proxy utilities
  audit/                  runner, report card, ranking comparison
  report/                 figures and table helpers
```

## Real Benchmarks

Configs exist for MMLU, GSM8K, BBH, TruthfulQA, and CausalAgentBench, but those loaders are intentionally scaffold-only. GPQA Diamond is now selected as the first real audit target and has a local JSONL adapter plus pre-registration artifacts.

The bundled `gpqa_diamond_tiny_fixture` is synthetic and dry-run only. It validates schema, scoring, diagnostics, report-card, validity-card, and evidence-profile plumbing; it is not GPQA and is not scientific evidence. A real GPQA audit still requires a verified local GPQA Diamond JSONL export and cached open/local model outputs.

## GPQA local export and output generation

The repo does not ship GPQA items. Users must obtain GPQA Diamond through appropriate local means and comply with the dataset's access and licensing terms. Raw question text should not be pasted into public reports, docs, or issue threads.

Export a local source file into the expected schema:

```bash
python3 -m valideval export-gpqa-diamond --source-file data/raw/gpqa_source.csv --output data/gpqa/gpqa_diamond.jsonl
```

Or export from a local Hugging Face cache if `datasets` is installed and the dataset is already present locally:

```bash
python3 -m valideval export-gpqa-diamond --source hf --output data/gpqa/gpqa_diamond.jsonl
```

Check the local/open panel and generate cached raw outputs:

```bash
python3 -m valideval check-panel --panel gpqa_open_local
python3 -m valideval generate-outputs --benchmark gpqa_diamond --items data/gpqa/gpqa_diamond.jsonl --panel gpqa_open_local --prompt-variant full --output-dir local_outputs/gpqa/full
```

Smoke runs can use `configs/panels/gpqa_smoke_local.yaml` and `--limit-items`, but they are workflow checks only. They are not GPQA results and are not sufficient for paper-grade IRT or model-family claims.

For cached real outputs, score raw outputs with `score-outputs` or normalize pre-scored predictions with `import-outputs`, then build matrices with `matrix-from-predictions`. No audit claims should be made until go/no-go passes and diagnostics are run under `docs/protocols/gpqa_diamond_preregistration.md`.

### How to provide real GPQA inputs

Expected item file:

```text
data/gpqa/gpqa_diamond.jsonl
```

Expected cached output paths:

```text
local_outputs/gpqa/full/*.jsonl
local_outputs/gpqa/question_only/*.jsonl
local_outputs/gpqa/choices_only/*.jsonl
local_outputs/gpqa/randomized_choices/*.jsonl
local_outputs/gpqa/answer_letter_only/*.jsonl
cache/gpqa_diamond/gpqa_open_local/predictions_full.jsonl
cache/gpqa_diamond/gpqa_open_local/matrix_full.csv
```

Validate the local item export:

```bash
python3 -m valideval doctor --benchmark gpqa_diamond --panel gpqa_open_local --local-path data/gpqa/gpqa_diamond.jsonl
python3 -m valideval validate-benchmark-file --benchmark gpqa_diamond --items data/gpqa/gpqa_diamond.jsonl
```

For already scored predictions:

```bash
python3 -m valideval import-outputs --input local_outputs/gpqa_full.jsonl --output cache/gpqa_diamond/gpqa_open_local/predictions_full.jsonl --adapter generic-jsonl --benchmark-id gpqa_diamond --prompt-variant full
```

For raw unscored outputs:

```bash
python3 -m valideval score-outputs --benchmark gpqa_diamond --items data/gpqa/gpqa_diamond.jsonl --input local_outputs/gpqa_full_raw.jsonl --output cache/gpqa_diamond/gpqa_open_local/predictions_full.jsonl --prompt-variant full
```

Then build and validate matrices:

```bash
python3 -m valideval matrix-from-predictions --benchmark gpqa_diamond --panel gpqa_open_local --variant full
python3 -m valideval validate-alignment --benchmark gpqa_diamond --items data/gpqa/gpqa_diamond.jsonl --predictions cache/gpqa_diamond/gpqa_open_local/predictions_full.jsonl
python3 -m valideval extraction-audit --benchmark gpqa_diamond --items data/gpqa/gpqa_diamond.jsonl --outputs local_outputs/gpqa_full_raw.jsonl --prompt-variant full
python3 -m valideval validate-prompt-variants --benchmark gpqa_diamond --panel gpqa_open_local --required-variants full question_only choices_only randomized_choices answer_letter_only
python3 -m valideval gpqa-go-no-go --benchmark gpqa_diamond --items data/gpqa/gpqa_diamond.jsonl --panel gpqa_open_local
python3 -m valideval audit-manifest --benchmark gpqa_diamond --items data/gpqa/gpqa_diamond.jsonl --panel gpqa_open_local
```

Real-audit dry run from imported outputs:

```bash
python3 -m valideval audit --benchmark gpqa_diamond --panel gpqa_open_local --local-path data/gpqa/gpqa_diamond.jsonl --config configs/audits/gpqa_diamond_preregistered.yaml --from-cache --input-validated-only --dry-run-real
```

These commands produce input-validation artifacts only. They do not establish GPQA Diamond validity findings, rankings, contamination status, or benchmark-health claims.

Useful setup files:

```text
configs/benchmarks/gpqa_diamond.yaml
configs/constructs/gpqa_diamond_construct.yaml
configs/audits/gpqa_diamond_preregistered.yaml
configs/panels/gpqa_open_local.yaml
configs/panels/gpqa_smoke_local.yaml
docs/protocols/gpqa_diamond_preregistration.md
GPQA_DIAMOND_AUDIT_READINESS.md
GPQA_OUTPUT_GENERATION_PLAN.md
examples/gpqa_diamond_tiny_fixture.jsonl
schemas/gpqa_diamond_item.schema.json
schemas/gpqa_model_output_raw.schema.json
schemas/gpqa_model_prediction_scored.schema.json
```

The repo does not invent results. To audit a real benchmark, provide a validated local JSONL export, normalize existing local outputs with `import-outputs`, or implement a loader/scoring plugin.

## What Is Intentionally Not Claimed

- A diagnostic does not prove that a benchmark is globally valid or invalid.
- Contamination overlap is evidence, not proof.
- Absence of overlap is not proof of cleanliness.
- Local data-forensics scans only cover the corpora and metadata supplied to the audit.
- Repair recommendations are advisory and require benchmark-author review.
- Validity evidence profiles describe audit completeness; they are not scalar scores or quality grades.
- Diagnostic-sensitive ranking views are sensitivity analyses, not corrected leaderboards.
- Synthetic diagnostic validation is detector evidence under controlled generators, not real benchmark evidence.
- Health badges are per-dimension summaries and must not be averaged into a total score.
- Human labels are not perfect ground truth; they are protocol evidence that may require adjudication.
- Rule/mock judge agreement is not a proof that an open-ended scoring rule is valid.
- Domain-pack diagnostics depend on domain metadata and perturbations; unavailable signals are missing evidence, not passed checks.
- Scaffolded domain packs define threats, schemas, and repair policies but do not claim empirical coverage.
- IRT proxy values are not ground truth.
- A diagnostic-sensitive ranking is an alternative view under assumptions, not the one true ranking.
- GPQA fixture dry-runs are setup checks only and must not be reported as GPQA Diamond findings.

## Reproducibility

The toy demo is fully offline and deterministic. It requires no paid APIs, no internet, no Hugging Face downloads, and no Ollama. Predictions and matrices are cached under `cache/`, diagnostics under `results/`, the audit manifest under `results/{benchmark}/manifest.json`, and report cards plus report manifests under `reportcards/`.

Use `python3 -m valideval doctor --benchmark toy_mcq --panel mock --strict` as a metadata-only readiness gate when you need CI to fail on missing cache, diagnostics, or report-card artifacts. For restricted benchmarks, doctor reports counts, hashes, paths, and missing-artifact status without printing raw item text or raw outputs.

Release bundles can be created with `python3 -m valideval bundle --benchmark toy_mcq --panel mock` and verified with `python3 -m valideval verify-bundle bundles/toy_mcq_mock_bundle`. Bundles disclose missing expected artifacts instead of synthesizing them.

## Roadmap

- Add local JSONL audit recipes for more real benchmark exports beyond MMLU.
- Add richer real-benchmark recipes for human validation and adjudication.
- Add optional embedding-backed semantic duplicate detection beyond TF-IDF.
- Regenerate paper figures and tables directly from all cached results.

## Citation

Citation metadata will be added after the first public research release.

## Contributing

Keep changes reproducible, offline-safe where possible, and honest about evidence. Do not add paid APIs as required dependencies. Do not collapse validity into one scalar.
