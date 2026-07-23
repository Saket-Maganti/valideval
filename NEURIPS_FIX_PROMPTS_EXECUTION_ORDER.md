# NeurIPS Fix Prompts Execution Order

| Phase | Prompt | Purpose | Run now? | CPU time | GPU time | Blockers |
|---|---|---|---|---:|---:|---|
| Immediate | 01 | Freeze and audit trail | built | 1-3 min tests | none | canonical git history unknown |
| Immediate | 02 | Claims ledger and evidence pivot | built | <1 min | none | none |
| Immediate | 20 | Execution order and budget | built | <1 min | none | none |
| Evidence infra | 03 | Wide prediction importer | built | 1-10 min fixtures, 10-60 min large files | none | local published predictions |
| Evidence infra | 04 | Leaderboard/HELM importers | built | 10-90 min depending local data | none | local detail files |
| Evidence infra | 05 | MMLU-Redux labels | built | 1-5 min fixtures, 5-20 min real files | none | local label file |
| Evidence infra | 06 | Flag validation | built | 5-30 min fixtures, 30-120 min large benchmark | none | diagnostic flags and labels |
| Synthetic | 07 | Cross-flaw specificity | built | 5-30 min small, 30-90 min larger | none | execute later |
| Synthetic | 08 | Held-out generators | built | 10-60 min | none | execute after cross-flaw |
| Psychometrics | 09 | Wide IRT | built | 30 min-4 hr real matrix | optional | panel validity |
| Main experiment | 10 | MMLU-Redux pipeline | built | 30 min-4 hr real run | none | predictions, matrix, labels |
| GPQA | 11 | GPQA wide protocol | built | 30 min-3 hr after import | none | wide GPQA files |
| Secondary | 12 | Second benchmark plan | built | 1-60 min local data | none | defer until MMLU |
| Stats | 13 | Stats grounding | built | 10-90 min | none | result artifacts |
| Guardrails | 14 | Panel validity | built | 5-30 min | none | matrix file |
| Paper | 15 | Evidence-first paper | scaffolded | <1 min | none | empirical placeholders |
| Related work | 16 | Citation map | scaffolded | <1 min | none | human citation verification |
| Review | 17 | External packet | scaffolded | 1-10 min | none | final evidence |
| Final gate | 18 | Readiness audit | scaffolded | 5-30 min | none | evidence experiments |
| Optional | 19 | Workshop-first strategy | scaffolded | <1 min | none | venue choice |

Do not run real LLM generation through Codex. Prefer local published prediction imports.
