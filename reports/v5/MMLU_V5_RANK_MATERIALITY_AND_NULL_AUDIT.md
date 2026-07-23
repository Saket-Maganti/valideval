# MMLU V5 Rank Materiality and Null Audit

## Verdict

**Status: `REPRODUCED`, conditional on the historical response matrix and stated protocols.**
Subject-level rankings vary, but the conclusion that dispersion exceeds chance is not robust to
the null model. The old “severe rank range ≥10” headline is `RETIRED`.

## Frozen input and command

- Matrix: `results/evidence/mmlu_reproduction_v5/matrix.reconstructed.v5.csv`
- Matrix SHA-256: `f85a0a44f3203de2863d86bf13b2c81d8e934ae4c07b826193b5e93a3fc86e74`
- Shape: 39 models × 14,042 items; 57 subjects; no missing cells
- Family map: `configs/models/study_h_family_map_v5.csv`; every family label is `INFERRED`
- Seed: 2027
- Item-within-subject bootstrap replicates: 500
- Primary additive-null simulations: 500
- Practical reversal threshold: absolute accuracy difference 0.01

```bash
python3 scripts/run_mmlu_rank_materiality_v5.py \
  --matrix results/evidence/mmlu_reproduction_v5/matrix.reconstructed.v5.csv \
  --model-family-map configs/models/study_h_family_map_v5.csv \
  --bootstrap 500 --null-simulations 500 \
  --output results/mmlu/rank_materiality_v5
```

## Null-calibrated result

Observed median rank range was 18.5 and observed maximum rank range was 29.0 using tie-aware
average ranks. Add-one exceedance probabilities were:

| Null | Median-range exceedance probability | Maximum-range exceedance probability | Interpretation |
|---|---:|---:|---|
| Ability + subject-difficulty additive | 0.202 | 0.136 | does not reject this richer null |
| Empirical-Bayes additive | 0.178 | 0.124 | does not reject this shrinkage null |
| Model ability with subject sizes only | 0.006 | 0.044 | exceeds this simpler null |
| Within-model margin-preserving permutation | 0.014 | 0.044 | exceeds this permutation null |

All four results use 500 simulations. Their disagreement is the central scientific finding:
subject structure can explain much of the raw dispersion under additive and empirical-Bayes
nulls. A benchmark-anomaly claim based on rank range alone is not robust.

## Materiality profile

- Kendall’s W across subject rankings: 0.878.
- The 1,596 subject-pair Spearman correlations have median 0.889, 5th percentile 0.759, and
  minimum 0.581.
- Median top-k Jaccard across subject pairs is 0.000 at k=1, 0.333 at k=3, 0.429 at k=5, and
  0.583 at k=10; ties are included at the boundary.
- Leaving out one subject preserves the aggregate ranking closely: minimum Spearman with the
  full ranking is 0.9992, and the maximum absolute change is two ranks.
- Bootstrap resampling of benchmark composition gives per-model rank intervals with median
  width about two positions; item-within-subject rank intervals are much wider, with median
  width 9.76 positions across model-subject cells.
- At the fixed one-percentage-point threshold, 2,376 subject-level reversals occur across 409
  unique model pairs and all 57 subjects. These are conditional pairwise findings, not a count
  of invalid items or models.
- Family-deduplicated and leave-one-family-out outputs were reproduced, but the family map is
  inferred from model names. Those sensitivity results therefore inherit `INFERRED` identity.

The full output directory also contains pairwise outranking probabilities, top-1/3/5/10
membership probabilities, normalized rank ranges, rank entropy, subject correlations,
leave-one-subject-out sensitivity, effect-size-filtered reversals, and benchmark-composition
rank confidence intervals.

## Hierarchical subject decomposition

The transparent regularized subject-conditioned logit decomposition reproduced on the matrix.
It separates a centered overall model effect, centered subject easiness, and shrunken
model-by-subject interactions. Its in-sample Brier score is 0.17839 versus 0.18194 for the
additive baseline; its in-sample log loss is 0.53317 versus 0.54285. These differences are
descriptive in-sample fit, not held-out predictive evidence or causal subject effects.

## Coverage and remaining gaps

Implemented: tie-aware ranks, item-within-subject bootstrap, subject-composition bootstrap,
four null generators, additive empirical-Bayes shrinkage, pairwise/top-k materiality,
leave-one-subject-out, family-deduplicated ranking, and leave-one-family-out.

Still `BLOCKED` for a maximum-ceiling confirmatory analysis: an explicit family-cluster
bootstrap, a justified model-bootstrap estimand, broader null sensitivity preregistration,
exact family identities, and held-out calibration of the hierarchical model. The single seeded
panel-size subsets are implementation checks, not stable sensitivity estimates.

## Paper-ready wording

> Under this historical 39-model MMLU panel, subject-conditioned rankings show locally
> meaningful pairwise reversals and low top-k overlap despite high overall concordance. Whether
> the observed rank dispersion exceeds a null is model-dependent: it exceeds simpler
> exchangeability nulls but not ability-plus-subject-difficulty or empirical-Bayes additive
> nulls. The result is evidence consistent with subject-sensitive ranking, not proof that MMLU
> or any model ranking is globally invalid.

