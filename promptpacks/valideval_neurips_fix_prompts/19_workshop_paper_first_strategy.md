# Prompt 19 — NeurIPS Workshop Paper Strategy Before Main Submission

## Estimated working time / runtime

| Mode | Estimate |
|---|---:|
| Human/Codex working time | 2–5 hr |
| CPU runtime | <1 min |
| GPU runtime | Not required |
| Expensive generation? | No |
| Run now or later? | Optional before main |

## Purpose

Creates lower-risk workshop plan around validation harness.

---

Prepare workshop-first strategy.

## Global hard rules
- Do not add feature sprawl.
- Do not run expensive Ollama/LLM generation unless explicitly requested.
- Do not use paid or closed APIs.
- Do not expose raw GPQA text.
- Do not make real benchmark claims from toy/fixture/chance-level panels.
- Keep GPQA local-panel results labeled preliminary/protocol-only.
- Keep claims tied to evidence.

## Create
`WORKSHOP_FIRST_STRATEGY.md` and `paper/workshop/outline.md`, `abstract.md`, `experiments_needed.md`, `submission_checklist.md`.

## Scope
Focus on diagnostic validation harness, synthetic flaw injection, cross-flaw specificity, claims ledger, evidence states.

## Exclude
Domain packs, dashboard, badges, GPQA item claims, unsupported MMLU claims.

## Output
Possible workshop themes, minimum experiments, page plan, feedback questions, how this strengthens NeurIPS main.
