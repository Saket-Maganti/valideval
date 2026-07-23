# Prompt 05 — MMLU-Redux Ground-Truth Ingestion Scaffold

## Estimated working time / runtime

| Mode | Estimate |
|---|---:|
| Human/Codex working time | 2–4 hr |
| CPU runtime | 1–5 min fixtures; 5–20 min real files |
| GPU runtime | Not required |
| Expensive generation? | No |
| Run now or later? | Now/build-only |

## Purpose

Creates external ground-truth ingestion for independently documented MMLU flaws.

---

Build MMLU-Redux-style ground-truth ingestion. Do not download real data.

## Global hard rules
- Do not add feature sprawl.
- Do not run expensive Ollama/LLM generation unless explicitly requested.
- Do not use paid or closed APIs.
- Do not expose raw GPQA text.
- Do not make real benchmark claims from toy/fixture/chance-level panels.
- Keep GPQA local-panel results labeled preliminary/protocol-only.
- Keep claims tied to evidence.

## Create module
`src/valideval/validation/external_ground_truth.py`, `mmlu_redux.py`.

## Schema
JSONL/CSV rows with benchmark, subset, item_id, issue_type, severity, source, metadata.

## CLI
`import-ground-truth --benchmark mmlu --input examples/mmlu_redux_mock.jsonl --format mmlu_redux_jsonl --output data/ground_truth/mmlu_redux_issues.normalized.jsonl`

## Validation
Require item_id, issue_type, source. Detect duplicate item/issue pairs. Warn on unknown issue types; do not drop. No item text required.

## Fixtures/tests
Create mock JSONL/CSV and `tests/test_mmlu_redux_ground_truth.py`.
