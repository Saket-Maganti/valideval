# Prompt 13 — Statistical Grounding: Multiplicity, Materiality, Nulls, and Uncertainty

## Estimated working time / runtime

| Mode | Estimate |
|---|---:|
| Human/Codex working time | 4–8 hr |
| CPU runtime | 10–90 min depending bootstrap |
| GPU runtime | Not required |
| Expensive generation? | No |
| Run now or later? | Build now; run later |

## Purpose

Hardens stats layer reviewers will attack.

---

Strengthen statistical reporting.

## Global hard rules
- Do not add feature sprawl.
- Do not run expensive Ollama/LLM generation unless explicitly requested.
- Do not use paid or closed APIs.
- Do not expose raw GPQA text.
- Do not make real benchmark claims from toy/fixture/chance-level panels.
- Keep GPQA local-panel results labeled preliminary/protocol-only.
- Keep claims tied to evidence.

## Audit existing stats
Multiplicity, bootstrap CIs, null models, effect size, materiality, power.

## Create/update
`src/valideval/stats/nulls.py`, `effect_sizes.py`, `multiplicity.py`, `bootstrap.py`, `materiality.py`, `docs/statistical_grounding.md`. Reuse existing files where present.

## Standard item diagnostic report
raw score, null, p-value, adjusted p-value, effect size, CI, materiality label, detectability label, synthetic-only threshold caveat.

## CLI
`stats-check --results results/mmlu/audit/ --output results/mmlu/stats_check/` with fixture mode.

## Tests
BH, Holm, Bonferroni, bootstrap deterministic seed, effect size, materiality vs significance separation.
