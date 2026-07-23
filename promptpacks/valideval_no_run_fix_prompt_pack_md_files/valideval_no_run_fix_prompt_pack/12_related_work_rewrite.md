# Codex Prompt — 12 Related Work and Construct-Validity Rewrite

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

Write serious related work and positioning.

Create/update:
- `paper/related_work.md`
- `paper/sections/02_related_work.tex`
- `RELATED_WORK_POSITIONING_MATRIX.md`
- `RELATED_WORK_TODO_CITATIONS.md`

Cover:
construct validity/psychometrics, benchmark validity critique, HELM, lm-eval-harness, OpenCompass, Inspect AI, MMLU/MMLU-Redux/MMLU-Pro/GPQA, tinyBenchmarks, IRT-for-eval, contamination, shortcut/partial-input, prompt sensitivity, calibration, benchmark saturation, LLM-as-judge reliability, measurement-instrument validation.

Do not claim:
- first benchmark validity toolkit,
- replacement for HELM/lm-eval/OpenCompass,
- all diagnostics validated,
- real benchmark error detection.

Positioning sentence:
> ValidEval is not another leaderboard runner; it is a diagnostic-validation and claim-gating framework for benchmark-validity diagnostics.

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
