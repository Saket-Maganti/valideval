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
