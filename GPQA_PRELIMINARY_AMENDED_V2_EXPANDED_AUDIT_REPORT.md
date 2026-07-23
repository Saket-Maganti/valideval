# GPQA Preliminary Amended-v2 Expanded Audit Report

## 1. Executive Summary

In this preliminary amended-v2 local panel, compliant-panel non-full coverage was completed through separate amended answer-only variants. The amended non-full matrices exist for all 8 compliant local Ollama models and 198 GPQA Diamond items.

The expanded go/no-go remains `no_go` for shortcut, prompt-sensitivity, and variant-reliability interpretation because `question_only_answer_only_v2` passed aggregate extraction but one model (`qwen2.5:1.5b-instruct`) was below the 0.95 per-model extraction threshold at 0.944. Sanitized distractor quality was newly allowed and run. This does not establish a general property of GPQA.

## 2. Scope and Labels

Labels: `preliminary`, `amended-v2`, `local-model-only`, `compliant-panel-only`.

This report uses local cached outputs only. It does not use paid APIs, closed-model APIs, smoke outputs, mock outputs, or the previous non-compliant panel. It intentionally omits raw GPQA question text and full answer-choice text.

## 3. Compliant Panel

Panel: `gpqa_minimal_open_local_amended_v2_compliant`.

The panel has 8 real local Ollama models selected under extraction-compliance-only criteria. The excluded original non-compliant models remain excluded and are not mixed into these artifacts.

## 4. Variant Coverage

Original primary non-full variants remain separate and blocked. They had only 4 of 8 compliant models present and were not scored into the compliant-panel cache.

Amended non-full coverage:

| Variant | Raw rows | Scored rows | Matrix | Aggregate extraction | Per-model threshold |
| --- | ---: | ---: | --- | ---: | --- |
| `question_only_answer_only_v2` | 1584 | 1584 | 8x198 | 0.982 | fail |
| `choices_only_answer_only_v2` | 1584 | 1584 | 8x198 | 0.992 | pass |
| `randomized_choices_answer_only_v2` | 1584 | 1584 | 8x198 | 0.994 | pass |
| `answer_letter_only_v2` | 1584 | 1584 | 8x198 | 0.999 | pass |


## 5. Non-Full Prompt Amendment, If Any

A Phase 29 amendment added answer-only non-full variants:

- `question_only` -> `question_only_answer_only_v2`
- `choices_only` -> `choices_only_answer_only_v2`
- `randomized_choices` -> `randomized_choices_answer_only_v2`
- `answer_letter_only` -> `answer_letter_only_v2`

Reason: completed original primary non-full outputs had poor extraction under the frozen extractor. No shortcut, prompt-sensitivity, reliability, or distractor-quality diagnostics were interpreted before this amendment. Original and amended non-full outputs remain separate.

## 6. Go/No-Go Status

Expanded go/no-go status: `no_go`.

Allowed newly under this expanded phase:

- `distractor_quality` in sanitized mode.

Still blocked:

- `shortcut`
- `prompt_sensitivity`
- variant reliability

The blocker is per-model extraction for `question_only_answer_only_v2`: `qwen2.5:1.5b-instruct` reached 0.944, below the 0.95 threshold.

## 7. Newly Unblocked Diagnostics

Only sanitized distractor quality was run. Shortcut, prompt-sensitivity, and reliability across variants were not run as interpreted findings.

## 8. Diagnostics Still Blocked

- Shortcut: blocked by `question_only_answer_only_v2` per-model extraction threshold failure.
- Prompt sensitivity: blocked under the configured four-variant requirement.
- Variant reliability: blocked under the configured four-variant requirement.
- DIF/calibration: still blocked for this preliminary panel and data shape.

## 9. Sanitized Distractor Quality

Sanitized artifact: `results/gpqa_diamond/preliminary_amended_v2/distractor_quality_sanitized.json`.

Summary under this local compliant panel:

- Total distractors: 594
- Dead distractor fraction: 0.288
- Confusing distractor count: 251
- Implausible distractor count: 171
- Mean lexical similarity to correct: 0.438
- Duplicate-choice flags: 10

This suggests possible distractor-review signals under this local panel only. It does not establish a general property of GPQA distractors.

## 10. Shortcut / Prompt Sensitivity Findings

No shortcut or prompt-sensitivity findings are reported. The required amended non-full variant set did not pass all per-model extraction gates.

## 11. Reliability Across Variants

No variant-reliability finding is reported. Although amended matrices exist, the configured full non-full requirement remains blocked by `question_only_answer_only_v2` per-model extraction.

## 12. Materiality Caveats

The question-only amended prompt nearly passed aggregate extraction but failed one per-model threshold. That is enough to block dependent diagnostics under the preregistered extraction-compliance policy. This is an evaluation-protocol extractability result, not a GPQA validity finding.

## 13. Do-Not-Claim List

- Do not claim GPQA is valid or invalid.
- Do not claim GPQA has shortcut behavior from this phase.
- Do not claim prompt sensitivity or variant reliability findings from blocked diagnostics.
- Do not treat sanitized distractor metrics as item-retention decisions.
- Do not generalize local-model-only results to all model classes.
- Do not present these diagnostics as one scalar benchmark-health score.

## 14. Reviewer-Risk Notes

Reviewer risks addressed here include prompt amendment transparency, separation of original and amended outputs, local-panel caveats, blocked-diagnostic disclosure, and sanitized distractor mode. Raw item text and full choice text are intentionally omitted.

## 15. Reproduction Commands

```bash
python3 -m valideval gpqa-go-no-go \
  --benchmark gpqa_diamond \
  --items data/gpqa/gpqa_diamond.jsonl \
  --panel gpqa_minimal_open_local_amended_v2_compliant \
  --config configs/audits/gpqa_diamond_amended_v2.yaml

python3 -m valideval diagnostics distractor-quality \
  --benchmark gpqa_diamond \
  --panel gpqa_minimal_open_local_amended_v2_compliant \
  --local-path data/gpqa/gpqa_diamond.jsonl \
  --config configs/audits/gpqa_diamond_amended_v2.yaml \
  --from-cache \
  --sanitized
```
