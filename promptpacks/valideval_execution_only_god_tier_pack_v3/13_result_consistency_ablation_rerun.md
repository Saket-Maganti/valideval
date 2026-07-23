# Prompt 13 — Result Consistency and Ablation Rerun

## Objective

Stress-test core results so reviewers cannot dismiss them as threshold/seed artifacts.

## Analyses

- threshold sensitivity,
- bootstrap seed sensitivity,
- subject subset sensitivity,
- model subset sensitivity,
- random diagnostic baseline,
- leave-one-subject-out,
- leave-one-model-family-out if metadata exists,
- small-panel degradation analysis.

## Outputs

```text
results/consistency_v3/
RESULT_CONSISTENCY_AND_ABLATION_V3_REPORT.md
paper/tables/result_consistency_v3.csv
paper/figures/result_consistency_v3.pdf
```

## Final verdict

```text
CORE_FINDINGS_ROBUST
CORE_FINDINGS_MIXED
CORE_FINDINGS_FRAGILE
CONSISTENCY_RUN_BLOCKED
```
