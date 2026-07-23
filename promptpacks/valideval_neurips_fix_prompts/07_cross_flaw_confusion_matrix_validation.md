# Prompt 07 — Cross-Flaw Confusion Matrix for Diagnostic Specificity

## Estimated working time / runtime

| Mode | Estimate |
|---|---:|
| Human/Codex working time | 4–8 hr |
| CPU runtime | 5–30 min synthetic small; 30–90 min larger configs |
| GPU runtime | Not required |
| Expensive generation? | No |
| Run now or later? | Now |

## Purpose

Fixes synthetic-validation circularity by testing all detectors on all flaws.

---

Add cross-flaw validation.

## Global hard rules
- Do not add feature sprawl.
- Do not run expensive Ollama/LLM generation unless explicitly requested.
- Do not use paid or closed APIs.
- Do not expose raw GPQA text.
- Do not make real benchmark claims from toy/fixture/chance-level panels.
- Keep GPQA local-panel results labeled preliminary/protocol-only.
- Keep claims tied to evidence.

## Module/CLI
Create `src/valideval/validation/cross_flaw.py` and command `validate-diagnostics-cross-flaw --config configs/validation/synthetic_default.yaml --output validation_reports/cross_flaw_confusion/`.

## Compute
For every detector × flaw: detector score, target/off-target activation, FPR on non-target flaws, specificity, confusion matrix.

## Outputs
`cross_flaw_matrix.csv`, `.json`, `summary.md`, `heatmap_data.csv`.

## Acceptance rule
Diagnostics that strongly activate on unrelated flaws should be downgraded or marked non-paper-eligible.

## Tests
Tiny synthetic fixture in `tests/test_cross_flaw_confusion.py`.
