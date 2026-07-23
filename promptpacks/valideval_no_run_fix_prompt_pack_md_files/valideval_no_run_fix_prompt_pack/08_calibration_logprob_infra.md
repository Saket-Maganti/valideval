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
