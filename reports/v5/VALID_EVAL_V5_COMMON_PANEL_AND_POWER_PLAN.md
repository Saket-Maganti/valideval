# ValidEval V5 Common Panel and Power Plan

## Verdict

**Panel status: `COMMON_PANEL_PARTIAL`. Power output status: `PLANNED`.** The deterministic
planner is complete, but its simulations are design aids and the required exact S3 members have
not been executed or fully enumerated.

Generated artifact: `results/planning/common_panel_power_v5.csv`.

## Planner freeze

The local-safe planner was run as:

```bash
python3 scripts/build_common_panel_plan_v5.py \
  --panel-sizes 4,8,12,16,24,28,30,32,36,40 \
  --simulations 2000
```

Every row is marked `PLANNED` and `planning_only=true`. The rank-correlation simulation uses a
Gaussian copula, a one-sided positive Spearman test, alpha 0.05, and deterministic seeded Monte
Carlo sampling. It is not an observed benchmark result.

## Tier architecture

| Tier | Intended use | Minimum scope | Evidence ceiling |
|---|---|---|---|
| S0 | Offline code-path fixture | two deterministic mock models | `NON_EVIDENCE_FIXTURE` |
| S1 | Engineering smoke | 2–3 real models, 10–50 items per benchmark | engineering only |
| S2 | Runtime/extraction pilot | 4–8 exact models, 100–500 items or selected subtasks | exploratory |
| S3 | Minimum scientific common panel | power-selected exact, family-diverse panel | scientific only after all quality gates |
| S4 | Maximum-ceiling panel | broader family, scale, architecture, and ability diversity | confirmatory if preregistered and complete |
| S5 | Robustness extension | optional models or prompt/scoring conditions | sensitivity only |

## Rank-correlation design results

For a planning target of true rank correlation 0.5:

| Models | Estimated detection probability | Monte Carlo SE | Approximate 95% correlation interval width | Minimum-family assumption |
|---:|---:|---:|---:|---:|
| 16 | 0.468 | 0.011 | 0.792 | 4 |
| 24 | 0.667 | 0.011 | 0.631 | 6 |
| 28 | 0.749 | 0.010 | 0.580 | 7 |
| 30 | 0.777 | 0.009 | 0.559 | 8 |
| 32 | 0.813 | 0.009 | 0.539 | 8 |
| 36 | 0.851 | 0.008 | 0.506 | 9 |
| 40 | 0.891 | 0.007 | 0.479 | 10 |

Under the explicitly chosen planning rule of at least 0.80 estimated detection probability for
a correlation of 0.5, **S3 targets 32 exact checkpoints across at least eight independent
families**. This is derived from the simulation rather than inherited from the old 30-model
gate. S4 targets 40 checkpoints across at least ten families for greater precision. If the
scientific target is correlation 0.3, even 40 models is weak under this simulation; if it is
0.7, fewer models may detect association but remain inadequate for family diversity and item
parameterization.

## Other estimands

The planner records, rather than silently equating, distinct design requirements:

- model-by-benchmark interaction becomes numerically plannable at 8 models;
- diagnostic transfer is flagged plannable at 12;
- regularized discrimination proxies are flagged plannable at 20;
- a full 2PL is never marked identified;
- item-difficulty standard error at probability 0.5 is reported as a simple binomial planning
  approximation;
- assumed external validation uses 50 positives, 150 negatives, and AUC 0.70;
- assumed human precision uses 200 reviewed items and precision 0.50, with 95% Wilson width
  about 0.137.

The last two calculations depend on assumed label counts and effects, not on panel size. They
cannot unlock a claim while Redux identity and human labels remain blocked.

## Current gap

Five immutable Study C checkpoint revisions are frozen, across three nominal families, and all
five remain T4 execution `PLANNED`. This is sufficient to attempt S1 and then S2. It is not
sufficient for S3: checkpoint coverage is 5/32 and nominal-family coverage is 3/8. The three
Qwen2.5 checkpoints also create family concentration.

Panel adequacy after execution additionally requires complete benchmark coverage, ability
spread, bounded missingness and extraction failures, prompt comparability, and family-
deduplicated sensitivity. Power simulation alone does not certify any of those conditions.

## Runtime planning boundary

`results/planning/runtime_estimates_v5.csv` contains 15 S1-only planning rows: five frozen
checkpoint revisions crossed with three benchmarks at 50 items each. All rows are `PLANNED`
and `UNMEASURED_ASSUMPTIONS`. The generic token, throughput, dual-GPU utilization, and download
proxies are frozen in `results/planning/runtime_estimates_v5_assumptions.json`. They are useful
for ordering the smoke tests, not for scheduling full benchmark execution. Full-run timing and
total compute remain `BLOCKED` until imported S1 measurements replace the proxies.

## Exact next action

Execute the five frozen checkpoints as S1, use imported throughput/OOM/extraction evidence to
update feasibility, then add exact checkpoint revisions from at least five additional families
and rerun the planner before freezing the S3 roster.
