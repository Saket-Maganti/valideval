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
