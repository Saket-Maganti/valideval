# Prompt 05 — Third Benchmark Pack: TruthfulQA or BBH

## Objective

Prepare a third benchmark path for stronger generality. Choose either TruthfulQA or BBH after feasibility review.

## Candidate criteria

TruthfulQA:
- high relevance to benchmark validity,
- but scoring may require judge/MC mode.

BBH:
- deterministic task structure,
- reasoning-focused,
- lm-eval support,
- more compute.

Choose the one with better deterministic scoring and execution feasibility.

## Create

```text
THIRD_BENCHMARK_SELECTION_REPORT.md
kaggle_third_benchmark/
kaggle_third_benchmark/valideval_third_benchmark_runner.ipynb
kaggle_third_benchmark/README.md
```

## Selection report sections

```markdown
# Third Benchmark Selection Report

## 1. Executive Summary
## 2. Candidate Comparison
## 3. Selected Benchmark
## 4. Construct Difference From MMLU/GSM8K
## 5. Scoring Reliability
## 6. Compute Requirements
## 7. Model Panel
## 8. Risks
## 9. Execution Path
## 10. Final Verdict
```

Final verdict:

```text
THIRD_BENCHMARK_PACK_READY
THIRD_BENCHMARK_DEFERRED
THIRD_BENCHMARK_BLOCKED
```
