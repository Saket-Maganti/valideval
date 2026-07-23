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
