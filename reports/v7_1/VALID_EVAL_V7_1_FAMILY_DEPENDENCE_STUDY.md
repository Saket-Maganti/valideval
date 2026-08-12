# ValidEval V7.1 Family-Dependence Study

Status: `FAMILY_DEPENDENCE_STRESS_READY`.

The stress table crosses four decision methods, family correlations 0.0, 0.5, and 0.9, and three
effective-N settings. Increasing dependence reduces power for the CI and FDR methods even when raw
sample size is held large, illustrating why checkpoint count is not an independence count.

Mean naive false-license rate rose from 0.382 at correlation 0.0 to about 0.402 at 0.9. CI-only and
FDR-only false-license rates remained much smaller in this simulation, while full licensing issued
no licenses. Coverage remained near 0.95. These are simulation-family-specific operating
characteristics, not empirical model-family population estimates.

The historical influence analysis now also partitions whole families: each of five policies used
24 discovery and 15 held-out models with a recorded family-overlap count of zero.
