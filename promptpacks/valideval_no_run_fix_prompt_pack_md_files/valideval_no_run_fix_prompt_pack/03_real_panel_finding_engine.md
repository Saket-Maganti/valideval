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
