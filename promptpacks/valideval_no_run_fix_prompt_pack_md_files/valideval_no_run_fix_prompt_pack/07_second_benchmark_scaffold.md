# Codex Prompt — 07 Second Benchmark Build-Only Scaffold

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

Scaffold a second benchmark path without running it.

Recommended:
- primary: GSM8K,
- fallback: TruthfulQA.

Create:
- `SECOND_BENCHMARK_BUILD_PLAN.md`
- `src/valideval/benchmarks/gsm8k.py`
- `src/valideval/benchmarks/truthfulqa.py`
- `configs/benchmarks/gsm8k_audit.yaml`
- `configs/benchmarks/truthfulqa_audit.yaml`
- CLI `benchmark-preflight --dry-run`
- `tests/test_second_benchmark_preflight.py`

Loaders should support schema validation and fixtures only. No download/evaluation.

Update paper with:
`[RESULT REQUIRED: second benchmark real-panel audit]`.

Allowed checks:
`ruff check .`
`python3 -m pytest -q tests/test_second_benchmark_preflight.py`

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
