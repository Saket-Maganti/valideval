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
