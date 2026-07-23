# Synthetic Harness Circularity Audit

## 1. Executive Summary

The current controlled synthetic validation harness is circular enough that its AUCs must be demoted. The harness injects hidden flaw labels into item metadata, the controlled model behavior branches on those labels, and the validation runner selects score extraction logic by the same diagnostic/flaw family. This can still test that plumbing, reports, thresholds, and artifact writing are connected, but it does not provide independent diagnostic-validation evidence.

Final evidence posture: current synthetic results are historical wiring/sanity-check artifacts only. Diagnostic-validation evidence remains `RESULT_REQUIRED` pending a decoupled flaw-agnostic harness or stronger external real-panel validation.

## 2. Current Harness Flow

1. `src/valideval/validation/flaw_generators.py` creates clean and flawed synthetic items.
2. Synthetic items receive metadata such as `flaw_type`, `is_flawed`, `flaw_strength`, and `ground_truth_signal`.
3. `src/valideval/validation/synthetic_benchmark.py` renders variants and produces controlled panel outputs.
4. The legacy `_controlled_output` path reads the injected metadata and emits model behavior tailored to the flaw.
5. `src/valideval/validation/validation_runner.py` runs the chosen diagnostic and calls `_extract_item_scores`.
6. `_extract_item_scores` chooses item-level readout statistics conditional on `diagnostic` and sometimes `flaw_type`.
7. Metrics compare these scores back to the injected clean/flawed labels.

## 3. Coupling Points

- Generator labels: `flaw_generators.py` writes `flaw_type`, `is_flawed`, and `ground_truth_signal`.
- Controlled model behavior: `_controlled_output` reads `item.metadata["flaw_type"]` and `item.metadata["is_flawed"]`.
- Flaw-specific branches: the controlled path has direct branches for shortcut, answer-length artifact, prompt-format fragility, low/negative discrimination, saturation/floor, extraction ambiguity, and other flaw types.
- Readout coupling: `_extract_item_scores(..., diagnostic, flaw_type)` changes the statistic by diagnostic family and, for answer-distribution cases, by `flaw_type`.
- Held-out/cross-flaw inheritance: `heldout_generators.py` and cross-flaw validation reuse the same legacy validation runner surface, so they do not remove the core coupling.

## 4. Why This Is Circular

The model-side signal is not generated from only observable item features. It is partly generated from hidden labels that also define the target variable. The readout then measures behavior patterns that were intentionally injected for the corresponding diagnostic/flaw pair. That means high AUC can reflect successful recovery of a hard-coded synthetic signature, not independent evidence that the diagnostic detects a realistic validity threat.

This is a methodological problem even if the code is deterministic, reproducible, and useful for smoke testing. Reproducibility of a circular harness does not make the synthetic AUCs independent validation evidence.

## 5. What Current Synthetic Results Can Still Support

- The validation CLI and report path can run on controlled artifacts.
- The diagnostics can produce item-level scores on synthetic response matrices.
- Report generation, status labels, threshold fields, and artifact schemas are wired together.
- Historical AUCs may remain as legacy sanity-check values if clearly labeled as coupled and non-independent.
- Cross-flaw and held-out outputs can still illustrate specificity/transfer risks within the legacy harness.

## 6. What Current Synthetic Results Cannot Support

- They cannot support an independent diagnostic-validation claim.
- They cannot show that diagnostics recover realistic benchmark flaws.
- They cannot establish real-benchmark detection success.
- They cannot justify threshold transfer to real benchmarks.
- They cannot resolve cross-flaw specificity, held-out transfer, calibration, or materiality.
- They cannot replace MMLU-Redux, HELM panel, or future decoupled-harness evidence.

## 7. Evidence-State Impact

| Evidence surface | Previous use | Revised state |
|---|---|---|
| Controlled synthetic AUCs | Positive synthetic diagnostic validation | `DEMOTED_TO_WIRING_CHECK` |
| Legacy controlled-harness labels | Historical synthetic status labels | Traceability only, not evidence upgrade |
| Cross-flaw synthetic artifacts | Specificity stress test | Legacy context only |
| Held-out generator artifacts | Transfer stress test | Legacy context only |
| Decoupled synthetic validation | Not run | `RESULT_REQUIRED` |
| Real MMLU-Redux validation | External stress test | Weak/negative, no detection-success claim |

## 8. Required Claim Changes

- Say the legacy synthetic harness currently supports wiring/sanity-check behavior only.
- Say current synthetic AUCs are not treated as independent diagnostic-validation evidence.
- Say current synthetic results are demoted pending a decoupled flaw-agnostic harness.
- Keep numerical historical results unchanged, but label them as legacy/sanity-check artifacts.
- Keep diagnostic-validation evidence as `RESULT_REQUIRED`.
- Center the real empirical spine on the 39-model HELM MMLU panel, weak/negative MMLU-Redux external validation, and real-panel claim-gating evidence.

## 9. Replacement Harness Requirements

- Synthetic model behavior must not branch on `is_flawed`.
- Synthetic model behavior must not branch on `flaw_type`.
- Model behavior must depend only on observable item features, public metadata, model configuration, and declared prompt variant.
- Diagnostic readout must be fixed before seeing flaw family.
- No per-flaw hand-picked score extraction.
- Held-out transfer must use generators not mirrored by detector-specific model behavior.
- Thresholds must be preregistered or sensitivity-reported.
- Legacy synthetic outputs must remain labeled `legacy_wiring_only`.

## 10. Final Verdict

SYNTHETIC_EVIDENCE_DEMOTED_TO_WIRING_CHECK
