# ValidEval V7.1 Study-C Power Redesign

Status: `PRIMARY_ESTIMAND_POWER_PLANNING_READY`.

The 72-cell, 500-replicate-per-cell grid covers pairwise accuracy difference, model-rank
correlation, model×benchmark interaction, family×benchmark interaction, diagnostic transport,
top-k stability, claim-license rate, and repair effect. Model, family, benchmark, and item counts,
family correlation, measurement error, and transport heterogeneity are active inputs. Every cell
reports Monte Carlo SE and a power interval.

Only two of 72 cells cleared 0.80, and neither made all declared primary estimands adequate. The S2,
S3, and S4 summaries therefore have empty `adequate_primary_estimands` sets and
`s3_minimum_scientific_label_permitted=false`. The highest simulated powers by estimand included
0.952 for repair effect and 0.774 for top-k stability; claim-license rate never exceeded 0.056.

These values are planning simulations. S2 measurements must replace throughput, measurement-error,
and heterogeneity assumptions before any S3 authorization decision.
