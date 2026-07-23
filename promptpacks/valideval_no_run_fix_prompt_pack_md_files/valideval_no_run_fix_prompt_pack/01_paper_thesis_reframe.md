# Codex Prompt — 01 Paper Thesis Reframe Around Diagnostic Validation

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

Reframe the paper away from broad toolkit/product pitch and toward the thesis:

> ValidEval validates validity diagnostics before they license benchmark-validity claims.

Inspect:
`paper/abstract.md`, `paper/introduction.md`, `paper/experiments.md`, `paper/diagnostic_validation.md`, `paper/limitations.md`, `paper/claims.md`, `paper/related_work.md`, `paper/main.tex`, `paper/sections/*`, `CLAIMS_LEDGER_NEURIPS.md`, `MMLU_EVIDENCE_GATE_REPORT.md`, `SYNTHETIC_EVIDENCE_STATUS_TABLE.md`.

The paper should say:
- controlled synthetic validation is generator-scoped,
- cross-flaw / held-out expose failures,
- MMLU-Redux is weak/negative,
- the 39-model HELM MMLU panel is a real-panel substrate,
- ranking/diagnostic finding remains `[RESULT REQUIRED]`.

The paper must not imply:
- ValidEval detects MMLU errors,
- MMLU-Redux validation succeeded,
- cross-flaw or held-out are solved,
- synthetic validation proves real validity,
- certificates/badges/domain packs are validated contributions.

Create `PAPER_THESIS_REFRAME_AUDIT.md` with:
1. Executive summary
2. Old risky framing
3. New thesis
4. Files reviewed
5. Edits made
6. Claims allowed
7. Claims blocked
8. Remaining `[RESULT REQUIRED]`
9. Reviewer risks
10. Next build step.

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
