# Preregistered Benchmark Set

| Benchmark | Claimed construct | Item format | Construct-critical field | Expected validity threats | Loader status |
| --- | --- | --- | --- | --- | --- |
| MMLU | Academic knowledge and problem solving | MCQ | Prompt and choices | contamination, saturation, coverage gaps | scaffold |
| BBH | Challenging task-specific reasoning | Mixed short answer | Prompt | prompt sensitivity, task heterogeneity | scaffold |
| GSM8K | Grade-school math reasoning | Free response | Problem text and final answer | answer extraction, contamination | scaffold |
| TruthfulQA | Truthfulness under misconception-prone questions | QA/MCQ | Question and references | judge reliability, ambiguity | scaffold |
| HotpotQA/NQ-style QA | Open-domain factual QA | QA with context | Context and question | retrieval leakage, ambiguity | planned |
| CausalAgentBench | Causal agentic reasoning | Scenario/task | Scenario, intervention, outcome | coverage, scoring validity | scaffold |
| Synthetic toy MCQ | Controlled validity artifacts | MCQ | Prompt, context, choices | shortcuts, low discrimination | implemented |
| Candidate robust benchmark | To be preregistered | TBD | TBD | expected lower shortcut risk | planned |

