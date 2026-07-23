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
