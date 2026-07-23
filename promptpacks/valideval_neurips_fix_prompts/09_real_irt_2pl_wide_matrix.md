# Prompt 09 — Real IRT / 2PL on Wide Response Matrices

## Estimated working time / runtime

| Mode | Estimate |
|---|---:|
| Human/Codex working time | 6–14 hr |
| CPU runtime | 30 min–4 hr depending on matrix |
| GPU runtime | Optional; can speed PyTorch/py-irt |
| Expensive generation? | No paid APIs |
| Run now or later? | Build now; run on wide matrix later |

## Purpose

Replaces proxy item-total discrimination with credible psychometrics once matrix is wide.

---

Add a real/wide-matrix IRT path.

## Global hard rules
- Do not add feature sprawl.
- Do not run expensive Ollama/LLM generation unless explicitly requested.
- Do not use paid or closed APIs.
- Do not expose raw GPQA text.
- Do not make real benchmark claims from toy/fixture/chance-level panels.
- Keep GPQA local-panel results labeled preliminary/protocol-only.
- Keep claims tied to evidence.

## Create module
`src/valideval/psychometrics/__init__.py`, `irt_2pl.py`, `irt_reports.py`.

## Requirements
Accept rows=models, columns=items binary matrix. Fit 1PL/Rasch and 2PL if enough data. Estimate item difficulty/discrimination, model ability, uncertainty/bootstrap where feasible. Block serious IRT if <30 models or insufficient ability spread.

## CLI
`fit-irt --matrix cache/mmlu/wide/matrix.csv --model 2pl --output results/mmlu/irt_2pl/`

## Outputs
item_parameters.csv, model_abilities.csv, fit_summary.md, flags.jsonl.

## Fallback
If dependency unavailable, provide proxy baseline with explicit warning.

## Tests
Simulated matrix in `tests/test_irt_2pl.py`.
