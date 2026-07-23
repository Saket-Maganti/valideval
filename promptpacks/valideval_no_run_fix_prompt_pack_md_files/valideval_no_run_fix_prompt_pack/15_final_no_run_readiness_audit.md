# Codex Prompt — 15 Final No-Run Readiness Audit

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

Perform final build-only readiness audit. No experiments.

Create:
`FINAL_NO_RUN_READINESS_AUDIT.md`

Include:
1. Executive summary
2. Build-only phases completed
3. Static checks
4. Dry-run surfaces
5. Evidence states
6. Claims status
7. Paper status
8. Reviewer packet status
9. Remaining build gaps
10. Remaining `[RESULT REQUIRED]`
11. Future authorized runs
12. Final verdict

Verdict:
- `NO_RUN_BUILD_READY`
- `NEEDS_MINOR_BUILD_FIXES`
- `NOT_READY`

Allowed targeted tests if files exist:
- `tests/test_real_panel_dryrun_commands.py`
- `tests/test_real_panel_baselines_scaffold.py`
- `tests/test_ollama_panel_dryrun.py`
- `tests/test_second_benchmark_preflight.py`
- `tests/test_calibration_preflight.py`
- `tests/test_power_materiality_preflight.py`
- `tests/test_mmlu_redux_alignment_preflight.py`
- `tests/test_preflight_confirmatory_synthetic.py`
- `tests/test_make_reviewer_packet.py`

Always run:
`ruff check .`

Do not run validation.

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
