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
