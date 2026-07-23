# Prompt 11 — GPQA Wide-Panel Reanalysis Protocol

## Estimated working time / runtime

| Mode | Estimate |
|---|---:|
| Human/Codex working time | 3–6 hr build; 30 min–3 hr run after data import |
| CPU runtime | 30 min–3 hr if wide predictions available |
| GPU runtime | Not required |
| Expensive generation? | No |
| Run now or later? | Build now; execute only with wide data |

## Purpose

Demotes small GPQA to protocol demo and prepares serious GPQA reanalysis.

---

Create a GPQA wide-panel protocol.

## Global hard rules
- Do not add feature sprawl.
- Do not run expensive Ollama/LLM generation unless explicitly requested.
- Do not use paid or closed APIs.
- Do not expose raw GPQA text.
- Do not make real benchmark claims from toy/fixture/chance-level panels.
- Keep GPQA local-panel results labeled preliminary/protocol-only.
- Keep claims tied to evidence.

## Create
`docs/protocols/gpqa_wide_panel_reanalysis_protocol.md`, `configs/audits/gpqa_wide_panel.yaml`, `GPQA_WIDE_PANEL_READINESS.md`.

## Protocol must state
Small local GPQA is not sufficient for item claims; wide matrix required; minimum model count e.g. 50+; ability spread required; no raw GPQA text in public artifacts.

## Readiness command
Add `gpqa-wide-readiness --predictions cache/gpqa/wide/predictions.jsonl --matrix cache/gpqa/wide/matrix.csv`.

## Checks
Model count, item count, accuracy distribution, ability spread, missingness, source validity.

## Tests
`tests/test_gpqa_wide_readiness.py` with all-chance fail and ability-spread pass.
