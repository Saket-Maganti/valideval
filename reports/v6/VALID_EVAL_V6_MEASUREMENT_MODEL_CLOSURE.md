# ValidEval V6 Measurement-Model Closure

Gate: `MEASUREMENT_MODEL_PLAN_DEFENSIBLE`

The selected model remains a transparent regularized subject-conditioned logistic decomposition,
not a forced 2PL. It was evaluated on the reproduced 39×14,042 historical MMLU matrix with a
seeded 20% held-out-item split.

At interaction shrinkage 10, held-out Brier score was 0.17870 and log loss 0.53487, compared with
0.18160/0.54241 for the additive baseline and 0.19721/0.58085 for the aggregate-model baseline.
The 100-replicate Brier interval was [0.17763, 0.18000] and expected calibration error was 0.00926.
Shrinkage values 2, 10, and 50 produced Brier scores from 0.17869 to 0.17873. A one-checkpoint-per-
family sensitivity gave Brier 0.19050 versus 0.19242 for its additive baseline, with ECE 0.01170.

The deterministic `NON_EVIDENCE_FIXTURE` synthetic recovery check produced ability Spearman 0.9816
and subject-easiness Spearman 1.0. That result tests implementation behavior only.

These findings support the model as an exploratory response-summary plan under this protocol. They
do not establish unidimensionality, local independence, invariance, latent-trait validity, or
construct validity. Detailed machine results are in
`results/mmlu/measurement_model_closure_v6.json`.
