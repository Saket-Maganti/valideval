# Prompt 18 — Final NeurIPS Readiness Audit Gate

## Estimated working time / runtime

| Mode | Estimate |
|---|---:|
| Human/Codex working time | 3–6 hr |
| CPU runtime | 5–30 min |
| GPU runtime | Not required |
| Expensive generation? | No |
| Run now or later? | After evidence experiments |

## Purpose

Final reviewer-style go/no-go before submission.

---

Run final NeurIPS readiness gate after evidence exists.

## Global hard rules
- Do not add feature sprawl.
- Do not run expensive Ollama/LLM generation unless explicitly requested.
- Do not use paid or closed APIs.
- Do not expose raw GPQA text.
- Do not make real benchmark claims from toy/fixture/chance-level panels.
- Keep GPQA local-panel results labeled preliminary/protocol-only.
- Keep claims tied to evidence.

## Create/update
`NEURIPS_READINESS_AUDIT.md`, `NEURIPS_SUBMISSION_GO_NO_GO.md`.

## Check required evidence
Wide matrix + panel validity; cross-flaw confusion; held-out validation; MMLU-Redux validation; real IRT/proxy limitations; GPQA caveat; claims ledger; paper draft; related work; tests/lint; reviewer-risk.

## Scorecard
novelty, diagnostic validation, external validation, benchmark evidence, stats, reproducibility, engineering, paper readiness, reviewer defensibility, NeurIPS fit.

## Decision values
`SUBMIT_NEURIPS_READY`, `BORDERLINE_NEEDS_REVISION`, `WORKSHOP_FIRST`, `TMLR_FIRST`, `NOT_READY`.

Run full tests and ruff.
