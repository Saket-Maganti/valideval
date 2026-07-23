# Prompt 09 — Psychometric Upgrade: Rasch Approximation and Scalable IRT

## Objective

Improve psychometric depth without overclaiming full 2PL if infeasible.

## Current blocker

Full Rasch/1PL local optimizer was infeasible due to large parameter count. Full 2PL is not available.

## Tasks

Implement a scalable approximate psychometric path:

1. marginal maximum-likelihood approximation if feasible,
2. regularized Rasch with alternating updates,
3. bootstrap proxy IRT uncertainty,
4. item discrimination via point-biserial / logistic slope proxy,
5. reliability metrics,
6. subject-level psychometric summaries,
7. sanity comparisons to existing proxy IRT.

## Commands

```bash
python3 -m valideval scalable-irt   --matrix cache/mmlu/wide/matrix.csv   --output results/mmlu/scalable_irt   --method alternating_rasch   --max-iter 100   --execute
```

## Required honesty

If this is still approximate, call it approximate/scalable/proxy. Do not call it full 2PL.

## Report

```text
SCALABLE_IRT_UPGRADE_REPORT.md
```

Final verdict:

```text
SCALABLE_IRT_APPROX_COMPLETE
SCALABLE_IRT_BLOCKED
SCALABLE_IRT_NEEDS_REVIEW
```
