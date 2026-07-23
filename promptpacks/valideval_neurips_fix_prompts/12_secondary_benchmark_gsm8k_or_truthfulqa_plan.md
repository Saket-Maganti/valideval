# Prompt 12 — Secondary Benchmark Plan: GSM8K/GSM1k or TruthfulQA

## Estimated working time / runtime

| Mode | Estimate |
|---|---:|
| Human/Codex working time | 2–4 hr plan; 4–12 hr if scaffold |
| CPU runtime | 1–60 min local data |
| GPU runtime | Not required |
| Expensive generation? | No |
| Run now or later? | Plan now; execute after MMLU |

## Purpose

Plans one second case study without feature sprawl.

---

Select one secondary benchmark path.

## Global hard rules
- Do not add feature sprawl.
- Do not run expensive Ollama/LLM generation unless explicitly requested.
- Do not use paid or closed APIs.
- Do not expose raw GPQA text.
- Do not make real benchmark claims from toy/fixture/chance-level panels.
- Keep GPQA local-panel results labeled preliminary/protocol-only.
- Keep claims tied to evidence.

## Create
`SECOND_REAL_BENCHMARK_DECISION.md`, `configs/audits/secondary_benchmark_candidate.yaml`.

## Compare
GSM8K/GSM1k, TruthfulQA, MMLU-Pro, GPQA wide panel. Criteria: per-instance predictions, external issue labels, text restrictions, fit with diagnostics, cost, paper value, risk.

## Default recommendation
MMLU-Redux first; GSM8K/GSM1k second if data available; GPQA wide as restricted-data protocol case. Avoid domain-specific packs for NeurIPS unless external ground truth exists.

No tests unless code changes.
