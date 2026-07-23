# Prompt 20 — Master Execution Order and Time Budget

## Estimated working time / runtime

| Mode | Estimate |
|---|---:|
| Human/Codex working time | 30–60 min |
| CPU runtime | <1 min |
| GPU runtime | Not required |
| Expensive generation? | No |
| Run now or later? | Now |

## Purpose

Builds the master schedule so you do not burn credits randomly.

---

Create master execution order and compute budget.

## Global hard rules
- Do not add feature sprawl.
- Do not run expensive Ollama/LLM generation unless explicitly requested.
- Do not use paid or closed APIs.
- Do not expose raw GPQA text.
- Do not make real benchmark claims from toy/fixture/chance-level panels.
- Keep GPQA local-panel results labeled preliminary/protocol-only.
- Keep claims tied to evidence.

## Create
`NEURIPS_FIX_PROMPTS_EXECUTION_ORDER.md`, `NEURIPS_TIME_AND_COMPUTE_BUDGET.md`.

## Table
Phase, prompt file, purpose, run now?, CPU time, GPU time, human/Codex time, blockers.

## Groups
Immediate no-run build-only; evidence infrastructure; synthetic validation; external validation; paper writing; release/review; final readiness.

## Warnings
Do not run real LLM generation through Codex; prefer importing published prediction files; feature freeze remains active.
