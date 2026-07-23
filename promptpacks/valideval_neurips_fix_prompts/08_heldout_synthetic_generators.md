# Prompt 08 — Held-Out Synthetic Flaw Generators to Reduce Circularity

## Estimated working time / runtime

| Mode | Estimate |
|---|---:|
| Human/Codex working time | 4–10 hr |
| CPU runtime | 10–60 min synthetic |
| GPU runtime | Not required |
| Expensive generation? | No |
| Run now or later? | After Prompt 07 |

## Purpose

Adds independent generator families so detectors are not validated only on mirror-image flaws.

---

Add held-out synthetic flaw generators.

## Global hard rules
- Do not add feature sprawl.
- Do not run expensive Ollama/LLM generation unless explicitly requested.
- Do not use paid or closed APIs.
- Do not expose raw GPQA text.
- Do not make real benchmark claims from toy/fixture/chance-level panels.
- Keep GPQA local-panel results labeled preliminary/protocol-only.
- Keep claims tied to evidence.

## Module
`src/valideval/validation/heldout_generators.py`.

## Required generator families
paraphrased shortcut artifact, distractor plausibility skew, item cluster redundancy, ability-dependent inversion, coverage blindspot, extraction ambiguity.

## CLI
`validate-diagnostics-heldout --config configs/validation/heldout_default.yaml --output validation_reports/heldout_generators/`

## Metrics
Original-generator AUC, held-out-generator AUC, transfer drop, FPR, sensitivity, specificity, paper-eligibility.

## Tests
`tests/test_heldout_generators.py` with tiny fixtures.
