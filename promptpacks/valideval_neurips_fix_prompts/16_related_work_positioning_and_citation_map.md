# Prompt 16 — Related Work Positioning and Citation Map

## Estimated working time / runtime

| Mode | Estimate |
|---|---:|
| Human/Codex working time | 3–8 hr |
| CPU runtime | <1 min |
| GPU runtime | Not required |
| Expensive generation? | No |
| Run now or later? | Now; human verify citations later |

## Purpose

Prevents attacks that ValidEval ignores prior benchmark/eval/psychometrics work.

---

Create related-work map. Do not fabricate bibliographic details. Use placeholders if uncertain.

## Global hard rules
- Do not add feature sprawl.
- Do not run expensive Ollama/LLM generation unless explicitly requested.
- Do not use paid or closed APIs.
- Do not expose raw GPQA text.
- Do not make real benchmark claims from toy/fixture/chance-level panels.
- Keep GPQA local-panel results labeled preliminary/protocol-only.
- Keep claims tied to evidence.

## Create
`paper/related_work_map.md`, `paper/citation_checklist.md`, `paper/positioning_table.md`, `paper/related_work_claim_boundaries.md`.

## Cover
HELM, lm-eval-harness, OpenCompass, Inspect AI, RAGAS, DeepEval, tinyBenchmarks, BetterBench, ECBD/evidence-centered benchmark design, IRT for NLP/item analysis, contamination detection, saturation, MMLU-Redux, GSM1k/GSM8K, LLM-as-judge reliability, Messick, Cronbach & Meehl, AERA/APA/NCME Standards.

## Table columns
Work, overlap, difference, must cite for, do not falsely claim.

## Boundaries
State ValidEval is not first eval harness, not first IRT, not first benchmark-validity critique. Differentiator: validated diagnostics + evidence governance + external ground truth.
