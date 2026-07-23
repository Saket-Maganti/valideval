# Synthetic Validation Artifact Inventory

## 1. Executive Summary

Existing local artifacts support a cautious synthetic diagnostic-validation narrative. The strongest
evidence is controlled synthetic flaw detection: `validation_reports/diagnostic_validation_summary.md`
reports 12 diagnostic/flaw experiments, with 10 marked `credible_under_synthetic_harness`, 2 marked
`prototype_only`, and none quarantined.

Cross-flaw and held-out generator artifacts also exist, but both are mixed. Cross-flaw validation
covers 64 diagnostic/flaw pairings and reports 7 strong off-target activations. Held-out generator
transfer covers 6 families and marks 3 as paper-eligible. These artifacts support evidence-gated,
diagnostic-specific claims only; they do not support universal diagnostic generalization.

No new validation was run for this inventory. All findings below are from existing local artifacts.

## 2. Artifacts Found

| Artifact | Path | Type | Metrics Present | Usable For Paper? | Caveats |
|---|---|---|---|---|---|
| Diagnostic validation summary | `validation_reports/diagnostic_validation_summary.md` | Markdown summary | 12 experiments; ROC AUC; PR AUC; clean FPR; monotonicity; credibility status | Yes | Controlled synthetic generators only; no real benchmark claims |
| Diagnostic validation JSON | `validation_reports/diagnostic_validation_summary.json` | JSON summary | Per-experiment metrics; calibration curves; materiality; multiplicity flags; limitations | Yes | Large detailed artifact; use summary values, not per-item internals |
| Synthetic validation caches | `validation_reports/_cache/` | Intermediate matrices/predictions | Matrices, metadata, predictions | No, except as provenance | Durable paper evidence is the report JSON/Markdown |
| Cross-flaw summary | `results/neurips_small_runs/cross_flaw_confusion/summary.md` | Markdown summary | 64 pairings; 7 strong off-target activations | Yes | Summary does not list every off-target row |
| Cross-flaw matrix | `results/neurips_small_runs/cross_flaw_confusion/cross_flaw_matrix.json` | JSON matrix | AUC; false-positive rate; specificity; target-pairing flag; paper-eligible flag | Yes | Mixed specificity; 7 off-target rows have AUC >= 0.8 |
| Cross-flaw CSV/heatmap data | `results/neurips_small_runs/cross_flaw_confusion/cross_flaw_matrix.csv`, `results/neurips_small_runs/cross_flaw_confusion/heatmap_data.csv` | Tabular data | Matrix-ready cross-flaw values | Yes | Use with JSON/summary for interpretation |
| Held-out summary | `results/neurips_small_runs/heldout_generators/summary.md` | Markdown summary | 6 families; 3 paper-eligible families | Yes | Large transfer drops must be reported as limitations |
| Held-out transfer matrix | `results/neurips_small_runs/heldout_generators/heldout_transfer.json` | JSON table | Original AUC; held-out AUC; transfer drop; paper-eligible flag | Yes | Mixed transfer; not real benchmark evidence |
| Held-out CSV | `results/neurips_small_runs/heldout_generators/heldout_transfer.csv` | Tabular data | Same held-out transfer fields | Yes | Use JSON/summary for interpretation |
| Synthetic validation config | `configs/validation/synthetic_default.yaml` | Config | 8 diagnostics; 8 flaws; strength grid `[0.0, 1.0]`; seed 0; 48 items | Context only | Config is not an empirical result |
| Held-out validation config | `configs/validation/heldout_default.yaml` | Config | 6 held-out families; strength grid `[0.0, 1.0]`; seed 0; 48 items | Context only | Config is not an empirical result |
| Calibration config | `configs/diagnostics/calibration.yaml` | Config | 10 bins and perturbation variants | Context only | No synthetic numeric calibration result by itself |
| Power config | `configs/diagnostics/power.yaml` | Config | 500 bootstrap samples; seed 0 | Context only | No synthetic-harness power result by itself |
| Toy calibration result | `results/toy_mcq/mock/calibration.json` | JSON diagnostic result | Calibration status; abstention proxy; prompt-consistency proxy | Limited | Numeric ECE/Brier/NLL blocked because confidence/logprob values are missing |
| Toy power result | `results/toy_mcq/mock/power.json` | JSON diagnostic result | Minimum detectable difference; effective item count; required item counts | Limited | Toy planning aid, not synthetic diagnostic-validation power evidence |

## 3. Synthetic Flaw Families Found

Controlled validation summary:

- `answer_length_artifact`
- `label_imbalance`
- `dead_distractors`
- `extraction_ambiguity`
- `scoring_ambiguity`
- `low_discrimination`
- `negative_discrimination`
- `redundancy`
- `prompt_format_fragility`
- `too_easy_saturation`
- `too_hard_floor`
- `shortcut_signal`

Cross-flaw grid:

- `shortcut_signal`
- `label_imbalance`
- `dead_distractors`
- `redundancy`
- `low_discrimination`
- `prompt_format_fragility`
- `extraction_ambiguity`
- `too_easy_saturation`

Held-out families:

- `paraphrased_shortcut_artifact`
- `distractor_plausibility_skew`
- `item_cluster_redundancy`
- `ability_dependent_inversion`
- `coverage_blindspot`
- `extraction_ambiguity`

## 4. Diagnostics Found

- `answer_distribution`
- `distractor_quality`
- `extraction_robustness`
- `irt`
- `redundancy`
- `reliability`
- `saturation`
- `shortcut`

## 5. Cross-Flaw Evidence Found

`results/neurips_small_runs/cross_flaw_confusion/summary.md` reports:

- Pairings tested: 64.
- Strong off-target activations: 7.

The JSON matrix shows 8 target rows, 7 of which are paper-eligible. The target pairing
`distractor_quality / dead_distractors` is not paper-eligible in the matrix.

Strong off-target rows using AUC >= 0.8:

| Diagnostic | Off-target flaw | AUC | Clean FPR | Specificity |
|---|---|---:|---:|---:|
| `shortcut` | `too_easy_saturation` | 1.0 | 0.0625 | 0.9375 |
| `distractor_quality` | `prompt_format_fragility` | 0.9928385416666666 | 0.02083333333333337 | 0.9791666666666666 |
| `distractor_quality` | `too_easy_saturation` | 0.9694010416666666 | 0.02083333333333337 | 0.9791666666666666 |
| `redundancy` | `shortcut_signal` | 0.9791666666666666 | 0.0 | 1.0 |
| `saturation` | `shortcut_signal` | 0.875 | 0.0 | 1.0 |
| `saturation` | `prompt_format_fragility` | 0.875 | 0.0 | 1.0 |
| `saturation` | `extraction_ambiguity` | 0.875 | 0.0 | 1.0 |

Interpretation: cross-flaw evidence exists, but it is mixed. It supports a specificity audit, not a
claim that diagnostics fire only on intended flaw families.

## 6. Held-Out Generator Evidence Found

`results/neurips_small_runs/heldout_generators/summary.md` reports:

- Families tested: 6.
- Paper-eligible families: 3.

Held-out transfer rows:

| Diagnostic | Family | Original flaw | Held-out flaw | Original AUC | Held-out AUC | Transfer drop | Paper-eligible |
|---|---|---|---|---:|---:|---:|---|
| `shortcut` | `paraphrased_shortcut_artifact` | `shortcut_signal` | `keyword_artifact` | 0.9281684027777778 | 0.5 | 0.4281684027777778 | false |
| `distractor_quality` | `distractor_plausibility_skew` | `dead_distractors` | `answer_length_artifact` | 0.7039930555555556 | 0.5629340277777778 | 0.1410590277777778 | false |
| `redundancy` | `item_cluster_redundancy` | `redundancy` | `context_leakage` | 0.9895833333333334 | 0.5 | 0.48958333333333337 | false |
| `irt` | `ability_dependent_inversion` | `low_discrimination` | `negative_discrimination` | 1.0 | 1.0 | 0.0 | true |
| `shortcut` | `coverage_blindspot` | `context_irrelevance` | `context_leakage` | 0.8582899305555556 | 0.8040364583333334 | 0.05425347222222221 | true |
| `extraction_robustness` | `extraction_ambiguity` | `scoring_ambiguity` | `extraction_ambiguity` | 1.0 | 1.0 | 0.0 | true |

Interpretation: held-out transfer evidence is present but mixed. It supports detector-specific
transfer claims for the paper-eligible families only.

## 7. FPR / Error-Control Evidence Found

The controlled diagnostic-validation summary reports clean FPR for all 12 diagnostic/flaw
experiments. Credible synthetic-harness diagnostics have clean FPR values ranging from 0.0 to
0.06628787878787878 in the summary table. The prototype-only `answer_distribution / label_imbalance`
case has clean FPR 0.20738636363636365 and should not be treated as paper-ready.

The Markdown summary states that clean/null behavior is estimated from strength 0.0 synthetic runs
and that the harness applies Benjamini-Hochberg correction to empirical null p-values for per-item
flags when possible.

## 8. Materiality Evidence Found

Materiality fields are present in `validation_reports/diagnostic_validation_summary.json`.

Practical-materiality rows:

- `redundancy / redundancy`
- `reliability / prompt_format_fragility`
- `saturation / too_easy_saturation`
- `shortcut / shortcut_signal`

Other rows are marked `statistically detectable` or `negligible`. The `extraction_robustness /
scoring_ambiguity` row is marked `negligible` despite AUC 1.0, which is an important reminder that
detector separability is not automatically practical materiality.

## 9. Missing Evidence

- Synthetic-harness-specific power analysis remains missing.
- Numeric calibration metrics remain blocked where confidence/logprob outputs are unavailable.
- Cross-flaw specificity has mixed evidence and off-target activations.
- Held-out generator transfer has mixed evidence and large transfer drops for 3 of 6 families.
- Synthetic validation does not establish real benchmark validity or real benchmark error detection.
- Human-reviewed real-benchmark calibration remains missing.

## 10. Recommended Next Runs

Do not run these without explicit approval. Recommended next runs are:

1. Investigate the 7 strong cross-flaw off-target activations with preregistered downgrade rules.
2. Extend held-out generator transfer for families with large drops.
3. Add confidence/logprob-bearing artifacts before numeric calibration claims.
4. Add synthetic-harness-specific power analysis.
5. Compare synthetic thresholds against a small human-reviewed real-benchmark sample before making
   real-benchmark diagnostic claims.
