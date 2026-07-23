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
