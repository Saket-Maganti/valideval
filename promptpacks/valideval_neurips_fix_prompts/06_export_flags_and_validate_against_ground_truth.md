# Prompt 06 — Export Diagnostic Flags and Validate Against External Ground Truth

## Estimated working time / runtime

| Mode | Estimate |
|---|---:|
| Human/Codex working time | 4–8 hr |
| CPU runtime | 5–30 min fixtures; 30–120 min large benchmark |
| GPU runtime | Not required |
| Expensive generation? | No |
| Run now or later? | Build now; real execution later |

## Purpose

Turns diagnostics into externally testable predictions with precision/recall/enrichment.

---

Build flag export and external validation.

## Global hard rules
- Do not add feature sprawl.
- Do not run expensive Ollama/LLM generation unless explicitly requested.
- Do not use paid or closed APIs.
- Do not expose raw GPQA text.
- Do not make real benchmark claims from toy/fixture/chance-level panels.
- Keep GPQA local-panel results labeled preliminary/protocol-only.
- Keep claims tied to evidence.

## Create/update
`src/valideval/validation/external_flag_validation.py`, `src/valideval/report/external_validation_report.py`.

## Flag schema
benchmark, subset, item_id, diagnostic, score, severity, direction, evidence summary. No raw item text.

## CLI
1. `export-flags --benchmark mmlu --results results/mmlu/audit/ --output results/mmlu/flags.jsonl`
2. `validate-flags-against-ground-truth --benchmark mmlu --flags results/mmlu/flags.jsonl --ground-truth data/ground_truth/mmlu_redux_issues.normalized.jsonl --output results/mmlu/external_validation/`

## Metrics
precision@k, recall@k, AP, AUROC, AUPRC, enrichment over random, bootstrap CI, issue-type and severity breakdown.

## Outputs/tests
summary.md, metrics.json, joined JSONL. Add fixture tests.
