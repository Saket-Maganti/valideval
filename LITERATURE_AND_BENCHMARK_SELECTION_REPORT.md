# Literature And Benchmark Selection Report

Scan date: 2026-06-03

This report is a planning document for ValidEval. It summarizes current literature and benchmark-selection considerations. It does not make empirical claims about any real benchmark.

## 1. Executive summary

The nearest current work does not make ValidEval irrelevant, but it does narrow the novelty claim.

The closest overlap is now psychometric benchmark auditing with IRT. A May 2026 arXiv paper, [Auditing LLM Benchmarks with Item Response Theory](https://arxiv.org/abs/2605.30504), reports an IRT-based indicator for likely mislabels across several benchmarks. That is close to ValidEval's IRT and item-quality thread. The right novelty claim for ValidEval is therefore not "first psychometric benchmark audit." A more defensible claim is:

> ValidEval is an offline-first, multidiagnostic validity-auditing toolkit that treats benchmark validity as a profile: item discrimination, shortcuts, answer artifacts, scoring/extraction fragility, reliability under perturbation, saturation, contamination/data-forensics signals, and materiality are reported separately rather than collapsed into a single score.

The best first real benchmark audit should be **GPQA Diamond**. It is current, influential, small enough for careful manual review, multiple-choice enough for the validated ValidEval diagnostics, and scientifically interesting because it has a strong construct claim: graduate-level, Google-resistant science reasoning suitable for scalable oversight. It is not as stale as MMLU/GSM8K, and it is not as infrastructure-heavy as SWE-bench or agent benchmarks.

The recommended first empirical step is a **pre-registered GPQA Diamond validity audit** with a deterministic open/local model panel, fixed prompt variants, cached responses, ValidEval's validated diagnostics, and human/expert review of only flagged items. The primary claim should be limited to: "Under this protocol, we find evidence consistent with / not consistent with specific validity threats in GPQA Diamond." Do not claim GPQA is globally valid or invalid.

Implementation status after Phase 14: the repository now contains GPQA Diamond setup artifacts, a local JSONL adapter, prompt templates, a synthetic tiny fixture, a dry-run command path, and a pre-registration draft. These are audit-readiness artifacts only. No real GPQA Diamond findings exist until a verified local GPQA export and cached open/local model outputs are audited.

## 2. Closest related work

### Evaluation runners and leaderboards

- [HELM](https://github.com/stanford-crfm/helm) and [HELM Capabilities](https://crfm.stanford.edu/helm/capabilities/v1.1.0/) provide transparent, reproducible, multi-scenario model evaluation. HELM is broad and multi-metric, but its center of gravity is model evaluation rather than auditing whether a benchmark's score supports a claimed construct.
- [lm-evaluation-harness](https://arxiv.org/abs/2405.14782) is the standard lightweight runner for many language-model benchmarks. It is infrastructure for reproducible scoring, not a validity-auditing layer.
- [OpenCompass](https://github.com/open-compass/opencompass) and the 2026 [OpenCompass paper](https://arxiv.org/abs/2605.19276) focus on large-scale, high-concurrency benchmark execution across many datasets and models.
- [Inspect AI](https://inspect.aisi.org.uk/) from the UK AI Security Institute is an open-source framework for frontier/safety evaluations. It is closer in spirit to robust evaluation workflows, but not specifically a benchmark-validity psychometrics toolkit.
- [RAGAS](https://arxiv.org/abs/2309.15217) and [RAGAS docs](https://docs.ragas.io/en/v0.3.4/) evaluate RAG pipelines using dimensions such as faithfulness and answer relevance. [DeepEval](https://deepeval.com/docs/introduction) is an application-testing framework for LLM apps. Both are useful comparators for application evaluation, but neither is primarily about benchmark construct validity.

### Benchmark validity and benchmark auditing

- [BetterBench](https://proceedings.neurips.cc/paper_files/paper/2024/file/26889e8359e7ef8a7f5d77457364ca55-Paper-Datasets_and_Benchmarks_Track.pdf) assesses AI benchmarks and discusses benchmark quality/validity concerns. It is one of the closest "benchmark about benchmarks" efforts.
- [Inadequacies of Large Language Model Benchmarks](https://arxiv.org/abs/2402.09880) analyzes benchmark functionality and integrity across LLM benchmarks.
- [Do These LLM Benchmarks Agree? Fixing Benchmark Evaluation with BenchBench](https://arxiv.org/abs/2407.13696) studies agreement and robustness of benchmark evaluations.
- [Auditing LLM Benchmarks with Item Response Theory](https://arxiv.org/abs/2605.30504) is the closest direct neighbor for IRT-based benchmark auditing. It reports likely mislabeled or ambiguous items using responses from many models. ValidEval should cite this as close related work and position itself as broader, not prior.

### Contamination and freshness

- [Proving Test Set Contamination in Black-Box Language Models](https://proceedings.iclr.cc/paper_files/paper/2024/hash/46e624c244cff669223d488defd4e835-Abstract-Conference.html) proposes a black-box contamination test with false-positive guarantees based on canonical ordering versus shuffled examples.
- [Detecting Pretraining Data from Large Language Models](https://proceedings.iclr.cc/paper_files/paper/2024/hash/e32ad85fa27be4a9868d55703f01323e-Abstract-Conference.html) introduces WIKIMIA for pretraining-data detection.
- [LiveBench](https://arxiv.org/abs/2406.19314) addresses contamination by using frequently updated, objective tasks. It is a benchmark-design response rather than an audit of an existing benchmark.
- [MMLU-CF](https://arxiv.org/abs/2412.15194) is a contamination-free MMLU-style benchmark, showing that MMLU-style measurement is still valued but the original benchmark's contamination risk is widely recognized.

### Shortcuts, artifacts, and prompt sensitivity

- [Large Language Models Sensitivity to the Order of Options in Multiple-Choice Questions](https://aclanthology.org/2024.findings-naacl.130/) reports large performance swings under answer-option reordering.
- [Large Language Models Are Not Robust Multiple Choice Selectors](https://arxiv.org/abs/2309.03882) studies token/option bias in MCQ answer selection.
- [PromptBench](https://www.jmlr.org/papers/v25/24-0023.html), [POSIX](https://aclanthology.org/2024.findings-emnlp.852/), [ProSA](https://arxiv.org/abs/2410.12405), and [On the Worst Prompt Performance of Large Language Models](https://arxiv.org/abs/2406.10248) show that prompt sensitivity is an active evaluation problem.
- [MMLU-Pro](https://arxiv.org/abs/2406.01574) explicitly tests prompt styles and reports reduced prompt sensitivity relative to MMLU.

### IRT, tiny benchmarks, and item selection

- [tinyBenchmarks](https://arxiv.org/abs/2402.14992) uses IRT-style methods to select small subsets that estimate full benchmark performance, including tinyMMLU. This is about efficient performance estimation more than validity-threat auditing.
- [Psychometrically derived 60-question benchmarks](https://www.sciencedirect.com/science/article/pii/S016028962500025X) is further evidence that short-form, psychometric benchmark design is active.
- The 2026 [IRT benchmark-auditing paper](https://arxiv.org/abs/2605.30504) is the most important close comparison for ValidEval's IRT item-quality claims.

### Benchmark saturation

- The [Stanford AI Index 2025 technical performance chapter](https://hai.stanford.edu/ai-index/2025-ai-index-report/technical-performance) says traditional benchmarks such as MMLU, GSM8K, and HumanEval have saturated, pushing the field toward harder benchmarks such as GPQA and FrontierMath.
- [MMLU-Pro](https://arxiv.org/abs/2406.01574) was motivated partly by MMLU plateauing.
- [BIG-Bench Extra Hard](https://arxiv.org/abs/2502.19187) was introduced because BIG-Bench and BBH were becoming saturated.

### LLM judge reliability

- [Judging the Judges: Position Bias in LLM-as-a-Judge](https://arxiv.org/abs/2406.07791), [Self-Preference Bias in LLM-as-a-Judge](https://arxiv.org/abs/2410.21819), and [Style over Substance](https://huggingface.co/papers/2409.15268) show that LLM judges can be biased or unstable.
- [JudgeBench](https://arxiv.org/abs/2410.12784) benchmarks LLM-based judges on objective pairwise judgments.
- [Judge Reliability Harness](https://arxiv.org/abs/2603.05399) is a close tool neighbor for judge-specific reliability stress tests. It is not a full benchmark-validity toolkit, but it overlaps with ValidEval's scoring/extraction and judge-reliability ambitions.

## 3. What is already known

- Benchmark scores are protocol-dependent. Prompt format, answer extraction, option order, scoring method, and few-shot setup can all change measured performance.
- Contamination is not a hypothetical problem. There are black-box and white-box methods for detecting possible pretraining/test-set overlap, but none fully solves closed-model contamination.
- Classic headline benchmarks are losing frontier-model discrimination. MMLU, GSM8K, HumanEval, and parts of BBH are no longer strong first-audit targets for frontier relevance.
- MCQ benchmarks can reward superficial selection biases. Answer-label priors, option-order effects, and choices-only shortcuts are especially relevant to ValidEval.
- LLM-as-judge evaluation is itself an object of validation. Judge consistency, position bias, verbosity bias, self-preference, and prompt sensitivity matter.
- Psychometric methods are becoming more common in LLM evaluation. ValidEval should not claim psychometrics as a unique category; it should claim a specific integration and reporting philosophy.

## 4. What ValidEval can still uniquely contribute

ValidEval can contribute a useful middle layer between raw evaluation harnesses and human benchmark-review papers:

- A **validity profile**, not a leaderboard score.
- Offline-safe diagnostics that can run on cached responses.
- Synthetic validation reports for diagnostic/flaw pairings before real benchmark claims.
- A common report format for shortcuts, answer artifacts, extraction fragility, reliability, IRT item quality, saturation, and materiality.
- Pre-registered audit protocols that separate detector sensitivity from real-world validity conclusions.
- Practical triage: identify which benchmark items deserve scarce expert review.

Novelty should be stated conservatively:

> ValidEval appears distinct from common evaluation runners and app-eval frameworks because it audits benchmark validity threats rather than only scoring models. However, IRT-based benchmark auditing and judge-reliability harnesses are active neighboring work, so ValidEval's strongest angle is the breadth and caution of its multidiagnostic validity-audit workflow.

## 5. Benchmark candidate comparison table

Scale: 1 = weak, 5 = strong. "Ease" includes feasibility with local/open models, deterministic scoring, and fit to current ValidEval diagnostics.

| Benchmark | Current relevance | Ease | Validity-threat potential | Existing criticism saturation | Expected paper value | Recommendation |
| --------- | ----------------: | ---: | ------------------------: | ----------------------------: | -------------------: | -------------- |
| GSM8K | 2 | 5 | 2 | 5 | 2 | Do not choose first. Useful software smoke test, but too saturated as a headline. |
| MMLU subset | 3 | 5 | 5 | 5 | 3 | Strong artifact/error audit target, but stale and heavily criticized. Better as a comparison baseline. |
| MMLU-Pro | 4 | 4 | 4 | 3 | 4 | Good second audit. More current than MMLU, MCQ-friendly, but designed to fix known MMLU issues. |
| BBH | 3 | 4 | 3 | 4 | 2 | Useful reasoning baseline, but approaching saturation and less aligned with ValidEval's strongest MCQ artifact diagnostics. |
| GPQA Diamond | 5 | 4 | 4 | 2 | 5 | **Choose first.** High relevance, clear construct, manageable size, MCQ-friendly, and not as stale as MMLU/GSM8K. |
| TruthfulQA | 3 | 3 | 5 | 4 | 3 | Good for judge/scoring reliability, but older and judge-dependent. Better after a judge-validation protocol. |
| HotpotQA / NQ-style QA | 3 | 3 | 4 | 4 | 3 | Good RAG/retrieval audit, but needs more retrieval/scoring machinery than first audit should require. |
| RAG faithfulness benchmark | 5 | 2 | 5 | 3 | 4 | High application relevance, but ValidEval needs more RAG-specific validated diagnostics first. |
| SWE-bench Lite / coding benchmark | 5 | 1 | 5 | 5 | 4 | Scientifically hot, but expensive and infrastructure-heavy. Existing criticism is already intense. |
| Agent/tool-use benchmark | 5 | 1 | 5 | 3 | 4 | High future value, but too much harness complexity for first real audit. |
| CausalAgentBench | 3 | 2 | 4 | 1 | 3 | I did not find a clearly established benchmark under this exact name. Treat as exploratory or clarify target. |
| Safety/judge benchmark | 5 | 2 | 5 | 3 | 4 | Important, but should follow a judge-reliability validation step. |

## 6. Recommended first benchmark

**First audit target: GPQA Diamond.**

Rationale:

- It is still part of the current frontier-evaluation conversation.
- It has a crisp construct claim: graduate-level, expert-written science questions that are difficult for non-experts even with web access.
- It is small enough for careful item-level review after automated triage.
- It is multiple-choice, so ValidEval's validated MCQ diagnostics apply.
- It can test item discrimination, negative discrimination, prompt/extraction reliability, answer-label artifacts, distractor behavior, and saturation without needing web browsing or agent execution.
- It is less stale than MMLU/GSM8K and less logistically heavy than SWE-bench or RAG benchmarks.

Do not frame this as "auditing all scientific reasoning benchmarks." Frame it as:

> A first real benchmark validity audit of GPQA Diamond under a cached open-model panel, focused on whether the observed response patterns and item features support the intended use of GPQA Diamond as a hard science-reasoning benchmark.

## 7. Recommended 3-5 benchmark portfolio after the first audit

1. **GPQA Diamond**: first audit; hard science MCQ; validates MCQ/IRT/reliability pipeline.
2. **MMLU-Pro subset**: broad multitask MCQ; compare against a benchmark designed to improve on MMLU.
3. **TruthfulQA or SimpleQA-style factuality benchmark**: scoring/judge reliability, abstention, truthfulness construct.
4. **FaithEval / CRAG / RAG faithfulness benchmark**: context grounding, retrieval sufficiency, and faithfulness.
5. **SWE-bench Lite/Verified or a newer live coding benchmark**: only after adding coding-agent harness support and carefully handling contamination/test-quality caveats.

## 8. First real audit protocol

### Benchmark

- GPQA Diamond if accessible from a stable source.
- Use only the item text, choices, answer key, and published metadata needed for deterministic MCQ scoring.
- Do not use web search during model answering.

### Model panel

- Use a deterministic open/local panel where possible.
- Include 8-12 models spanning ability, size, and family.
- Prefer currently available open models at audit time from families such as Qwen, Llama, Mistral, Gemma, Phi, and DeepSeek-Distill.
- Include at least one weaker baseline and one random/label-prior baseline for artifact checks.
- Paid APIs are optional replication only, not required dependencies.

### Prompting

- Primary prompt: answer-only MCQ with all choices.
- Perturbation prompts:
  - choice order shuffled
  - answer labels remapped
  - terse instruction
  - verbose instruction
  - direct-answer-only
  - choices-only ablation where scientifically appropriate

### Caching

- Cache every raw output, normalized prediction, score, prompt variant, model id, seed, and extraction warning.
- Freeze all prompts and extraction rules before running the main panel.

### Human review

- No full manual review required at first.
- Human/expert review only:
  - top flagged negative-discrimination items
  - top extraction/scoring ambiguous items
  - top shortcut/artifact-suspicious items
  - a small matched random control sample

## 9. Required model panel

Minimum viable panel:

- 10 model systems total.
- At least 6 real open/local LLMs.
- At least 2 weak/small models.
- At least 1 deterministic random baseline.
- At least 1 label-prior or choices-only baseline.

Recommended panel structure:

| Role | Purpose |
|---|---|
| Strong open reasoning model | Upper anchor for item discrimination |
| Medium general instruct model | Middle ability band |
| Small instruct model | Lower ability band |
| Math/science-tuned model | Domain specialization check |
| Non-reasoning/general chat model | Construct contrast |
| Random baseline | Null artifact check |
| Label-prior baseline | Answer-distribution artifact check |
| Choices-only heuristic baseline | Shortcut availability check |

Do not estimate latent ability as ground truth. Treat model ordering as an observed panel-specific proxy.

## 10. Diagnostics to run

Primary, because they have synthetic validation support:

- `answer_distribution`
- `distractor_quality`
- `irt`
- `reliability`
- `extraction_robustness`
- `saturation`
- `shortcut`

Exploratory only unless separately validated for this audit:

- `contamination`
- `data_forensics`
- `coverage`
- `calibration`, unless real confidence/logprob values are available
- any LLM-as-judge scoring

Primary item-level outputs:

- corrected/anchor-oriented discrimination
- negative-discrimination flags
- near-zero discrimination flags
- prompt stability / item reliability
- extraction ambiguity rate
- answer-label distribution and option-order sensitivity
- top-model saturation and floor effects
- shortcut/ablation retention

## 11. Pre-registration draft

### Title

Pre-registered validity audit of GPQA Diamond under a cached open-model panel.

### Research question

Under a fixed, offline evaluation protocol, does GPQA Diamond show evidence consistent with validity threats that could affect its interpretation as a graduate-level science-reasoning benchmark?

### Non-goals

- Do not estimate the true capability of any model.
- Do not claim GPQA Diamond is globally valid or invalid.
- Do not compare commercial frontier systems unless cached outputs are available and the protocol is fixed.
- Do not tune prompts after seeing results.

### Primary hypotheses

- H1: Most GPQA Diamond items will preserve positive item discrimination under the model panel.
- H2: A minority of items may show low or unstable discrimination because the benchmark is very hard for smaller/local models.
- H3: Some items may show extraction or prompt-format fragility, but severe answer-label artifacts should be rare if GPQA's construction is sound.
- H4: If high-ability models systematically fail items that low-ability or heuristic baselines pass, those items require expert review before they are interpreted as negative-discrimination evidence.

### Primary outcomes

- Fraction of items flagged as negative-discrimination, near-zero discrimination, unstable, or insufficient-panel.
- Fraction of items with material prompt instability.
- Fraction of items with extraction/scoring ambiguity.
- Evidence of answer-label, answer-length, or choices-only shortcut availability.
- Saturation/floor profile across the panel.

### Materiality rules

Report a potential material validity threat only if:

- the diagnostic flag survives multiplicity/error-control reporting where available,
- the effect is not confined to a single model family,
- it appears under at least two prompt variants or under the primary prompt plus a diagnostic ablation,
- and human/expert review agrees the flagged item has plausible construct/scoring concern.

### Analysis plan

1. Run the frozen prompt set across the frozen model panel.
2. Build cached response matrices.
3. Run primary diagnostics.
4. Generate a validity profile report.
5. Select flagged items for blind review.
6. Compare flagged items to matched random controls.
7. Report findings with cautious language.

### Stopping rule

If fewer than 6 non-baseline models produce parseable responses for at least 90% of items, do not publish item-discrimination conclusions. Report the run as a protocol/debugging audit only.

## 12. What result would be publishable

A publishable result would not need to "debunk" GPQA. It would be publishable if it shows one of:

- Evidence consistent with a small but material subset of items having scoring ambiguity, negative discrimination, or prompt fragility, confirmed by targeted expert review.
- A clean validity profile showing GPQA Diamond is relatively robust under ValidEval's diagnostics, paired with a reusable pre-registered audit protocol.
- A comparison showing that ValidEval flags a different class of issues than raw leaderboard scores, IRT-only audits, or standard evaluation harnesses.
- A material model-ranking sensitivity analysis where removing or downweighting flagged items changes conclusions under the defined panel.

## 13. What result would be boring but useful

- No major validity threats found.
- Most items are simply too hard for the open/local model panel, making discrimination estimates unstable.
- Extraction is clean, answer-label artifacts are minimal, and prompt perturbations have small effects.

This would still be useful because it would validate the end-to-end real-audit workflow and identify the panel strength needed for future audits.

## 14. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Open/local panel is too weak for GPQA | Include enough ability spread; treat floor effects as a result, not a failure. |
| Domain expertise is needed to judge flagged science items | Use targeted expert review only for flagged items plus controls. |
| GPQA is public and may be contaminated | Report contamination checks as exploratory; do not claim proof of contamination. |
| IRT proxy may be unstable with small panels | Require minimum panel size and report insufficient-panel labels. |
| Prompt choices dominate results | Freeze prompt variants and report prompt sensitivity rather than tuning it away. |
| ValidEval overclaims from diagnostics | Use "evidence consistent with" and tie claims to protocol scope. |
| Benchmark access/licensing issues | Use only permitted dataset artifacts and record source/snapshot. |

## 15. Final recommendation

Run **GPQA Diamond** first.

MMLU is too stale as a headline, GSM8K is too saturated, SWE-bench is too infrastructure-heavy and already under intense scrutiny, and RAG/agent/safety benchmarks need additional validated diagnostics before they are good first targets.

GPQA Diamond gives ValidEval the strongest first scientific test: a current, consequential, hard, MCQ benchmark with a clear construct claim and enough item-level structure for validated diagnostics to matter. The audit should be pre-registered, offline-safe, cached, and careful: the deliverable is a validity profile, not a verdict. Phase 14 prepared that protocol and a fixture-only dry run; it did not run the real benchmark audit.
