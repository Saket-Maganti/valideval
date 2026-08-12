# ValidEval V7.1 Study-H Estimand Sensitivity

Status: `STUDY_H_V7_1_REPRODUCED_WITH_LIMITATIONS`.

The cached historical panel contains 39 models, ten inferred families, 57 subjects, and 14,042
items. V7.1 separates the canonical item-weighted score from a balanced subject-weighted score.
Their model-rank Spearman correlation was 0.99615 and the winner did not change, but this high
agreement does not erase model-level rank differences or the estimand distinction.

Headline rank uncertainty uses 500 nested subject/item draws and simultaneous rank confidence
sets. Pairwise decisions use BH FDR with Holm sensitivity. The sensitivity grid uses 100 Monte Carlo
replicates per cell and reports Monte Carlo SE plus 2.5% and 97.5% quantiles.

The observed Kendall's W was 0.8781 with bootstrap interval [0.8599, 0.8983]. Null conclusions are
generator-sensitive. Results are conditional on observed checkpoints, inferred families, cached
responses, estimand, and resampling protocol; Study H is not population-generalization evidence.
