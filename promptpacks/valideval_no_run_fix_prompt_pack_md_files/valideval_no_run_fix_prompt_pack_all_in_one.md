---

# FILE: 00_global_no_run_rules.md

# Codex Prompt — 00 Global No-Run Rules and Evidence-State Lock

## Global hard rules

This is a **build/fix/polish only** prompt.

Do **not** run:
- validation experiments,
- synthetic generation,
- model inference,
- downloads,
- metric recomputation,
- threshold tuning,
- MMLU-Redux reruns,
- confirmatory cross-flaw / held-out runs,
- real-panel ranking analysis.

Allowed:
- static inspection,
- code scaffolding,
- dry-run or preflight commands,
- report/template creation,
- claim hygiene,
- `ruff check .`,
- targeted tests for newly added no-run code.

Do not upgrade evidence states. Do not remove caveats. Do not remove `[RESULT REQUIRED]` unless a matching local artifact already exists.


## Task

Create `NO_RUN_RULES_AND_EVIDENCE_STATE_LOCK.md`.

It must record the current evidence states:
- controlled synthetic flaw detection: current supported/credible status from docs,
- synthetic FPR/null controls: current supported status from docs,
- cross-flaw specificity: WEAK,
- held-out generator transfer: WEAK,
- materiality: WEAK,
- toy-only power: WEAK,
- numeric calibration without confidence/logprob outputs: BLOCKED,
- synthetic-to-real threshold validation: NOT_RUN,
- confirmatory synthetic follow-up: RESULT_REQUIRED,
- MMLU-Redux: weak/negative external stress test,
- GPQA: protocol/demo unless wide-panel evidence exists,
- HELM MMLU panel: real input exists, but real-panel finding still RESULT_REQUIRED.

Update `README.md`, `CLAIMS_LEDGER_NEURIPS.md`, `paper/claims.md`, and `paper/limitations.md` only with pointers or claim-state clarifications.

Final report structure:
`## Summary`, `## Evidence states locked`, `## Forbidden commands`, `## Allowed commands`, `## Files created/modified`, `## Commands run`, `## Recommendation`.

## Final response format

Return:

```markdown
## Summary
## What was built/changed
## What was not run
## Evidence states
## Files created/modified
## Commands run
## Remaining blockers
## Recommendation
## Next best prompt
```


---

# FILE: 01_paper_thesis_reframe.md

# Codex Prompt — 01 Paper Thesis Reframe Around Diagnostic Validation

## Global hard rules

This is a **build/fix/polish only** prompt.

Do **not** run:
- validation experiments,
- synthetic generation,
- model inference,
- downloads,
- metric recomputation,
- threshold tuning,
- MMLU-Redux reruns,
- confirmatory cross-flaw / held-out runs,
- real-panel ranking analysis.

Allowed:
- static inspection,
- code scaffolding,
- dry-run or preflight commands,
- report/template creation,
- claim hygiene,
- `ruff check .`,
- targeted tests for newly added no-run code.

Do not upgrade evidence states. Do not remove caveats. Do not remove `[RESULT REQUIRED]` unless a matching local artifact already exists.


## Task

Reframe the paper away from broad toolkit/product pitch and toward the thesis:

> ValidEval validates validity diagnostics before they license benchmark-validity claims.

Inspect:
`paper/abstract.md`, `paper/introduction.md`, `paper/experiments.md`, `paper/diagnostic_validation.md`, `paper/limitations.md`, `paper/claims.md`, `paper/related_work.md`, `paper/main.tex`, `paper/sections/*`, `CLAIMS_LEDGER_NEURIPS.md`, `MMLU_EVIDENCE_GATE_REPORT.md`, `SYNTHETIC_EVIDENCE_STATUS_TABLE.md`.

The paper should say:
- controlled synthetic validation is generator-scoped,
- cross-flaw / held-out expose failures,
- MMLU-Redux is weak/negative,
- the 39-model HELM MMLU panel is a real-panel substrate,
- ranking/diagnostic finding remains `[RESULT REQUIRED]`.

The paper must not imply:
- ValidEval detects MMLU errors,
- MMLU-Redux validation succeeded,
- cross-flaw or held-out are solved,
- synthetic validation proves real validity,
- certificates/badges/domain packs are validated contributions.

Create `PAPER_THESIS_REFRAME_AUDIT.md` with:
1. Executive summary
2. Old risky framing
3. New thesis
4. Files reviewed
5. Edits made
6. Claims allowed
7. Claims blocked
8. Remaining `[RESULT REQUIRED]`
9. Reviewer risks
10. Next build step.

## Final response format

Return:

```markdown
## Summary
## What was built/changed
## What was not run
## Evidence states
## Files created/modified
## Commands run
## Remaining blockers
## Recommendation
## Next best prompt
```


---

# FILE: 02_surface_area_freeze.md

# Codex Prompt — 02 Surface-Area Freeze and Release Slimming

## Global hard rules

This is a **build/fix/polish only** prompt.

Do **not** run:
- validation experiments,
- synthetic generation,
- model inference,
- downloads,
- metric recomputation,
- threshold tuning,
- MMLU-Redux reruns,
- confirmatory cross-flaw / held-out runs,
- real-panel ranking analysis.

Allowed:
- static inspection,
- code scaffolding,
- dry-run or preflight commands,
- report/template creation,
- claim hygiene,
- `ruff check .`,
- targeted tests for newly added no-run code.

Do not upgrade evidence states. Do not remove caveats. Do not remove `[RESULT REQUIRED]` unless a matching local artifact already exists.


## Task

Reduce reviewer risk from feature sprawl and process theater.

Create `SURFACE_AREA_FREEZE_AUDIT.md`.

Classify:
- core paper contribution,
- reviewer-facing files,
- support files,
- deferred/non-paper features,
- files not in main reviewer path.

Mark as deferred unless separately validated:
- domain packs,
- certificates/badges,
- repair engine,
- leaderboard/site,
- design assistant/plugin surfaces,
- predictive/Goodhart claims,
- any diagnostic without validation.

Update `README.md`, `REVIEWER_READING_GUIDE.md`, `REVIEWER_PACKET_MANIFEST.md`, `paper/claims.md`, `paper/limitations.md`, and `CLAIMS_LEDGER_NEURIPS.md` so the reviewer path is:
1. paper thesis,
2. diagnostic validation,
3. synthetic evidence state,
4. MMLU weak/negative stress test,
5. preregistered confirmatory plan,
6. real-panel finding `[RESULT REQUIRED]`.

Do not delete files unless clearly temporary/generated and already excluded from release.

## Final response format

Return:

```markdown
## Summary
## What was built/changed
## What was not run
## Evidence states
## Files created/modified
## Commands run
## Remaining blockers
## Recommendation
## Next best prompt
```


---

# FILE: 03_real_panel_finding_engine.md

# Codex Prompt — 03 Build Real-Panel Finding Engine Without Running Analyses

## Global hard rules

This is a **build/fix/polish only** prompt.

Do **not** run:
- validation experiments,
- synthetic generation,
- model inference,
- downloads,
- metric recomputation,
- threshold tuning,
- MMLU-Redux reruns,
- confirmatory cross-flaw / held-out runs,
- real-panel ranking analysis.

Allowed:
- static inspection,
- code scaffolding,
- dry-run or preflight commands,
- report/template creation,
- claim hygiene,
- `ruff check .`,
- targeted tests for newly added no-run code.

Do not upgrade evidence states. Do not remove caveats. Do not remove `[RESULT REQUIRED]` unless a matching local artifact already exists.


## Task

Build the engine for later real-panel findings, but do not run analysis.

Create or update:
- `src/valideval/real_panel/finding_engine.py`
- CLI dry-run commands:
  - `real-panel-ranking-audit --dry-run`
  - `diagnostic-disagreement-audit --dry-run`
  - `subject-instability-audit --dry-run`
- `tests/test_real_panel_dryrun_commands.py`
- `REAL_PANEL_FINDING_ENGINE_BUILD_AUDIT.md`

Dry-run commands should validate input paths and schemas, write manifests, list planned metrics and outputs, but refuse metric computation.

Planned finding types:
1. accuracy-only vs validity-adjusted ranking disagreement,
2. diagnostic-vs-diagnostic disagreement,
3. subject-specific validity instability,
4. suspicious-item subset ranking sensitivity,
5. multiple-diagnostic flagged item sets,
6. MMLU-Redux weak/negative as blocked-claim case.

Non-dry-run must refuse unless an explicit future authorization flag exists, e.g. `--execute-confirmatory-real-panel`.

Allowed checks:
`ruff check .`
`python3 -m pytest -q tests/test_real_panel_dryrun_commands.py`

## Final response format

Return:

```markdown
## Summary
## What was built/changed
## What was not run
## Evidence states
## Files created/modified
## Commands run
## Remaining blockers
## Recommendation
## Next best prompt
```


---

# FILE: 04_baselines_ablations_scaffold.md

# Codex Prompt — 04 Real-Panel Baselines and Ablations Scaffold

## Global hard rules

This is a **build/fix/polish only** prompt.

Do **not** run:
- validation experiments,
- synthetic generation,
- model inference,
- downloads,
- metric recomputation,
- threshold tuning,
- MMLU-Redux reruns,
- confirmatory cross-flaw / held-out runs,
- real-panel ranking analysis.

Allowed:
- static inspection,
- code scaffolding,
- dry-run or preflight commands,
- report/template creation,
- claim hygiene,
- `ruff check .`,
- targeted tests for newly added no-run code.

Do not upgrade evidence states. Do not remove caveats. Do not remove `[RESULT REQUIRED]` unless a matching local artifact already exists.


## Task

Build no-run scaffolds for reviewer-required baselines.

Create:
- `REAL_PANEL_BASELINES_PLAN.md`
- `src/valideval/real_panel/baselines.py`
- `configs/real_panel/baselines_mmlu.yaml`
- `tests/test_real_panel_baselines_scaffold.py`

Baseline plan must include:
1. accuracy-only ranking,
2. random item subset,
3. subject-stratified subset,
4. naive difficulty,
5. naive disagreement,
6. diagnostic-vs-diagnostic,
7. MMLU-Redux external label baseline,
8. subject confounding baseline.

Code must include schemas and dry-run manifests only. Computation stubs should raise `NotImplementedError` or explicit refusal.

Update paper placeholders:
- `[RESULT REQUIRED: accuracy-only baseline]`
- `[RESULT REQUIRED: random subset baseline]`
- `[RESULT REQUIRED: subject-stratified baseline]`
- `[RESULT REQUIRED: naive disagreement baseline]`
- `[RESULT REQUIRED: diagnostic-vs-diagnostic baseline]`.

Allowed checks:
`ruff check .`
`python3 -m pytest -q tests/test_real_panel_baselines_scaffold.py`

## Final response format

Return:

```markdown
## Summary
## What was built/changed
## What was not run
## Evidence states
## Files created/modified
## Commands run
## Remaining blockers
## Recommendation
## Next best prompt
```


---

# FILE: 05_figures_tables_templates.md

# Codex Prompt — 05 Real-Panel Figures and Tables Templates

## Global hard rules

This is a **build/fix/polish only** prompt.

Do **not** run:
- validation experiments,
- synthetic generation,
- model inference,
- downloads,
- metric recomputation,
- threshold tuning,
- MMLU-Redux reruns,
- confirmatory cross-flaw / held-out runs,
- real-panel ranking analysis.

Allowed:
- static inspection,
- code scaffolding,
- dry-run or preflight commands,
- report/template creation,
- claim hygiene,
- `ruff check .`,
- targeted tests for newly added no-run code.

Do not upgrade evidence states. Do not remove caveats. Do not remove `[RESULT REQUIRED]` unless a matching local artifact already exists.


## Task

Create publication-ready templates with no fake values.

Create:
- `paper/tables/real_panel_ranking_audit_template.tex`
- `paper/tables/diagnostic_disagreement_template.tex`
- `paper/tables/subject_instability_template.tex`
- `paper/tables/baseline_comparison_template.tex`
- `paper/figures/README_REAL_PANEL_FIGURES.md`
- `templates/reports/REAL_PANEL_FINDING_SUMMARY_TEMPLATE.md`
- `templates/reports/REAL_PANEL_RANKING_AUDIT_TEMPLATE.md`
- `templates/reports/DIAGNOSTIC_DISAGREEMENT_AUDIT_TEMPLATE.md`
- `templates/reports/SUBJECT_INSTABILITY_AUDIT_TEMPLATE.md`
- `REAL_PANEL_FIGURE_TABLE_TEMPLATE_AUDIT.md`

Every template must use `[RESULT REQUIRED]`.

Document future figures:
1. accuracy-only vs validity-adjusted ranking scatter,
2. rank shift bar plot,
3. diagnostic disagreement heatmap,
4. subject instability heatmap,
5. suspicious-item subset effect plot,
6. MMLU-Redux weak/negative summary,
7. synthetic cross-flaw/held-out evidence-state figure.

Do not compile unless placeholders are known safe.

## Final response format

Return:

```markdown
## Summary
## What was built/changed
## What was not run
## Evidence states
## Files created/modified
## Commands run
## Remaining blockers
## Recommendation
## Next best prompt
```


---

# FILE: 06_ollama_panel_dryrun.md

# Codex Prompt — 06 Ollama `load_panel()` Integration, Dry-Run Only

## Global hard rules

This is a **build/fix/polish only** prompt.

Do **not** run:
- validation experiments,
- synthetic generation,
- model inference,
- downloads,
- metric recomputation,
- threshold tuning,
- MMLU-Redux reruns,
- confirmatory cross-flaw / held-out runs,
- real-panel ranking analysis.

Allowed:
- static inspection,
- code scaffolding,
- dry-run or preflight commands,
- report/template creation,
- claim hygiene,
- `ruff check .`,
- targeted tests for newly added no-run code.

Do not upgrade evidence states. Do not remove caveats. Do not remove `[RESULT REQUIRED]` unless a matching local artifact already exists.


## Task

Address the “wire Ollama into `load_panel()`” criticism without inference.

Create/update:
- `src/valideval/panels/ollama_panel.py`
- `src/valideval/panels/loader.py`
- `configs/panels/ollama_local_small.yaml`
- CLI `panel-preflight --dry-run`
- `tests/test_ollama_panel_dryrun.py`
- `OLLAMA_PANEL_DRYRUN_BUILD_REPORT.md`

Dry-run should:
- validate config,
- list planned models,
- list benchmark compatibility,
- not call Ollama server,
- not run inference.

Non-dry-run must refuse unless explicit `--execute-inference` is supplied.

Allowed checks:
`ruff check .`
`python3 -m pytest -q tests/test_ollama_panel_dryrun.py`

## Final response format

Return:

```markdown
## Summary
## What was built/changed
## What was not run
## Evidence states
## Files created/modified
## Commands run
## Remaining blockers
## Recommendation
## Next best prompt
```


---

# FILE: 07_second_benchmark_scaffold.md

# Codex Prompt — 07 Second Benchmark Build-Only Scaffold

## Global hard rules

This is a **build/fix/polish only** prompt.

Do **not** run:
- validation experiments,
- synthetic generation,
- model inference,
- downloads,
- metric recomputation,
- threshold tuning,
- MMLU-Redux reruns,
- confirmatory cross-flaw / held-out runs,
- real-panel ranking analysis.

Allowed:
- static inspection,
- code scaffolding,
- dry-run or preflight commands,
- report/template creation,
- claim hygiene,
- `ruff check .`,
- targeted tests for newly added no-run code.

Do not upgrade evidence states. Do not remove caveats. Do not remove `[RESULT REQUIRED]` unless a matching local artifact already exists.


## Task

Scaffold a second benchmark path without running it.

Recommended:
- primary: GSM8K,
- fallback: TruthfulQA.

Create:
- `SECOND_BENCHMARK_BUILD_PLAN.md`
- `src/valideval/benchmarks/gsm8k.py`
- `src/valideval/benchmarks/truthfulqa.py`
- `configs/benchmarks/gsm8k_audit.yaml`
- `configs/benchmarks/truthfulqa_audit.yaml`
- CLI `benchmark-preflight --dry-run`
- `tests/test_second_benchmark_preflight.py`

Loaders should support schema validation and fixtures only. No download/evaluation.

Update paper with:
`[RESULT REQUIRED: second benchmark real-panel audit]`.

Allowed checks:
`ruff check .`
`python3 -m pytest -q tests/test_second_benchmark_preflight.py`

## Final response format

Return:

```markdown
## Summary
## What was built/changed
## What was not run
## Evidence states
## Files created/modified
## Commands run
## Remaining blockers
## Recommendation
## Next best prompt
```


---

# FILE: 08_calibration_logprob_infra.md

# Codex Prompt — 08 Calibration / Logprob Infrastructure, No Analysis

## Global hard rules

This is a **build/fix/polish only** prompt.

Do **not** run:
- validation experiments,
- synthetic generation,
- model inference,
- downloads,
- metric recomputation,
- threshold tuning,
- MMLU-Redux reruns,
- confirmatory cross-flaw / held-out runs,
- real-panel ranking analysis.

Allowed:
- static inspection,
- code scaffolding,
- dry-run or preflight commands,
- report/template creation,
- claim hygiene,
- `ruff check .`,
- targeted tests for newly added no-run code.

Do not upgrade evidence states. Do not remove caveats. Do not remove `[RESULT REQUIRED]` unless a matching local artifact already exists.


## Task

Build calibration/logprob plumbing, no metrics.

Create:
- `src/valideval/calibration/logprob_schema.py`
- `src/valideval/calibration/preflight.py`
- `configs/calibration/mmlu_logprob_calibration.yaml`
- CLI `calibration-preflight --dry-run`
- `templates/reports/CALIBRATION_REPORT_TEMPLATE.md`
- `paper/tables/calibration_template.tex`
- `tests/test_calibration_preflight.py`
- `CALIBRATION_INFRASTRUCTURE_BUILD_REPORT.md`

Schema fields:
benchmark, item_id, model_id, selected_answer, gold_answer, correct, logprob_selected, logprob_gold, option_logprobs, source, metadata.

Future metrics listed only:
ECE, adaptive ECE, Brier, NLL, accuracy-confidence curve, calibration by subject, calibration by diagnostic flag.

Do not compute metrics.

Allowed checks:
`ruff check .`
`python3 -m pytest -q tests/test_calibration_preflight.py`

## Final response format

Return:

```markdown
## Summary
## What was built/changed
## What was not run
## Evidence states
## Files created/modified
## Commands run
## Remaining blockers
## Recommendation
## Next best prompt
```


---

# FILE: 09_power_materiality_scaffold.md

# Codex Prompt — 09 Power and Materiality Scaffold

## Global hard rules

This is a **build/fix/polish only** prompt.

Do **not** run:
- validation experiments,
- synthetic generation,
- model inference,
- downloads,
- metric recomputation,
- threshold tuning,
- MMLU-Redux reruns,
- confirmatory cross-flaw / held-out runs,
- real-panel ranking analysis.

Allowed:
- static inspection,
- code scaffolding,
- dry-run or preflight commands,
- report/template creation,
- claim hygiene,
- `ruff check .`,
- targeted tests for newly added no-run code.

Do not upgrade evidence states. Do not remove caveats. Do not remove `[RESULT REQUIRED]` unless a matching local artifact already exists.


## Task

Build power/materiality infrastructure without simulations.

Create:
- `POWER_AND_MATERIALITY_ANALYSIS_PLAN.md`
- `src/valideval/statistics/power_materiality.py`
- `configs/statistics/power_materiality_mmlu.yaml`
- CLI `power-materiality-preflight --dry-run`
- `templates/reports/POWER_MATERIALITY_REPORT_TEMPLATE.md`
- `paper/tables/power_materiality_template.tex`
- `tests/test_power_materiality_preflight.py`

Future metrics listed only:
minimum detectable effect, expected CI width, sample-size/item-count sensitivity, false-positive budget, materiality threshold, detectability vs materiality gap.

Paper placeholders:
- `[RESULT REQUIRED: synthetic-harness power analysis]`
- `[RESULT REQUIRED: materiality threshold validation]`.

Allowed checks:
`ruff check .`
`python3 -m pytest -q tests/test_power_materiality_preflight.py`

## Final response format

Return:

```markdown
## Summary
## What was built/changed
## What was not run
## Evidence states
## Files created/modified
## Commands run
## Remaining blockers
## Recommendation
## Next best prompt
```


---

# FILE: 10_mmlu_redux_alignment_upgrade.md

# Codex Prompt — 10 MMLU-Redux Direct/Hash Alignment Upgrade Plan

## Global hard rules

This is a **build/fix/polish only** prompt.

Do **not** run:
- validation experiments,
- synthetic generation,
- model inference,
- downloads,
- metric recomputation,
- threshold tuning,
- MMLU-Redux reruns,
- confirmatory cross-flaw / held-out runs,
- real-panel ranking analysis.

Allowed:
- static inspection,
- code scaffolding,
- dry-run or preflight commands,
- report/template creation,
- claim hygiene,
- `ruff check .`,
- targeted tests for newly added no-run code.

Do not upgrade evidence states. Do not remove caveats. Do not remove `[RESULT REQUIRED]` unless a matching local artifact already exists.


## Task

Build a direct/hash alignment preflight. Do not download or rerun validation.

Create:
- `MMLU_REDUX_DIRECT_HASH_ALIGNMENT_PLAN.md`
- `src/valideval/validation/mmlu_redux_alignment_preflight.py`
- CLI `mmlu-redux-alignment-preflight --dry-run`
- `tests/test_mmlu_redux_alignment_preflight.py`

The preflight should inspect local schemas and report whether direct ID or stable hash fields exist. It must not expose raw MMLU question text.

Update:
- `MMLU_EVIDENCE_GATE_REPORT.md`
- `paper/appendices/mmlu_redux_evidence_appendix.md`
- `paper/limitations.md`
- `CLAIMS_LEDGER_NEURIPS.md`

Keep claims blocked until direct/hash alignment exists.

Allowed checks:
`ruff check .`
`python3 -m pytest -q tests/test_mmlu_redux_alignment_preflight.py`

## Final response format

Return:

```markdown
## Summary
## What was built/changed
## What was not run
## Evidence states
## Files created/modified
## Commands run
## Remaining blockers
## Recommendation
## Next best prompt
```


---

# FILE: 11_synthetic_confirmatory_consolidation.md

# Codex Prompt — 11 Synthetic Confirmatory Consolidation, No Execution

## Global hard rules

This is a **build/fix/polish only** prompt.

Do **not** run:
- validation experiments,
- synthetic generation,
- model inference,
- downloads,
- metric recomputation,
- threshold tuning,
- MMLU-Redux reruns,
- confirmatory cross-flaw / held-out runs,
- real-panel ranking analysis.

Allowed:
- static inspection,
- code scaffolding,
- dry-run or preflight commands,
- report/template creation,
- claim hygiene,
- `ruff check .`,
- targeted tests for newly added no-run code.

Do not upgrade evidence states. Do not remove caveats. Do not remove `[RESULT REQUIRED]` unless a matching local artifact already exists.


## Task

Consolidate preregistered cross-flaw/held-out confirmatory run surfaces.

Inspect:
- `PREREGISTERED_CROSS_FLAW_HELDOUT_INVESTIGATION_PLAN.md`
- `CROSS_FLAW_AND_HELDOUT_FAILURE_CASES.md`
- `PREREGISTRATION_REVIEW_AUDIT.md`
- `CONFIRMATORY_RUN_COMMAND_MANIFEST.md`
- `RUNBOOK_CONFIRMATORY_SYNTHETIC_VALIDATION.md`
- `STATIC_CONFIRMATORY_PREFLIGHT_REPORT.md`
- report templates
- `SYNTHETIC_EVIDENCE_STATUS_TABLE.md`
- `CLAIMS_LEDGER_NEURIPS.md`

Create:
`SYNTHETIC_CONFIRMATORY_NO_RUN_CONSOLIDATION.md`

Verdict:
- `CONFIRMATORY_SURFACE_READY`
- `NEEDS_DOC_FIXES`
- `NOT_READY`

Allowed checks:
`python3 scripts/preflight_confirmatory_synthetic.py`
`ruff check .`
`python3 -m pytest -q tests/test_preflight_confirmatory_synthetic.py`

This preflight is static only. Do not run validation.

## Final response format

Return:

```markdown
## Summary
## What was built/changed
## What was not run
## Evidence states
## Files created/modified
## Commands run
## Remaining blockers
## Recommendation
## Next best prompt
```


---

# FILE: 12_related_work_rewrite.md

# Codex Prompt — 12 Related Work and Construct-Validity Rewrite

## Global hard rules

This is a **build/fix/polish only** prompt.

Do **not** run:
- validation experiments,
- synthetic generation,
- model inference,
- downloads,
- metric recomputation,
- threshold tuning,
- MMLU-Redux reruns,
- confirmatory cross-flaw / held-out runs,
- real-panel ranking analysis.

Allowed:
- static inspection,
- code scaffolding,
- dry-run or preflight commands,
- report/template creation,
- claim hygiene,
- `ruff check .`,
- targeted tests for newly added no-run code.

Do not upgrade evidence states. Do not remove caveats. Do not remove `[RESULT REQUIRED]` unless a matching local artifact already exists.


## Task

Write serious related work and positioning.

Create/update:
- `paper/related_work.md`
- `paper/sections/02_related_work.tex`
- `RELATED_WORK_POSITIONING_MATRIX.md`
- `RELATED_WORK_TODO_CITATIONS.md`

Cover:
construct validity/psychometrics, benchmark validity critique, HELM, lm-eval-harness, OpenCompass, Inspect AI, MMLU/MMLU-Redux/MMLU-Pro/GPQA, tinyBenchmarks, IRT-for-eval, contamination, shortcut/partial-input, prompt sensitivity, calibration, benchmark saturation, LLM-as-judge reliability, measurement-instrument validation.

Do not claim:
- first benchmark validity toolkit,
- replacement for HELM/lm-eval/OpenCompass,
- all diagnostics validated,
- real benchmark error detection.

Positioning sentence:
> ValidEval is not another leaderboard runner; it is a diagnostic-validation and claim-gating framework for benchmark-validity diagnostics.

Allowed checks:
`ruff check .`

## Final response format

Return:

```markdown
## Summary
## What was built/changed
## What was not run
## Evidence states
## Files created/modified
## Commands run
## Remaining blockers
## Recommendation
## Next best prompt
```


---

# FILE: 13_claims_ledger_sync.md

# Codex Prompt — 13 Claims Ledger and Paper Sync

## Global hard rules

This is a **build/fix/polish only** prompt.

Do **not** run:
- validation experiments,
- synthetic generation,
- model inference,
- downloads,
- metric recomputation,
- threshold tuning,
- MMLU-Redux reruns,
- confirmatory cross-flaw / held-out runs,
- real-panel ranking analysis.

Allowed:
- static inspection,
- code scaffolding,
- dry-run or preflight commands,
- report/template creation,
- claim hygiene,
- `ruff check .`,
- targeted tests for newly added no-run code.

Do not upgrade evidence states. Do not remove caveats. Do not remove `[RESULT REQUIRED]` unless a matching local artifact already exists.


## Task

Synchronize paper claims with evidence states.

Inspect:
`CLAIMS_LEDGER_NEURIPS.md`, `paper/CLAIMS_LEDGER.md`, `paper/claims.md`, `paper/abstract.md`, `paper/introduction.md`, `paper/experiments.md`, `paper/diagnostic_validation.md`, `paper/limitations.md`, `paper/sections/*`, `MMLU_EVIDENCE_GATE_REPORT.md`, `SYNTHETIC_EVIDENCE_STATUS_TABLE.md`.

Search for risky phrases:
detects MMLU errors, MMLU-Redux validation succeeded, validated all diagnostics, proves, solves, strong external validation, real benchmark error detection, all diagnostics generalize, cross-flaw solved, held-out solved, GPQA establishes, domain packs validated.

Create:
`CLAIMS_LEDGER_PAPER_SYNC_AUDIT.md`

Verdict:
- `CLAIMS_SYNCED`
- `CLAIMS_NEED_MINOR_FIXES`
- `CLAIMS_UNSAFE`

Only edit claim wording. Do not change empirical values.

Allowed checks:
`ruff check .`

## Final response format

Return:

```markdown
## Summary
## What was built/changed
## What was not run
## Evidence states
## Files created/modified
## Commands run
## Remaining blockers
## Recommendation
## Next best prompt
```


---

# FILE: 14_reviewer_packet_slimming.md

# Codex Prompt — 14 Reviewer Packet Slimming and Repo Hygiene

## Global hard rules

This is a **build/fix/polish only** prompt.

Do **not** run:
- validation experiments,
- synthetic generation,
- model inference,
- downloads,
- metric recomputation,
- threshold tuning,
- MMLU-Redux reruns,
- confirmatory cross-flaw / held-out runs,
- real-panel ranking analysis.

Allowed:
- static inspection,
- code scaffolding,
- dry-run or preflight commands,
- report/template creation,
- claim hygiene,
- `ruff check .`,
- targeted tests for newly added no-run code.

Do not upgrade evidence states. Do not remove caveats. Do not remove `[RESULT REQUIRED]` unless a matching local artifact already exists.


## Task

Keep reviewer packet lean and reduce process-theater risk.

Inspect:
`REVIEWER_PACKET_MANIFEST.md`, `REVIEWER_READING_GUIDE.md`, `ARTIFACT_EXCLUSION_POLICY.md`, `REVIEWER_PACKET_ZIP_AUDIT.md`, `REVIEWER_PACKET_HANDOFF_NOTE.md`, `scripts/make_reviewer_packet.py`, `tests/test_make_reviewer_packet.py`.

Create:
`REVIEWER_PACKET_SLIMMING_AUDIT.md`

Check packet includes only:
- paper,
- README,
- core claims ledger,
- synthetic evidence table,
- MMLU evidence gate,
- preregistration plan,
- preflight report,
- runbook/manifest,
- relevant configs,
- core source code,
- tests.

Exclude:
raw/cache artifacts, huge result dirs, duplicate audits, exploratory prompt packs, obsolete run logs, stale notes, `.jsonl`, large CSVs.

Verdict:
- `PACKET_SURFACE_CLEAN`
- `PACKET_NEEDS_REBUILD`
- `PACKET_TOO_BROAD`

Run:
`ruff check .`
`python3 -m pytest -q tests/test_make_reviewer_packet.py`

## Final response format

Return:

```markdown
## Summary
## What was built/changed
## What was not run
## Evidence states
## Files created/modified
## Commands run
## Remaining blockers
## Recommendation
## Next best prompt
```


---

# FILE: 15_final_no_run_readiness_audit.md

# Codex Prompt — 15 Final No-Run Readiness Audit

## Global hard rules

This is a **build/fix/polish only** prompt.

Do **not** run:
- validation experiments,
- synthetic generation,
- model inference,
- downloads,
- metric recomputation,
- threshold tuning,
- MMLU-Redux reruns,
- confirmatory cross-flaw / held-out runs,
- real-panel ranking analysis.

Allowed:
- static inspection,
- code scaffolding,
- dry-run or preflight commands,
- report/template creation,
- claim hygiene,
- `ruff check .`,
- targeted tests for newly added no-run code.

Do not upgrade evidence states. Do not remove caveats. Do not remove `[RESULT REQUIRED]` unless a matching local artifact already exists.


## Task

Perform final build-only readiness audit. No experiments.

Create:
`FINAL_NO_RUN_READINESS_AUDIT.md`

Include:
1. Executive summary
2. Build-only phases completed
3. Static checks
4. Dry-run surfaces
5. Evidence states
6. Claims status
7. Paper status
8. Reviewer packet status
9. Remaining build gaps
10. Remaining `[RESULT REQUIRED]`
11. Future authorized runs
12. Final verdict

Verdict:
- `NO_RUN_BUILD_READY`
- `NEEDS_MINOR_BUILD_FIXES`
- `NOT_READY`

Allowed targeted tests if files exist:
- `tests/test_real_panel_dryrun_commands.py`
- `tests/test_real_panel_baselines_scaffold.py`
- `tests/test_ollama_panel_dryrun.py`
- `tests/test_second_benchmark_preflight.py`
- `tests/test_calibration_preflight.py`
- `tests/test_power_materiality_preflight.py`
- `tests/test_mmlu_redux_alignment_preflight.py`
- `tests/test_preflight_confirmatory_synthetic.py`
- `tests/test_make_reviewer_packet.py`

Always run:
`ruff check .`

Do not run validation.

## Final response format

Return:

```markdown
## Summary
## What was built/changed
## What was not run
## Evidence states
## Files created/modified
## Commands run
## Remaining blockers
## Recommendation
## Next best prompt
```


---

# FILE: 16_later_run_plan.md

# Codex Prompt — 16 Master Later Run Plan

## Global hard rules

This is a **build/fix/polish only** prompt.

Do **not** run:
- validation experiments,
- synthetic generation,
- model inference,
- downloads,
- metric recomputation,
- threshold tuning,
- MMLU-Redux reruns,
- confirmatory cross-flaw / held-out runs,
- real-panel ranking analysis.

Allowed:
- static inspection,
- code scaffolding,
- dry-run or preflight commands,
- report/template creation,
- claim hygiene,
- `ruff check .`,
- targeted tests for newly added no-run code.

Do not upgrade evidence states. Do not remove caveats. Do not remove `[RESULT REQUIRED]` unless a matching local artifact already exists.


## Task

Create master plan for later execution. Do not run anything.

Create:
- `MASTER_LATER_RUN_PLAN.md`
- `LATER_RUN_APPROVAL_CHECKLIST.md`

Priority order:
1. one focused real-panel finding run,
2. preregistered confirmatory cross-flaw,
3. preregistered confirmatory held-out,
4. calibration/logprob analysis,
5. power/materiality analysis,
6. second benchmark.

Do-not-run-together rule:
Do not execute all evidence families in one mega batch. Each run must have:
- command,
- expected runtime,
- inputs,
- preflight status,
- evidence state before,
- claim state before,
- stop rule,
- user approval requirement.

Update `README.md` and `paper/NEURIPS_SUBMISSION_PLAN.md` only with pointers.

Run:
`ruff check .`

## Final response format

Return:

```markdown
## Summary
## What was built/changed
## What was not run
## Evidence states
## Files created/modified
## Commands run
## Remaining blockers
## Recommendation
## Next best prompt
```


---

# FILE: README_INDEX.md

# ValidEval No-Run Fix/Build Prompt Pack

This pack is for the current ValidEval situation after harsh review feedback and later HELM MMLU progress.

## Strategic diagnosis

The strongest paper is not “ValidEval detects benchmark errors.” The strongest paper is:

> Benchmark-validity diagnostics are themselves measurement instruments. They need validation for sensitivity, specificity, transfer, false-positive control, materiality, and claim authorization before they can support benchmark-validity claims.

## Current corrected state

- Earlier “mock-only” criticism is partly stale: a real 39-model HELM MMLU panel exists.
- MMLU-Redux remains weak/negative external validation; no detection-success claim is allowed.
- Cross-flaw specificity and held-out transfer remain weak/mixed.
- Confirmatory runs are deferred.
- The next build target is a real-panel finding engine, paper tightening, baselines, dry-run scaffolds, calibration/power infrastructure, and release slimming.

## Prompt order

| # | File | Purpose | Time |
|---:|---|---|---:|
| 00 | `00_global_no_run_rules.md` | Lock no-run rules and evidence states | 20–45 min |
| 01 | `01_paper_thesis_reframe.md` | Reframe paper around diagnostic validation | 1–3 hr |
| 02 | `02_surface_area_freeze.md` | Freeze/defer product sprawl | 1–3 hr |
| 03 | `03_real_panel_finding_engine.md` | Build dry-run real-panel finding engine | 3–8 hr |
| 04 | `04_baselines_ablations_scaffold.md` | Build baseline/ablation scaffolds | 3–6 hr |
| 05 | `05_figures_tables_templates.md` | Build result templates only | 2–5 hr |
| 06 | `06_ollama_panel_dryrun.md` | Wire local model panel dry-run path | 4–8 hr |
| 07 | `07_second_benchmark_scaffold.md` | Scaffold GSM8K/TruthfulQA no-run path | 4–8 hr |
| 08 | `08_calibration_logprob_infra.md` | Build calibration/logprob infrastructure | 4–8 hr |
| 09 | `09_power_materiality_scaffold.md` | Build power/materiality preflight | 3–6 hr |
| 10 | `10_mmlu_redux_alignment_upgrade.md` | Build direct/hash alignment preflight | 2–5 hr |
| 11 | `11_synthetic_confirmatory_consolidation.md` | Consolidate synthetic confirmatory no-run surface | 2–4 hr |
| 12 | `12_related_work_rewrite.md` | Write serious related work | 3–8 hr |
| 13 | `13_claims_ledger_sync.md` | Sync claims with evidence | 1–3 hr |
| 14 | `14_reviewer_packet_slimming.md` | Slim reviewer packet / repo hygiene | 2–5 hr |
| 15 | `15_final_no_run_readiness_audit.md` | Final no-run readiness audit | 1–3 hr |
| 16 | `16_later_run_plan.md` | Master later execution order | 1–2 hr |

## What this pack does not do

It does not execute any empirical run. It builds the safest path to run later.
