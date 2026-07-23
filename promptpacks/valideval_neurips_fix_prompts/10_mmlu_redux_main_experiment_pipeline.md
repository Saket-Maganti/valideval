# Prompt 10 — MMLU-Redux Main External-Validation Experiment Pipeline

## Estimated working time / runtime

| Mode | Estimate |
|---|---:|
| Human/Codex working time | 8–16 hr build; 1–4 hr real run |
| CPU runtime | 30 min–4 hr real run depending rows/models |
| GPU runtime | Not required |
| Expensive generation? | No paid APIs |
| Run now or later? | Build now; execute after data |

## Purpose

Creates the main paper experiment: ValidEval flags versus MMLU-Redux issues.

---

Build the end-to-end MMLU-Redux validation pipeline.

## Global hard rules
- Do not add feature sprawl.
- Do not run expensive Ollama/LLM generation unless explicitly requested.
- Do not use paid or closed APIs.
- Do not expose raw GPQA text.
- Do not make real benchmark claims from toy/fixture/chance-level panels.
- Keep GPQA local-panel results labeled preliminary/protocol-only.
- Keep claims tied to evidence.

## Inputs may be missing
If `cache/mmlu/wide/predictions.jsonl`, `cache/mmlu/wide/matrix.csv`, or ground truth is missing, create readiness report and stop.

## CLI
`mmlu-redux-validation --predictions cache/mmlu/wide/predictions.jsonl --matrix cache/mmlu/wide/matrix.csv --ground-truth data/ground_truth/mmlu_redux_issues.normalized.jsonl --output results/mmlu/mmlu_redux_validation/`

## Steps
Validate matrix, run eligible diagnostics, export flags, join with ground truth, compute precision/recall/AP/AUPRC/enrichment/bootstrap CI, write paper table.

## Outputs
README.md, metrics.json, join JSONL, enrichment curve CSV, summary.md, paper_table_mmlu_redux.md.

## Tests
`tests/test_mmlu_redux_validation_pipeline.py` with tiny mock matrix/ground truth.
