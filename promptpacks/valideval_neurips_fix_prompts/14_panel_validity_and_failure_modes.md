# Prompt 14 — Panel Validity Diagnostics and Failure-Mode Guardrails

## Estimated working time / runtime

| Mode | Estimate |
|---|---:|
| Human/Codex working time | 3–6 hr |
| CPU runtime | 5–30 min |
| GPU runtime | Not required |
| Expensive generation? | No |
| Run now or later? | Now |

## Purpose

Prevents repeating the GPQA chance-panel mistake.

---

Add panel validity guardrails.

## Global hard rules
- Do not add feature sprawl.
- Do not run expensive Ollama/LLM generation unless explicitly requested.
- Do not use paid or closed APIs.
- Do not expose raw GPQA text.
- Do not make real benchmark claims from toy/fixture/chance-level panels.
- Keep GPQA local-panel results labeled preliminary/protocol-only.
- Keep claims tied to evidence.

## Create/update
`src/valideval/diagnostics/panel_validity.py`, `docs/panel_validity_requirements.md`.

## Checks
Number of models/items, accuracy distribution, spread around chance, variance, fraction near chance, missingness, suitability for IRT/item discrimination/ranking.

## CLI
`panel-validity --matrix path/to/matrix.csv --chance 0.25 --output results/<bench>/panel_validity/`

## Behavior
Near-chance panels block item-discrimination/IRT findings and label results protocol/demo only.

## Tests
All-chance fail, wide ability pass, small-n blocks IRT, high missingness blocks.
