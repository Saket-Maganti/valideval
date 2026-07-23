# Prompt 08 — Second Benchmark Selection and CPU Execution Path

## Objective

Choose and prepare/run a second benchmark path so the paper is not MMLU-only.

## Candidates

- GPQA Diamond,
- MMLU-Pro,
- TruthfulQA,
- GSM8K,
- BBH,
- ARC/HellaSwag,
- compact lm-eval-harness task.

## Decision criteria

- feasible panel,
- enough model variance,
- clear construct,
- deterministic scoring,
- no expensive API dependency,
- fits ValidEval diagnostics.

## Create selection report

```text
SECOND_BENCHMARK_SELECTION_AND_EXECUTION_PLAN.md
```

Structure:

```markdown
# Second Benchmark Selection and Execution Plan

## 1. Executive Summary
## 2. Candidate Comparison
## 3. Recommended Benchmark
## 4. Why Not Others
## 5. Required Panel
## 6. CPU Path
## 7. Kaggle GPU Path If Needed
## 8. Diagnostics To Run
## 9. Baselines
## 10. Expected Paper Value
## 11. Risks
## 12. Final Decision
```

## CPU/public-artifact path

```bash
python3 -m valideval benchmark-preflight --benchmark <selected> --dry-run

python3 -m valideval import-wide-predictions   --benchmark <selected>   --input <path>   --output cache/<selected>/wide/predictions.jsonl

python3 -m valideval matrix-from-wide-predictions   --input cache/<selected>/wide/predictions.jsonl   --output cache/<selected>/wide/matrix.csv

python3 -m valideval panel-validity   --matrix cache/<selected>/wide/matrix.csv   --output results/<selected>/panel_validity   --strict
```

If no CPU/public-artifact path is feasible, use the Kaggle notebook builder.

## Report

```text
SECOND_BENCHMARK_RUN_REPORT.md
```

Final verdict:

```text
SECOND_BENCHMARK_RUN_COMPLETE
SECOND_BENCHMARK_CPU_BLOCKED_USE_KAGGLE
SECOND_BENCHMARK_SELECTION_ONLY
```

## Verification

```bash
ruff check .
python3 -m pytest -q
```
