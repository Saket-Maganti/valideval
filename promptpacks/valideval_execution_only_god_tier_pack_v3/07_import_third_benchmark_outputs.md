# Prompt 07 — Import Third Benchmark Outputs

## Objective

Import BBH/TruthfulQA outputs if present.

## Search

```bash
find kaggle_outputs data/external -maxdepth 5 -type f \( -name "*bbh*.zip" -o -name "*truthful*.zip" -o -name "*third*.zip" \) | sort
```

## Outputs

```text
cache/<third_benchmark>/wide/predictions.jsonl
cache/<third_benchmark>/wide/matrix.csv
results/<third_benchmark>/panel_validity/
THIRD_BENCHMARK_IMPORT_AND_VALIDATION_REPORT.md
```

## Final verdict

```text
THIRD_BENCHMARK_PANEL_VALIDITY_PASS
THIRD_BENCHMARK_PANEL_VALIDITY_PARTIAL
THIRD_BENCHMARK_IMPORT_BLOCKED_NO_OUTPUTS
THIRD_BENCHMARK_SCHEMA_FAILED
```
