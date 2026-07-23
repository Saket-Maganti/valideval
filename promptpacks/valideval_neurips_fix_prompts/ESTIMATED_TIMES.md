# Estimated Work Times and Run Times

| # | Prompt | Human/Codex working time | CPU runtime | GPU runtime | Expensive? |
|---:|---|---:|---:|---:|---|
| 01 | Prompt 01 — Freeze Features, Initialize Reproducibility, and Create Audit Trail | 45–90 min | 1–3 min | Not required | No |
| 02 | Prompt 02 — Scope Trim, Claims Ledger, and Evidence Pivot | 1–2 hr | <1 min | Not required | No |
| 03 | Prompt 03 — Generic Wide Response Matrix Importer | 3–6 hr | 1–10 min fixtures; 10–60 min large local files | Not required | No |
| 04 | Prompt 04 — Published Per-Instance Details Importers for Leaderboard / HELM-style Data | 4–8 hr | 10–90 min depending on local data size | Not required | No |
| 05 | Prompt 05 — MMLU-Redux Ground-Truth Ingestion Scaffold | 2–4 hr | 1–5 min fixtures; 5–20 min real files | Not required | No |
| 06 | Prompt 06 — Export Diagnostic Flags and Validate Against External Ground Truth | 4–8 hr | 5–30 min fixtures; 30–120 min large benchmark | Not required | No |
| 07 | Prompt 07 — Cross-Flaw Confusion Matrix for Diagnostic Specificity | 4–8 hr | 5–30 min synthetic small; 30–90 min larger configs | Not required | No |
| 08 | Prompt 08 — Held-Out Synthetic Flaw Generators to Reduce Circularity | 4–10 hr | 10–60 min synthetic | Not required | No |
| 09 | Prompt 09 — Real IRT / 2PL on Wide Response Matrices | 6–14 hr | 30 min–4 hr depending on matrix | Optional; can speed PyTorch/py-irt | No paid APIs |
| 10 | Prompt 10 — MMLU-Redux Main External-Validation Experiment Pipeline | 8–16 hr build; 1–4 hr real run | 30 min–4 hr real run depending rows/models | Not required | No paid APIs |
| 11 | Prompt 11 — GPQA Wide-Panel Reanalysis Protocol | 3–6 hr build; 30 min–3 hr run after data import | 30 min–3 hr if wide predictions available | Not required | No |
| 12 | Prompt 12 — Secondary Benchmark Plan: GSM8K/GSM1k or TruthfulQA | 2–4 hr plan; 4–12 hr if scaffold | 1–60 min local data | Not required | No |
| 13 | Prompt 13 — Statistical Grounding: Multiplicity, Materiality, Nulls, and Uncertainty | 4–8 hr | 10–90 min depending bootstrap | Not required | No |
| 14 | Prompt 14 — Panel Validity Diagnostics and Failure-Mode Guardrails | 3–6 hr | 5–30 min | Not required | No |
| 15 | Prompt 15 — NeurIPS Paper Draft Scaffold: Evidence-First, No Hype | 4–10 hr scaffold; 20–40 hr human revision later | <1 min | Not required | No |
| 16 | Prompt 16 — Related Work Positioning and Citation Map | 3–8 hr | <1 min | Not required | No |
| 17 | Prompt 17 — External Review Packet and v0.2.x Release Hardening | 2–5 hr | 1–10 min | Not required | No |
| 18 | Prompt 18 — Final NeurIPS Readiness Audit Gate | 3–6 hr | 5–30 min | Not required | No |
| 19 | Prompt 19 — NeurIPS Workshop Paper Strategy Before Main Submission | 2–5 hr | <1 min | Not required | No |
| 20 | Prompt 20 — Master Execution Order and Time Budget | 30–60 min | <1 min | Not required | No |

## Notes
- Avoid Codex-driven LLM generation.
- Import published per-instance predictions where possible.
- The highest-value real run is MMLU/MMLU-Redux external validation after data is available.
- The most important build tasks are wide importer, external validation, cross-flaw specificity, panel validity, and paper scaffold.
