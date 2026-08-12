# ValidEval V7.1 Null-Model Contracts

Status: `NULL_MODEL_CONTRACTS_READY_WITH_SENSITIVITY_FLAG`.

Study H reports seven null generators with machine-readable `fixed`, `estimated`, `randomized`, and
`hypothesis` fields:

- `SUBJECT_SIZE_ONLY`
- `ADD_ABILITY_SUBJECT`
- `FIXED_PRIOR_SHRUNK_ADDITIVE`
- `MODEL_TOTAL_SUBJECT_SIZE_HYPERGEOMETRIC`
- `LATENT_FACTOR_NULL`
- `FAMILY_CORRELATED_NULL`
- `DETERMINISTIC_MODEL_SUBJECT_PERTURBATION_NULL`

The former “empirical Bayes” label is now fixed-prior shrinkage, the former fixed-margin label now
states the margins actually held fixed, and deterministic perturbations are not called a random
effects model. Each method used 200 simulations. The observed null exceedance probabilities vary
substantially across generators, so `null_model_sensitivity_flag` is true and no single null is
presented as uniquely correct.
