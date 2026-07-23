# Cross-Flaw and Held-Out Failure Cases

## 1. Executive Summary

This document records the current cross-flaw and held-out generator failure cases before any further
investigation. It is a no-run inventory: no validation was rerun, no thresholds were tuned, and no
new metrics were created.

Existing artifacts show 7 strong cross-flaw off-target activations and 3 non-paper-eligible held-out
transfer families. These failures are scientifically useful because they identify where controlled
synthetic sensitivity does not yet justify a claim-supporting diagnostic.

## 2. Cross-Flaw Off-Target Activations

| ID | Detector | Intended flaw | Off-target flaw | Activation strength | Existing artifact | Paper eligibility | Notes |
|---|---|---|---|---:|---|---|---|
| CF-01 | `shortcut` | `shortcut_signal` | `too_easy_saturation` | AUC 1.0 | `results/neurips_small_runs/cross_flaw_confusion/cross_flaw_matrix.json` | false | Strongest possible off-target AUC under the current matrix; investigate shared easy-item or shortcut-like structure before using shortcut as claim-supporting evidence in this family. |
| CF-02 | `distractor_quality` | `dead_distractors` | `prompt_format_fragility` | AUC 0.9928385416666666 | `results/neurips_small_runs/cross_flaw_confusion/cross_flaw_matrix.json` | false | Suggests the current distractor-quality detector may respond to artifacts outside dead-distractor structure. |
| CF-03 | `distractor_quality` | `dead_distractors` | `too_easy_saturation` | AUC 0.9694010416666666 | `results/neurips_small_runs/cross_flaw_confusion/cross_flaw_matrix.json` | false | Potential shared latent structure between implausible distractors and saturation/easy-item behavior. |
| CF-04 | `redundancy` | `redundancy` | `shortcut_signal` | AUC 0.9791666666666666 | `results/neurips_small_runs/cross_flaw_confusion/cross_flaw_matrix.json` | false | May reflect generator coupling or a real overlap between repeated patterns and shortcut features. |
| CF-05 | `saturation` | `too_easy_saturation` | `shortcut_signal` | AUC 0.875 | `results/neurips_small_runs/cross_flaw_confusion/cross_flaw_matrix.json` | false | Indicates saturation-style behavior may appear in shortcut synthetic flaws. |
| CF-06 | `saturation` | `too_easy_saturation` | `prompt_format_fragility` | AUC 0.875 | `results/neurips_small_runs/cross_flaw_confusion/cross_flaw_matrix.json` | false | Needs review for whether prompt-format fragility creates item-level saturation-like signatures. |
| CF-07 | `saturation` | `too_easy_saturation` | `extraction_ambiguity` | AUC 0.875 | `results/neurips_small_runs/cross_flaw_confusion/cross_flaw_matrix.json` | false | Needs review for scoring/extraction artifacts that mimic easy-item saturation. |

## 3. Held-Out Transfer Drops

| ID | Diagnostic | Training/known generator | Held-out generator | Drop type | Existing artifact | Paper eligibility | Notes |
|---|---|---|---|---|---|---|---|
| HO-01 | `shortcut` | `paraphrased_shortcut_artifact` / `shortcut_signal` / original AUC 0.9281684027777778 | `keyword_artifact` / held-out AUC 0.5 | AUC drop 0.4281684027777778 to chance-level held-out behavior | `results/neurips_small_runs/heldout_generators/heldout_transfer.json` | false | Strong evidence of generator-detector coupling risk for this shortcut family. |
| HO-02 | `distractor_quality` | `distractor_plausibility_skew` / `dead_distractors` / original AUC 0.7039930555555556 | `answer_length_artifact` / held-out AUC 0.5629340277777778 | AUC drop 0.1410590277777778 with weak held-out AUC | `results/neurips_small_runs/heldout_generators/heldout_transfer.json` | false | Original and held-out AUC are both too weak for paper eligibility under current rules. |
| HO-03 | `redundancy` | `item_cluster_redundancy` / `redundancy` / original AUC 0.9895833333333334 | `context_leakage` / held-out AUC 0.5 | AUC drop 0.48958333333333337 to chance-level held-out behavior | `results/neurips_small_runs/heldout_generators/heldout_transfer.json` | false | Strong evidence that the detector did not transfer to the held-out generator family. |

## 4. What These Failures Mean

- Controlled synthetic sensitivity is not sufficient for diagnostic generalization.
- Some off-target activations may reflect shared latent flaw structure rather than simple detector
  failure.
- Some off-target activations may be false positives caused by generator artifacts, threshold
  leakage, or detector overbreadth.
- Held-out transfer drops indicate generator-detector coupling risk.
- Failure cases should guide downgrade rules, future preregistered analyses, and reviewer-facing
  limitations.

## 5. What They Do Not Mean

- They do not show that ValidEval fails as a framework.
- They do not show that any real benchmark is valid or invalid.
- They do not establish real benchmark error detection.
- They do not validate MMLU-Redux as a diagnostic-success target.
- They do not justify threshold tuning after observing failures.

## 6. Current Claim Status

- Cross-flaw specificity remains `WEAK`.
- Held-out generator transfer remains `WEAK`.
- Controlled synthetic flaw detection remains `SUPPORTED` only for generator-scoped sensitivity.
- Numeric calibration remains `BLOCKED` without confidence/logprob outputs.
- Synthetic-to-real threshold validation remains `NOT_RUN`.
