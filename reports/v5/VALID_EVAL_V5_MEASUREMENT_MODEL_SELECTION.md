# ValidEval V5 Measurement-Model Selection

## Verdict

**Status: `EXPLORATORY_MODEL_REPRODUCED_PSYCHOMETRIC_VALIDITY_BLOCKED`.** The historical matrix
passes minimum adequacy checks and the selected transparent decomposition runs successfully.
Neither fact validates IRT assumptions, identifies a full 2PL, or establishes construct
validity.

## Gate rename and stale-artifact boundary

The canonical diagnostic is now `minimum_matrix_adequacy`; `panel_validity` remains only a
backward-compatible alias. Its required interpretation is:

> Passing this gate permits exploratory matrix analysis; it does not validate psychometric
> assumptions or establish construct validity.

The V5 run on the reproduced MMLU matrix passes with 39 models, 14,042 items, zero missingness,
and ability spread 0.5802. It explicitly records `psychometric_validity_established=false`.
Older stored reports that say the panel supports psychometric interpretation are `STALE` and
must not be cited as the V5 conclusion.

## Assumption audit

| Assumption | Current evidence | State |
|---|---|---|
| Model and item count, missingness, ability spread | directly checked on reproduced matrix | `REPRODUCED` minimum adequacy only |
| Subject nesting | 57 subjects encoded in canonical item IDs | `REPRODUCED` |
| Family concentration | inferred map has 10 families; largest named family is 11/39 | `INFERRED` |
| Unidimensionality | not tested with a confirmatory latent model | `BLOCKED` |
| Multidimensionality | subject interactions are descriptive, not a dimension-selection test | `BLOCKED` |
| Local item independence | not established; templates and content may induce dependence | `BLOCKED` |
| Respondent/model independence | checkpoints share training, architecture, and family lineage | `BLOCKED` |
| Invariance across families and prompt regimes | exact historical revisions/prompts unavailable | `BLOCKED` |
| Item-discrimination identifiability | 39 dependent respondents are insufficient for an unrestricted 2PL claim | `BLOCKED` |
| Prompt and extraction method variance | fixed historical artifacts do not identify these components | `BLOCKED` |
| Saturation | no model is within the configured 0.01 floor/ceiling bound | `REPRODUCED` under this matrix |
| Benchmark contamination | absence cannot be proven from repository artifacts | `BLOCKED` |

## Candidate-method decision

| Method | Scientific role | Decision |
|---|---|---|
| Legacy proxy IRT | diagnostic weighting baseline | retain only as a proxy; never call 2PL |
| Rasch/1PL | simple unidimensional benchmark | future controlled-panel comparator after assumption checks |
| Regularized 2PL or Bayesian IRT | item discrimination and uncertainty | block until an adequate independent panel and recovery study exist |
| Multidimensional/hierarchical IRT | explicit subject/domain structure | future work; current panel does not justify the complexity |
| Matrix factorization | predictive low-rank baseline | optional comparator, not a validity model |
| Mixed-effects logistic model | transparent model/subject/interaction decomposition | selected conceptual target for later controlled data |
| Regularized subject-conditioned logit decomposition | closed-form exploratory approximation | implemented now |
| Generalizability theory | variance decomposition across facets | useful future comparator when prompt/extraction facets are crossed |
| Nonparametric response curves | assumption-light item behavior | optional exploratory analysis with a larger exact panel |

The implemented method is deliberately named
`regularized_subject_conditioned_logit_decomposition`. It is not a likelihood-fitted mixed
model, Rasch model, Bayesian model, or full 2PL.

## Reproduced exploratory fit

The model uses centered model effects, centered subject effects, and shrunken model-by-subject
interaction logits. It is closed form, so convergence is deterministic and no iterative
optimizer is claimed. On the historical matrix:

- assumption gate: pass for the configured minimums;
- centered-effect constraints: numerically zero means;
- Brier score: 0.17839; additive baseline: 0.18194;
- log loss: 0.53317; additive baseline: 0.54285;
- synthetic recovery fixture: `PASS`, ability Spearman 0.9816 and subject-easiness Spearman 1.0.

The recovery result is `NON_EVIDENCE_FIXTURE`. The fit improvements are in-sample and must not
be presented as calibrated generalization.

## Validation ceiling

Implemented safeguards cover identifiability centering, approximate parameter uncertainty,
closed-form convergence, additive-baseline comparison, minimum panel checks, family-
concentration failure behavior, and synthetic ordering recovery.

Still required before a psychometric paper claim: held-out calibration, repeated panel-size
sensitivity, explicit duplication perturbations, local-dependence tests, invariance tests,
prompt/extraction facets, and recovery under misspecification. The one-subset-per-size output is
a deterministic smoke check and not a stability estimate.

## Exact next action

After Study C reaches the exact S3 panel, compare a preregistered Rasch/1PL baseline with the
regularized subject-conditioned model using held-out items, family-deduplicated panels,
duplication perturbations, and calibration diagnostics. Keep 2PL and latent-validity claims
blocked unless those checks pass.

