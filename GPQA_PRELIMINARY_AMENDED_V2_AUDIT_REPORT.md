# GPQA Preliminary Amended-v2 Audit Report

## 1. Executive Summary

This preliminary amended-v2 audit ran on the extraction-compliant local Ollama panel only. It used the amended primary `full_answer_only_v2` matrix and interpreted only diagnostics authorized by the current go/no-go.

Key preliminary signals are proxy item-discrimination warnings, extraction strict-vs-lenient sensitivity, and ranking uncertainty for close local-model comparisons. These signals are conditional on this local panel and do not establish a general property of GPQA.

## 2. What This Audit Is

- A preliminary audit.
- An amended-v2 audit.
- A local-model-only audit.
- A compliant-panel-only audit.
- A first controlled diagnostic interpretation after go/no-go passed.

## 3. What This Audit Is Not

- Not a final paper-grade audit.
- Not a claim that GPQA is valid or invalid.
- Not a result for closed, paid, or frontier models.
- Not an interpretation of shortcut or prompt-sensitivity diagnostics.
- Not a public reproduction of raw GPQA question text.

## 4. Protocol and Amendment Status

The active protocol is `docs/protocols/gpqa_diamond_preregistration_amended_v2.md`. The extraction-compliance decision is recorded in `docs/protocols/gpqa_diamond_amended_v2_extraction_compliance_decision.md`.

The amended primary prompt is `full_answer_only_v2`. The original `full` prompt artifacts remain archived as protocol-development evidence and were not used as the primary matrix in this audit.

## 5. Data and Provenance

- Item file: `data/gpqa/gpqa_diamond.jsonl`
- Items: 198
- Local export validated before output generation and scoring.
- No raw GPQA question text appears in this report.

## 6. Compliant Local Model Panel

Panel: `gpqa_minimal_open_local_amended_v2_compliant`.

The panel has 8 real local Ollama models and excludes prior non-compliant models under extraction-compliance-only criteria. This is a technical I/O validity criterion, not performance filtering.

## 7. Diagnostics Authorized

Authorized diagnostics are listed in `results/gpqa_diamond/preliminary_amended_v2/allowed_diagnostics.json`.

Run in this phase:

- answer_distribution
- irt
- saturation
- extraction_robustness
- redundancy
- ranking_uncertainty
- power
- data_forensics

## 8. Diagnostics Blocked

Blocked as primary interpreted diagnostics:

- shortcut
- prompt_sensitivity
- variant/test-retest reliability
- distractor_quality until sanitized artifact mode exists
- DIF and calibration for this data shape

## 9. Diagnostic Findings

Under this preliminary local-model panel:

- Answer labels are not heavily concentrated by position in this export: max label fraction is 0.278.
- Proxy IRT reports 62 negative-discrimination item flags and near-zero discrimination fraction 0.308. This is a possible review signal, not an item-quality conclusion.
- Saturation diagnostic category is `not saturated` for this local panel, with ceiling proximity 0.298.
- Extraction robustness reports strict-vs-lenient score shift 0.052 and invalid output rate 0.003. This suggests scoring/extraction sensitivity remains worth monitoring even after compliance gating.
- Redundancy diagnostic reports lexical/template redundancy fraction 0.0.
- Ranking uncertainty reports 2 bootstrap rank-instability flags. Close model differences should not be treated as settled.
- Power diagnostic advises not overinterpreting model-score differences within about 8.682 percentage points.
- Data forensics reports no external overlap measurement because no local corpus was supplied; provenance and duplicate signals are local metadata/lexical screens only.

## 10. Materiality Assessment

The strict-vs-lenient extraction shift exceeds the preregistered warning level of 0.03. The near-zero discrimination fraction is just above the configured 0.30 warning level. Negative-discrimination flags exist and should become a private expert-review queue before any item-level action.

The saturation diagnostic did not produce a saturation warning for this local panel. That does not settle saturation for stronger or different model panels.

## 11. Ranking and Model-Panel Caveats

This is not a final ranking. The model panel is small, local, and selected for extraction compliance before interpretation. Ranking uncertainty and power diagnostics both warn against treating close model gaps as stable.

## 12. Item-Level Caveats

Item IDs can be used for private review, but this report does not reproduce GPQA item text. Item-level proxy flags are screening signals and require human validation before any claim about an item.

## 13. Comparison to Go/No-Go Criteria

The compliant panel passed amended go/no-go before interpretation:

- Valid item file.
- Complete amended primary matrix.
- 8 models.
- Extraction success above 0.95.
- Frozen extractor recorded.

## 14. What Can Be Said

- In this preliminary local-model panel, several full-path diagnostics produced review-worthy signals.
- Under the amended-v2 answer-only protocol, extraction compliance was sufficient for this compliant panel.
- Proxy item-discrimination and extraction-sensitivity findings merit follow-up.
- Close local-model ranking differences should be treated cautiously.

## 15. What Cannot Be Said

- GPQA is valid or invalid.
- GPQA has proven shortcuts, contamination, saturation, or bad items.
- These findings generalize to all model classes.
- Original full-prompt artifacts are primary amended-v2 results.
- Non-compliant model outputs can be mixed into the compliant-panel audit.

## 16. Reviewer-Risk Notes

Reviewer risks addressed here include hidden prompt amendment, threshold lowering, model-exclusion transparency, local-panel overgeneralization, missing human validation, missing external contamination scan, and blocked prompt-variant diagnostics.

The report intentionally includes negative result / missing diagnostics disclosures. Baseline and dumb baseline diagnostics were not run in this phase.

## 17. Next Required Runs

- Complete non-full variants for the compliant 8-model panel before shortcut and prompt-sensitivity diagnostics.
- Add sanitized distractor-quality output mode before distractor interpretation.
- Run human validation / expert review for item-level flags.
- Replicate with a broader open local panel before publication-grade interpretation.

## 18. Reproduction Commands

```bash
python3 -m valideval gpqa-go-no-go \
  --benchmark gpqa_diamond \
  --items data/gpqa/gpqa_diamond.jsonl \
  --panel gpqa_minimal_open_local_amended_v2_compliant \
  --config configs/audits/gpqa_diamond_amended_v2.yaml

python3 -m valideval audit \
  --benchmark gpqa_diamond \
  --panel gpqa_minimal_open_local_amended_v2_compliant \
  --local-path data/gpqa/gpqa_diamond.jsonl \
  --config configs/audits/gpqa_diamond_amended_v2.yaml \
  --from-cache \
  --input-validated-only \
  --diagnostics answer_distribution irt saturation extraction_robustness redundancy ranking_uncertainty power data_forensics
```
