# ValidEval V7.1 Pairwise Multiplicity

Status: `PAIRWISE_MULTIPLICITY_READY`.

Study-H all-pairs inference defines one family, `ALL_MODEL_PAIRS`, across 741 comparisons. The
primary adjustment is Benjamini–Hochberg FDR and the sensitivity adjustment is Holm FWER. A single
prespecified comparison is explicitly distinguishable from an all-pairs leaderboard family.

In the cached 39-model Study-H panel, BH rejected 677 pairs while Holm rejected none. This large
difference is exactly why unadjusted marginal intervals are not reported as a collection of
licensed directional decisions. The result is conditional on the historical panel and joint
bootstrap protocol.
