# MMLU V7 Full Uncertainty and Null Analysis

Gate: `STUDY_H_REPRODUCED_WITH_LIMITATIONS`.

Study H reproduced the 39-model, 14,042-item, 57-subject historical MMLU analysis with 500 nested
subject/item bootstraps, 500 family-cluster bootstraps, leave-one-family-out, equal-family weighting,
and seven null generators. Kendall's W was 0.878 with bootstrap interval
[0.860, 0.898]. The top four aggregate ranks
were point-stable in the nested bootstrap, while lower ranks had wider sets.

The main limitation is null sensitivity. Median-rank-range exceedance probabilities ranged from
0.010 to
1.000. Additive and fixed-margin nulls make the observed
dispersion look unusual; family-correlated and latent-factor nulls do not. Therefore the result is
evidence consistent with subject-dependent ranking under several protocols, not a null-invariant
proof of instability.

Runtime: 10.25 seconds. All tables are under `results/v7/study_h/`.
