# ValidEval V7 Measurement Regime Study

Gate: `MEASUREMENT_REGIME_STUDY_COMPLETE`.

Nineteen deterministic regimes varied model count (5–120), family dependence, skew, multimodality,
heavy tails, latent dimension, missingness, and saturation. Evaluation used held-out response cells
and compared aggregate ability, additive subject difficulty, regularized subject-conditioned, and
low-rank predictions.

The corrected positive-discrimination generator produced: {'CAUTION': 1, 'SUPPORTED': 16, 'UNIDENTIFIABLE': 1, 'UNRELIABLE': 1}. This maps where
the declared estimators recover the known synthetic target. It does not establish that a real
benchmark has a scalar or multidimensional latent trait. In particular, the map must guide model
choice rather than justify fitting the most complex model everywhere.

Runtime: 0.29 seconds. Backing table:
`results/v7/measurement/regime_study/regime_map.csv`.
