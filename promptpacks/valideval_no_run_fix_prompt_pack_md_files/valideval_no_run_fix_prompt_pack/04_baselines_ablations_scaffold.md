# Codex Prompt — 04 Real-Panel Baselines and Ablations Scaffold

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

Build no-run scaffolds for reviewer-required baselines.

Create:
- `REAL_PANEL_BASELINES_PLAN.md`
- `src/valideval/real_panel/baselines.py`
- `configs/real_panel/baselines_mmlu.yaml`
- `tests/test_real_panel_baselines_scaffold.py`

Baseline plan must include:
1. accuracy-only ranking,
2. random item subset,
3. subject-stratified subset,
4. naive difficulty,
5. naive disagreement,
6. diagnostic-vs-diagnostic,
7. MMLU-Redux external label baseline,
8. subject confounding baseline.

Code must include schemas and dry-run manifests only. Computation stubs should raise `NotImplementedError` or explicit refusal.

Update paper placeholders:
- `[RESULT REQUIRED: accuracy-only baseline]`
- `[RESULT REQUIRED: random subset baseline]`
- `[RESULT REQUIRED: subject-stratified baseline]`
- `[RESULT REQUIRED: naive disagreement baseline]`
- `[RESULT REQUIRED: diagnostic-vs-diagnostic baseline]`.

Allowed checks:
`ruff check .`
`python3 -m pytest -q tests/test_real_panel_baselines_scaffold.py`

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
