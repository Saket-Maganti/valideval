# Third Benchmark Selection Report

## 1. Executive Summary
BBH is selected over TruthfulQA for this runbook because deterministic task structure and lm-eval support reduce scoring ambiguity.

## 2. Candidate Comparison
TruthfulQA is relevant to benchmark validity but judge/free-form scoring can introduce extra validation complexity. BBH is reasoning-focused and more deterministic.

## 3. Selected Benchmark
BBH.

## 4. Construct Difference From MMLU/GSM8K
BBH stresses multi-step reasoning and task-specific generalization.

## 5. Scoring Reliability
Deterministic/lm-eval task formats are preferred.

## 6. Compute Requirements
Kaggle T4/P100, small model panel first.

## 7. Model Panel
Reuse the GSM8K small/medium open model panel.

## 8. Risks
Compute time, model availability, shard timeouts, output normalization.

## 9. Execution Path
Use `kaggle_third_benchmark/valideval_third_benchmark_runner.ipynb`.

## 10. Final Verdict
`THIRD_BENCHMARK_PACK_READY`.
