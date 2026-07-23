# Prompt 03 — Generic Wide Response Matrix Importer

## Estimated working time / runtime

| Mode | Estimate |
|---|---:|
| Human/Codex working time | 3–6 hr |
| CPU runtime | 1–10 min fixtures; 10–60 min large local files |
| GPU runtime | Not required |
| Expensive generation? | No |
| Run now or later? | Build now; real import later |

## Purpose

Builds the critical importer for published per-instance predictions, avoiding LLM generation.

---

You are working inside `valideval`.

## Global hard rules
- Do not add feature sprawl.
- Do not run expensive Ollama/LLM generation unless explicitly requested.
- Do not use paid or closed APIs.
- Do not expose raw GPQA text.
- Do not make real benchmark claims from toy/fixture/chance-level panels.
- Keep GPQA local-panel results labeled preliminary/protocol-only.
- Keep claims tied to evidence.

## Create module
`src/valideval/importers/__init__.py`, `wide_matrix.py`, `schemas.py`.

## Normalized schema
Each row must become JSONL with: benchmark, subset, item_id, model_id, prediction, gold, correct, source, source_file, metadata.

## Supported input formats
1. generic JSONL with item/model/prediction/gold.
2. generic CSV with item_id, model_id, prediction, gold, subset.
3. model-major JSONL with model_id and predictions list.

## CLI
Add `import-wide-predictions` and `matrix-from-wide-predictions`.

## Requirements
No silent row dropping; row-numbered validation errors; stable model/item ordering; duplicate/missing report; no item text required.

## Fixtures/tests
Create `examples/wide_predictions_mock.jsonl`, `.csv`, and `tests/test_wide_matrix_importer.py`. Test JSONL/CSV import, duplicate detection, missing fields, matrix shape, stable ordering. Run targeted tests and ruff.
