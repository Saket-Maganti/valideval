# Diagnostic Validation

## 1. Why Diagnostics Need Validation

ValidEval treats benchmark-validity diagnostics as measurement instruments. A diagnostic should not
support a benchmark claim until it has evidence about sensitivity, false-positive behavior,
specificity, transfer, materiality, and failure modes under a documented protocol.

The legacy evidence in this section is synthetic harness output only. A deeper audit found that the
current controlled synthetic harness is circular by construction: injected flaw metadata influences
controlled model behavior, and the readout changes by diagnostic/flaw family. Current synthetic AUCs
therefore remain historical wiring/sanity-check artifacts and are not treated as independent
diagnostic-validation evidence. They do not establish that any real benchmark has or lacks a
validity threat.

## 2. Legacy Controlled Synthetic Flaw Injection

The durable legacy controlled synthetic artifacts are:

- `validation_reports/diagnostic_validation_summary.md`
- `validation_reports/diagnostic_validation_summary.json`

The summary reports 12 diagnostic/flaw experiments. Ten were historically marked
`credible_under_synthetic_harness`, two are marked `prototype_only`, and none are quarantined. Those
labels are preserved below for traceability only. They are not current paper-facing evidence labels.

| Diagnostic | Flaw | Status | ROC AUC | PR AUC | Clean FPR | Materiality |
|---|---|---|---:|---:|---:|---|
| `answer_distribution` | `answer_length_artifact` | `credible_under_synthetic_harness` | 1.0 | 1.0 | 0.0 | statistically detectable |
| `answer_distribution` | `label_imbalance` | `prototype_only` | 0.9659750021522039 | 0.9605167620394999 | 0.20738636363636365 | statistically detectable |
| `distractor_quality` | `dead_distractors` | `prototype_only` | 0.7385117151629935 | 0.6955696656570433 | 0.006628787878787845 | statistically detectable |
| `extraction_robustness` | `extraction_ambiguity` | `credible_under_synthetic_harness` | 1.0 | 1.0 | 0.0 | statistically detectable |
| `extraction_robustness` | `scoring_ambiguity` | `credible_under_synthetic_harness` | 1.0 | 1.0 | 0.0 | negligible |
| `irt` | `low_discrimination` | `credible_under_synthetic_harness` | 0.9985795454545454 | 0.9978452774549815 | 0.06628787878787878 | statistically detectable |
| `irt` | `negative_discrimination` | `credible_under_synthetic_harness` | 0.909086367556425 | 0.8718164100208852 | 0.02341137123745818 | statistically detectable |
| `redundancy` | `redundancy` | `credible_under_synthetic_harness` | 0.9910037878787878 | 0.992911321521563 | 0.0 | practically material |
| `reliability` | `prompt_format_fragility` | `credible_under_synthetic_harness` | 1.0 | 1.0 | 0.05018939393939392 | practically material |
| `saturation` | `too_easy_saturation` | `credible_under_synthetic_harness` | 0.8939393939393939 | 0.7715054231830228 | 0.0 | practically material |
| `saturation` | `too_hard_floor` | `credible_under_synthetic_harness` | 0.9887125875229569 | 0.978021696421031 | 0.0445075757575758 | statistically detectable |
| `shortcut` | `shortcut_signal` | `credible_under_synthetic_harness` | 0.9166168969524794 | 0.8888135921564225 | 0.014204545454545414 | practically material |

## 3. Diagnostic Sensitivity

Controlled synthetic flaw injection currently supports only a wiring/sanity-check statement: the
legacy diagnostics and report plumbing can separate some known injected synthetic signatures from
clean synthetic runs under the implemented generators. Because the controlled model can branch on
`is_flawed` and `flaw_type`, this is not an independent sensitivity claim.

All rows remain useful for development and regression checks, but none should be promoted to
paper-ready diagnostic-validation evidence without a decoupled, flaw-agnostic harness.

## 4. Cross-Flaw Specificity

The cross-flaw artifacts are:

- `results/neurips_small_runs/cross_flaw_confusion/summary.md`
- `results/neurips_small_runs/cross_flaw_confusion/cross_flaw_matrix.json`

The summary reports 64 pairings and 7 strong off-target activations. Using AUC >= 0.8, the strong
off-target activations are:

| Diagnostic | Off-target flaw | AUC |
|---|---|---:|
| `shortcut` | `too_easy_saturation` | 1.0 |
| `distractor_quality` | `prompt_format_fragility` | 0.9928385416666666 |
| `distractor_quality` | `too_easy_saturation` | 0.9694010416666666 |
| `redundancy` | `shortcut_signal` | 0.9791666666666666 |
| `saturation` | `shortcut_signal` | 0.875 |
| `saturation` | `prompt_format_fragility` | 0.875 |
| `saturation` | `extraction_ambiguity` | 0.875 |

This is useful legacy specificity context because it exposes off-target activation risks. It does not
support a claim that diagnostics fire only on intended threat families, and it is not primary
diagnostic-validation evidence under the circularity audit.

The 7 off-target cases are frozen in `CROSS_FLAW_AND_HELDOUT_FAILURE_CASES.md`. Any future
investigation should follow `PREREGISTERED_CROSS_FLAW_HELDOUT_INVESTIGATION_PLAN.md`; until then,
cross-flaw specificity remains `WEAK`.

## 5. Held-Out Generator Transfer

The held-out artifacts are:

- `results/neurips_small_runs/heldout_generators/summary.md`
- `results/neurips_small_runs/heldout_generators/heldout_transfer.json`

The summary reports 6 held-out families and 3 paper-eligible families.

| Diagnostic | Family | Original AUC | Held-out AUC | Transfer drop | Paper-eligible |
|---|---|---:|---:|---:|---|
| `shortcut` | `paraphrased_shortcut_artifact` | 0.9281684027777778 | 0.5 | 0.4281684027777778 | false |
| `distractor_quality` | `distractor_plausibility_skew` | 0.7039930555555556 | 0.5629340277777778 | 0.1410590277777778 | false |
| `redundancy` | `item_cluster_redundancy` | 0.9895833333333334 | 0.5 | 0.48958333333333337 | false |
| `irt` | `ability_dependent_inversion` | 1.0 | 1.0 | 0.0 | true |
| `shortcut` | `coverage_blindspot` | 0.8582899305555556 | 0.8040364583333334 | 0.05425347222222221 | true |
| `extraction_robustness` | `extraction_ambiguity` | 1.0 | 1.0 | 0.0 | true |

Held-out evidence is mixed and remains legacy synthetic transfer context. It can motivate future
decoupled transfer tests, but it no longer supports detector-specific transfer claims as primary
paper evidence.

The 3 non-paper-eligible transfer families are frozen in
`CROSS_FLAW_AND_HELDOUT_FAILURE_CASES.md`. Any future investigation should follow
`PREREGISTERED_CROSS_FLAW_HELDOUT_INVESTIGATION_PLAN.md`; until then, held-out generator transfer
remains `WEAK`.

## 6. False-Positive and Null Controls

Clean/null behavior is estimated from strength 0.0 synthetic runs. The legacy controlled synthetic summary
reports clean FPR for all 12 experiments. The 10 credible rows have clean FPR values from 0.0 to
0.06628787878787878. The prototype-only `answer_distribution / label_imbalance` row has clean FPR
0.20738636363636365 and should not be treated as paper-ready.

The harness applies Benjamini-Hochberg correction to empirical null p-values for per-item flags when
possible. These controls are legacy synthetic-generator sanity checks, not independent
diagnostic-validation or real-benchmark error-control claims.

## 7. Materiality and Power

Materiality labels are present in the controlled synthetic JSON. Four diagnostic/flaw pairs are marked
`practically material`: `redundancy / redundancy`, `reliability / prompt_format_fragility`,
`saturation / too_easy_saturation`, and `shortcut / shortcut_signal`.

The `extraction_robustness / scoring_ambiguity` row is marked `negligible` despite AUC 1.0, which
blocks an AUC-only importance claim.

Power evidence remains limited. `results/toy_mcq/mock/power.json` exists as a toy planning artifact,
with minimum detectable difference 0.25433934108924844 and a do-not-overinterpret band of
25.433934108924845 points. This is not synthetic diagnostic-validation power evidence.

[RESULT REQUIRED: synthetic-harness power analysis]

## 8. Evidence Status

| Evidence block | Status | Interpretation |
|---|---|---|
| Legacy controlled synthetic flaw detection | DEMOTED_TO_WIRING_CHECK | Current synthetic AUCs are historical sanity-check artifacts, not independent diagnostic-validation evidence |
| Cross-flaw specificity | WEAK | 64 pairings exist, but 7 strong off-target activations remain |
| Held-out generator transfer | WEAK | 6 families exist, but only 3 are paper-eligible |
| False-positive / null control | DEMOTED_TO_WIRING_CHECK | Clean FPR and null controls are legacy synthetic-generator sanity checks only |
| Materiality thresholding | WEAK | Materiality labels exist, but several remain generic or non-practical |
| Power analysis | WEAK | Toy power exists; synthetic-harness power remains result-required |
| Calibration | BLOCKED | Numeric calibration requires confidence/logprob outputs |
| Synthetic-to-real transfer | NOT_RUN | No artifact validates synthetic thresholds on real benchmark outcomes |
| Decoupled synthetic diagnostic validation | RESULT_REQUIRED | No decoupled flaw-agnostic harness run exists |

## 9. What This Supports

- ValidEval provides a legacy controlled synthetic wiring/sanity-check harness.
- Historical synthetic AUCs remain traceable as old sanity-check artifacts.
- Clean/null behavior and FPR can be reported only as legacy synthetic-generator sanity checks.
- Cross-flaw and held-out artifacts identify specificity and transfer risks.
- Materiality labels can prevent detector separability from becoming an automatic importance claim.
- The claims ledger can block unsupported diagnostic claims.

## 10. What This Does Not Support

- Universal diagnostic generalization.
- Real-benchmark validity conclusions from synthetic evidence alone.
- Current synthetic AUCs as primary positive diagnostic-validation evidence.
- Real benchmark error-detection claims.
- MMLU-Redux diagnostic-validation success claims.
- GPQA establishes real benchmark validity.
- Numeric calibration has been established without confidence/logprob outputs.

## 11. Remaining Result Requirements

- `[RESULT REQUIRED: synthetic-harness power analysis]`
- `[RESULT REQUIRED: decoupled flaw-agnostic synthetic diagnostic-validation harness]`
- `[RESULT REQUIRED: numeric calibration with confidence/logprob outputs]`
- `[RESULT REQUIRED: human-reviewed real-benchmark threshold calibration]`
- `[RESULT REQUIRED: confirmatory cross-flaw and held-out investigation under preregistered plan]`
