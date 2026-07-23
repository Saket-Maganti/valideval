# Prompt 04 — Published Per-Instance Details Importers for Leaderboard / HELM-style Data

## Estimated working time / runtime

| Mode | Estimate |
|---|---:|
| Human/Codex working time | 4–8 hr |
| CPU runtime | 10–90 min depending on local data size |
| GPU runtime | Not required |
| Expensive generation? | No |
| Run now or later? | Build now; real import later |

## Purpose

Adds adapters for published prediction-detail files stored locally.

---

Build adapters for local published per-instance prediction details. Do not download data.

## Global hard rules
- Do not add feature sprawl.
- Do not run expensive Ollama/LLM generation unless explicitly requested.
- Do not use paid or closed APIs.
- Do not expose raw GPQA text.
- Do not make real benchmark claims from toy/fixture/chance-level panels.
- Keep GPQA local-panel results labeled preliminary/protocol-only.
- Keep claims tied to evidence.

## Add module
`src/valideval/importers/leaderboard_details.py`, `helm_details.py`.

## Modes
`leaderboard_jsonl`, `leaderboard_csv`, `helm_jsonl`, `helm_json`, `auto`.

## CLI
`python3 -m valideval import-published-details --benchmark mmlu --input path/to/details.jsonl --format auto --output cache/mmlu/wide/predictions.jsonl --mapping-report results/mmlu/import_mapping_report.md`

## Mapping flexibility
Support common fields: model/model_id, task/benchmark, subset/subject, doc_id/sample_id/item_id, prediction/pred/answer/filtered_resps, gold/target/correct_answer, exact_match/correct/acc.

## Privacy default
Discard prompt/question text by default. Only keep text if `--include-text` is explicitly passed.

## Reports/tests
Write import summary JSON/MD with hashes, discarded text fields, rows/models/items/subsets. Add tiny tests.
