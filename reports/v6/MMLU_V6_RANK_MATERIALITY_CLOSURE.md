# MMLU V6 Rank-Materiality Closure

Gate: `RANK_MATERIALITY_ANALYSIS_READY`

The deterministic closure ran on the reproduced historical Study H matrix: 39 models, 14,042 items,
57 subjects, seed 2027, 500 subject bootstraps, and 500 additive-null simulations. Status was
`REPRODUCED`.

Observed Kendall's W was 0.8781. The observed median rank range was 18.5 and maximum was 29.0.
Under this registered additive null, the corresponding exceedance probabilities were 0.2016 and
0.1357. These results reinforce the V5 correction: raw rank dispersion is null-dependent and does
not justify an arbitrary universal severity threshold.

Family closure includes a 10-family equal-weight checkpoint bootstrap and leave-one-family-out
sensitivity. The latter retained essentially perfect Spearman agreement for the remaining named
checkpoints under every held-out family. A naive model bootstrap was formally rejected for fixed
checkpoint ranks because it omits named checkpoints and duplicates others; the family-balanced
resampling estimand is reported instead.

The evidence is conditional on this response matrix, resampling design, and null model. It does not
prove global benchmark validity or invalidity. Detailed machine results are under the ignored local
analysis directory `results/mmlu/rank_materiality_v6`.
