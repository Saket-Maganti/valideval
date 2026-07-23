# Prompt 15 — NeurIPS Paper Draft Scaffold: Evidence-First, No Hype

## Estimated working time / runtime

| Mode | Estimate |
|---|---:|
| Human/Codex working time | 4–10 hr scaffold; 20–40 hr human revision later |
| CPU runtime | <1 min |
| GPU runtime | Not required |
| Expensive generation? | No |
| Run now or later? | Now |

## Purpose

Starts the actual paper while marking missing results explicitly.

---

Create real paper scaffold. Do not invent results.

## Global hard rules
- Do not add feature sprawl.
- Do not run expensive Ollama/LLM generation unless explicitly requested.
- Do not use paid or closed APIs.
- Do not expose raw GPQA text.
- Do not make real benchmark claims from toy/fixture/chance-level panels.
- Keep GPQA local-panel results labeled preliminary/protocol-only.
- Keep claims tied to evidence.

## Create/update paper files
`paper/title.md`, `abstract.md`, `introduction.md`, `related_work.md`, `method.md`, `diagnostic_validation.md`, `external_validation.md`, `gpqa_protocol_demo.md`, `experiments.md`, `limitations.md`, `ethics_and_data.md`, `reviewer_risk.md`, `claims.md`, `figures_plan.md`, `tables_plan.md`, `submission_checklist.md`.

## Main claim
ValidEval treats benchmark-validity diagnostics as measurement instruments calibrated for sensitivity, FPR, specificity, uncertainty, and materiality.

## Required placeholders
`[RESULT REQUIRED: cross-flaw confusion matrix]`, `[RESULT REQUIRED: MMLU-Redux external validation precision/recall]`, `[RESULT REQUIRED: wide response matrix counts]`, `[RESULT REQUIRED: real 2PL IRT if used]`.

## Contributions
Limit to 4: computable framework; validation harness; external validation; offline audit protocol/report cards/claims ledger.

## Limitations
Synthetic circularity, threshold transfer, panel validity, GPQA small-panel limitation, unvalidated domain packs, no universal validity conclusion.
