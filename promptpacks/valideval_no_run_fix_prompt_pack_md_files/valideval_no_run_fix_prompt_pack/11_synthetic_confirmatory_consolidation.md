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
