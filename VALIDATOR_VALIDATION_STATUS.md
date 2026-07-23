# Validator Validation Status

Generated: 2026-06-03

This document summarizes Phase 12 synthetic detector validation. It does not contain real benchmark findings.

## 1. What Was Built

ValidEval now includes a synthetic Diagnostic Validation Harness under `src/valideval/validation/`.

The harness can:

- generate controlled MCQ benchmarks with ground-truth flaw metadata
- sweep flaw strength from `0.0` to `1.0`
- run existing ValidEval diagnostics on synthetic cached predictions and response matrices
- compute ROC AUC, PR AUC, sensitivity, specificity, false-positive rate, monotonicity, score-strength correlation, calibration curves, and null distributions
- apply multiplicity correction with Benjamini-Hochberg, Benjamini-Yekutieli, Bonferroni, and Holm
- estimate expected false flags under null synthetic benchmarks
- classify materiality separately from detectability
- render JSON and Markdown validation reports

## 2. Injectable Flaws

Implemented synthetic flaws:

- clean
- shortcut_signal
- label_imbalance
- answer_length_artifact
- keyword_artifact
- dead_distractors
- redundancy
- low_discrimination
- negative_discrimination
- too_easy_saturation
- too_hard_floor
- scoring_ambiguity
- prompt_format_fragility
- extraction_ambiguity
- context_irrelevance
- context_leakage

## 3. Diagnostics Validated

Current full-suite command:

```bash
python3 -m valideval validate-diagnostics --config configs/validation/all_sweeps.yaml
```

Summary report:

- `validation_reports/diagnostic_validation_summary.md`
- `validation_reports/diagnostic_validation_summary.json`

| Diagnostic | Synthetic Flaw | Status | ROC AUC | PR AUC | Clean FPR | Monotonicity |
|---|---|---|---:|---:|---:|---:|
| shortcut | shortcut_signal | credible_under_synthetic_harness | 0.917 | 0.889 | 0.014 | 1.000 |
| answer_distribution | label_imbalance | prototype_only | 0.966 | 0.961 | 0.207 | 1.000 |
| answer_distribution | answer_length_artifact | credible_under_synthetic_harness | 1.000 | 1.000 | 0.000 | 1.000 |
| distractor_quality | dead_distractors | prototype_only | 0.739 | 0.696 | 0.007 | 0.900 |
| redundancy | redundancy | credible_under_synthetic_harness | 0.991 | 0.993 | 0.000 | 1.000 |
| irt | low_discrimination | credible_under_synthetic_harness | 0.999 | 0.998 | 0.066 | 1.000 |
| irt | negative_discrimination | credible_under_synthetic_harness | 0.909 | 0.872 | 0.023 | 0.900 |
| reliability | prompt_format_fragility | credible_under_synthetic_harness | 1.000 | 1.000 | 0.050 | 1.000 |
| extraction_robustness | extraction_ambiguity | credible_under_synthetic_harness | 1.000 | 1.000 | 0.000 | 1.000 |
| extraction_robustness | scoring_ambiguity | credible_under_synthetic_harness | 1.000 | 1.000 | 0.000 | 1.000 |
| saturation | too_easy_saturation | credible_under_synthetic_harness | 0.894 | 0.772 | 0.000 | 1.000 |
| saturation | too_hard_floor | credible_under_synthetic_harness | 0.989 | 0.978 | 0.045 | 1.000 |

## 4. False-Positive Rates

Clean/null false-positive rates are estimated from strength `0.0` synthetic runs. The label-imbalance detector has a high clean false-positive rate under the current threshold (`0.207`) and is therefore prototype-only despite high AUC.

## 5. Recommended Thresholds

Per-diagnostic threshold recommendations are in each experiment JSON file under `threshold_recommendation`. These thresholds are synthetic-generator thresholds only. They should not be transferred directly to real benchmark audits.

## 6. Diagnostics Still Unvalidated Or Quarantined

Quarantined under this harness:

- None.

Prototype-only:

- `answer_distribution / label_imbalance`: high AUC but high clean false-positive rate.
- `distractor_quality / dead_distractors`: moderate separability, not strong enough to treat as calibrated.

Previously quarantined:

- `irt / negative_discrimination` is now credible under the revised synthetic harness. The root cause was that the old generator could make anti-correlated items dominate the response matrix, flipping the total-score ability proxy and causing clean anchor items to be flagged instead of the known flawed items. The revised generator keeps clean anchor items available, uses an ordered synthetic IRT validation panel, and reports anchor-oriented proxy discrimination while retaining corrected item-total correlation as a field.

Important caveat: this does not prove that negative-discrimination detection is universally calibrated. Under this protocol, a response matrix with few or no clean anchor items remains hard to orient without external evidence about model ability.

## 7. Features Quarantined Or Reframed

- Certificate wording is reframed as an evidence profile / audit completeness profile. It explicitly says it is not a validity score or quality grade.
- Numeric calibration output is disabled unless real confidence/logprob values exist. Prompt consistency is reported only as a stability proxy.
- Ranking language is softened to diagnostic-sensitive sensitivity analysis views, not corrected or true leaderboards.

## 8. Ready For First Real Benchmark Audit?

Not yet for all diagnostics. A first real benchmark smoke audit is reasonable only if the report explicitly separates calibrated synthetic detector evidence from exploratory diagnostics.

Best next benchmark target: GSM8K-style or small MCQ subset with local cached outputs, because scoring is relatively simple and shortcut/answer-artifact/extraction diagnostics are now better constrained than the broad leaderboard/certificate stack.

## 9. Single Most Important Next Step

Run a small cached benchmark smoke audit and compare flagged shortcut, scoring, and low/negative-discrimination items against human review before making stronger real-benchmark claims.
