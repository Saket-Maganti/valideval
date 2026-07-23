# Prompt 17 — External Review Packet and v0.2.x Release Hardening

## Estimated working time / runtime

| Mode | Estimate |
|---|---:|
| Human/Codex working time | 2–5 hr |
| CPU runtime | 1–10 min |
| GPU runtime | Not required |
| Expensive generation? | No |
| Run now or later? | After initial evidence scaffolds |

## Purpose

Creates a clean review packet instead of dumping phase reports.

---

Create external-review packet. Do not include restricted/private raw data.

## Global hard rules
- Do not add feature sprawl.
- Do not run expensive Ollama/LLM generation unless explicitly requested.
- Do not use paid or closed APIs.
- Do not expose raw GPQA text.
- Do not make real benchmark claims from toy/fixture/chance-level panels.
- Keep GPQA local-panel results labeled preliminary/protocol-only.
- Keep claims tied to evidence.

## Create folder
`external_review_packets/neurips_evidence_pivot/` with REVIEWER_README, project summary, claims ledger, evidence pivot, validation status, GPQA limitation note, MMLU plan, paper outline, file manifest.

## Reviewer README
Explain what ValidEval is, current evidence, missing evidence, what to evaluate, what is out of scope, known risks.

## Zip
Create `external_review_packets/valideval_neurips_evidence_pivot_packet.zip`. Exclude raw GPQA, local_outputs, cache if too large, private data.
