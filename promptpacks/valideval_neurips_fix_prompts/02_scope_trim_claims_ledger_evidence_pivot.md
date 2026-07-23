# Prompt 02 — Scope Trim, Claims Ledger, and Evidence Pivot

## Estimated working time / runtime

| Mode | Estimate |
|---|---:|
| Human/Codex working time | 1–2 hr |
| CPU runtime | <1 min |
| GPU runtime | Not required |
| Expensive generation? | No |
| Run now or later? | Now |

## Purpose

Converts the brutal review into an evidence-first plan and prevents overclaiming.

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

## Create/update
- `CLAIMS_LEDGER_NEURIPS.md`
- `NEURIPS_EVIDENCE_PIVOT.md`
- `DO_NOT_DO_NEURIPS.md`
- `GPQA_SMALL_PANEL_LIMITATION_NOTE.md`

## Claims ledger
Create a table with columns: claim, current support, evidence needed, status, allowed in paper. Include claims about ValidEval diagnostics, synthetic validation, external validation, GPQA, MMLU, domain packs, predictive/Goodhart, usability, reproducibility. Mark unsupported claims honestly.

## Evidence pivot
State that the paper-saving route is: wide response matrix importer → MMLU-Redux external validation → cross-flaw specificity → real/wide-panel IRT → evidence-first paper.

## Do-not-do
Freeze domain packs, dashboard, badges, certificates, more GPQA small-Ollama loops, embedding dedup unless evidence-critical, and new diagnostics.

## GPQA limitation note
State small local GPQA is protocol feasibility only, not item-validity evidence.

No tests unless code changes.
