# Decoupled Synthetic Baselines Plan

This plan defines future baselines for an approved decoupled synthetic harness run. It performs no computation and creates no evidence.

## 1. Random Diagnostic Baseline

Randomly rank items independent of prompt text, subject, choices, and outputs. This tests whether the proposed readout beats chance under the same evaluation universe. Future claim upgrades require performance above this baseline.

## 2. Majority / Difficulty Baseline

Rank items using only aggregate correctness or difficulty proxies. This tests whether the diagnostic is merely rediscovering easy/hard item structure rather than the intended validity threat.

## 3. Prompt-Length Baseline

Rank items by prompt length or token-count proxy. This tests whether the readout is confounded by surface verbosity rather than construct-relevant behavior.

## 4. Choice-Length Baseline

Rank items by answer-choice length features, including maximum/minimum choice length and correct-choice length if the future protocol permits answer-aware baselines. This tests answer-length artifacts and surface-form confounding.

## 5. Subject-Only Baseline

Rank items by subject or subject-level aggregate rates. This tests whether diagnostic signals are dominated by domain composition or subject difficulty.

## 6. Naive Disagreement Baseline

Rank items by simple model disagreement without diagnostic-specific features. This tests whether the proposed readout adds anything beyond generic panel instability.

## 7. Legacy Wiring-Only Baseline as Negative Control

Run only as a labeled negative-control comparison in a future approved protocol, never as primary evidence. The legacy wiring-only harness should not be allowed to upgrade claims. Its role is to show how a coupled harness can produce separability that must be rejected as independent evidence.

## 8. Ablation Without Hidden Labels

Run the same model/readout with hidden-label metadata stripped and with public metadata minimized. This tests whether any apparent signal depends on metadata leakage. If performance collapses only when hidden labels are removed, the protocol is blocked.

## 9. Held-Out Generator Baseline

Evaluate transfer to held-out generator families not mirrored by detector-specific behavior. This tests whether findings are generator-specific. A future diagnostic claim requires held-out performance and transfer-drop reporting under preregistered gates.

## 10. Reporting Rule

Every future result table must report the primary readout next to the random, surface-form, subject-only, naive-disagreement, and held-out baselines. Missing baseline artifacts keep claim status at `RESULT_REQUIRED`.
