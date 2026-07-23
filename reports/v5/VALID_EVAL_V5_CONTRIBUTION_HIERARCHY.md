# ValidEval V5 Contribution Hierarchy

Date: 2026-07-15

## Thesis

Benchmark-validity diagnostics are measurement instruments. Their sensitivity, specificity,
uncertainty, decision materiality, external validity, and transfer must be established before they
can license claims about benchmark quality or model rankings.

This is narrower and more defensible than “a toolkit with many diagnostics.” It also prevents the
project from claiming novelty for applying IRT to LLM benchmarks: Land and Bikel's 2026
[IRT benchmark audit](https://arxiv.org/abs/2605.30504) is a direct neighbor, and
[tinyBenchmarks](https://arxiv.org/abs/2402.14992) already uses psychometric ideas for efficient
evaluation.

## Contribution ledger

| Contribution | Class | Novelty claim | Evidence now | Evidence required | Nearest competitors | Reviewer objection | Response and ceiling |
|---|---|---|---|---|---|---|---|
| Diagnostics-as-instruments with explicit claim gates | **PRIMARY** | Integrates diagnostic validation, evidence states, materiality, identity, and transfer into one falsifiable audit protocol | Deterministically reproduced public HELM-derived MMLU case study; machine-readable claim ledger; build-time fail-closed gates | Controlled Study C, confirmatory decoupled synthetic evidence, and human/external validation | [BetterBench](https://proceedings.neurips.cc/paper_files/paper/2024/hash/26889e8359e7ef8a7f5d77457364ca55-Abstract-Datasets_and_Benchmarks_Track.html), [Land and Bikel 2026](https://arxiv.org/abs/2605.30504), [BenchBench](https://arxiv.org/abs/2407.13696) | “This is careful engineering, not a scientific contribution.” | Show that plausible diagnostics fail or change decisions under predeclared validation tests; claim ceiling remains protocol-scoped. |
| Null-calibrated ranking materiality | **SECONDARY** | Separates descriptive rank variability from variability exceeding defensible nulls and practical decision thresholds | V5 implementation and historical MMLU matrix | Preregistered robustness analyses, family metadata, and confirmation on controlled Study C | [Benchmarking LLMs via Uncertainty Quantification](https://proceedings.neurips.cc/paper_files/paper/2024/hash/1bdcb065d40203a00bd39831153338bb-Abstract-Datasets_and_Benchmarks_Track.html) | “Raw rank range is mechanically large with 39 models and 57 subjects.” | Lead with null exceedance, confidence sets, top-k probabilities, and effect sizes; retire the legacy “severe >=10” label. |
| Exact-identity controlled cross-benchmark design | **SECONDARY** | Makes exact checkpoint/configuration identity part of the cross-benchmark estimand | Registry, contracts, power/runtime planners, overlap gate | Same exact revisions on MMLU, GSM8K, and BBH with adequate family diversity | [BenchBench](https://arxiv.org/abs/2407.13696), HELM | “Family names and scores are not comparable interventions.” | Keep Study H and Study C separate; family-level analyses remain exploratory. |
| Leakage and circularity threat model | **SECONDARY** | Treats gold isolation, diagnostic-label isolation, post-selection, synthetic circularity, and identity leakage as one executable gate | Static/adversarial guard suite and preregistration config | Real execution manifests and blinded review audit trail | [Oren et al. 2024](https://proceedings.iclr.cc/paper_files/paper/2024/hash/46e624c244cff669223d488defd4e835-Abstract-Conference.html), option-order work | “Pipeline leakage is being conflated with model pretraining contamination.” | Keep four threat classes separate; absence of pretraining contamination is never claimed. |
| Reusable offline-safe implementation | **ENGINEERING** | Deterministic cached-response analyses, secure imports, manifests, and fixture-tested notebooks | V5 source, tests, and release allowlists | Remote S1 smoke and artifact review | HELM, lm-eval-harness, Inspect AI | “A tool is not a paper.” | Support the scientific protocol; never lead with feature count. |
| MMLU-Redux item validation | **RETIRED** | None until exact identity exists | Structural subject/index linkage only; weak historical metrics | Stable IDs or content hashes plus confirmed-only reanalysis | MMLU-Redux | “The labels are not linked to the scored items.” | Treat as an unsuccessful exploratory linkage attempt. |
| Human confirmation of benchmark issues | **BLOCKED** | Blinded enrichment/precision study, not general recall | Protocol and import path only | Real blinded labels, controls, agreement, adjudication | Human benchmark audits | “A high-score queue cannot estimate recall.” | Claim only the estimand supported by the sampling design. |
| Benchmark repair improves decisions | **FUTURE** | A repair policy improves preregistered decision utility without post-selection | No V5 repair evidence | Confirmed issues, held-out repair rule, before/after uncertainty and utility | Benchmark repair literature | “Repair is tuned on the same panel.” | Use held-out or nested validation; otherwise keep blocked. |

## Contribution priority

The paper should lead with the primary contribution, then use the historical MMLU study to show why
the distinction matters. The software, dashboard, number of diagnostics, and notebook suite are
supporting artifacts. A future paper becomes competitive only if the controlled common-panel and at
least one independent validation pillar produce a clear, uncertainty-aware result.

Status: `PRIMARY CONTRIBUTION DEFINED; EMPIRICAL CEILING BLOCKED`.
