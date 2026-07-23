# GPQA Diamond Preregistration — Amended v2

Artifact class: **real GPQA amended protocol setup**.

This amendment contains no GPQA diagnostic interpretation and no raw GPQA item text.

## 1. Amendment Summary

The GPQA Diamond audit protocol is amended to adopt `full_answer_only_v2` as the primary full-prompt extraction-compliance path. The original `full` prompt artifacts are retained as protocol-development evidence and are not deleted, renamed, or mixed with amended v2 artifacts.

## 2. Original Protocol

The original pre-registration used `full` as the primary full prompt and froze five prompt variants: `full`, `question_only`, `choices_only`, `randomized_choices`, and `answer_letter_only`. The primary extractor counted invalid and ambiguous model outputs rather than coercing them.

## 3. Reason for Amendment

The original primary prompt failed the preflight extraction threshold. This was treated as an evaluation-protocol extractability problem, not as a GPQA validity finding. The answer-only v2 prompt was tested separately as an exploratory extraction-compliance path before any diagnostic interpretation.

## 4. Evidence Used Before Amendment

Pre-amendment evidence was limited to input-validation artifacts: output coverage, extraction success, alignment, and matrix readiness. The exploratory v2 path crossed the extraction threshold, while the original `full` path remained below threshold.

## 5. What Was Not Interpreted Before Amendment

No diagnostic outputs were interpreted before this amendment. No claims were made about GPQA shortcut sensitivity, contamination, item quality, saturation, construct validity, model ranking, or benchmark health.

## 6. Amended Primary Prompt

The amended primary full-prompt path is:

```text
configs/prompts/gpqa/full_answer_only_v2.yaml
```

This prompt requires the model to return exactly one answer letter. It is adopted to improve output extractability under the frozen extractor, not to change GPQA items, answer labels, or scoring rules.

## 7. Prompt Hashes

- Original `full` prompt hash: `85881fb857347db5da8cbe1091040e6914b95939060fc331f2c84970992006a2`
- Amended `full_answer_only_v2` prompt hash: `40d98d99b74b47ebbc95bad1bc88ab7e4278ba9f0f06b34ce1e12965dcd7707f`

## 8. Scoring / Extraction Rules

The frozen GPQA extraction/scoring rules remain in effect. No answer labels are changed. Outputs without a recoverable final answer remain invalid, and conflicting answer letters remain ambiguous unless a robust final-answer cue applies.

## 9. Model Panel

The amended preflight uses `configs/panels/gpqa_minimal_open_local.yaml`. This is a preliminary local/open Ollama panel and is not described as paper-grade evidence.

## 10. Prompt Variants

The amended primary full path is `full_answer_only_v2`. The original `full` variant is archived for protocol-development transparency. Non-full variants remain separate and may be used later only when their coverage and extraction status meet the applicable preflight requirements.

Phase 29 adds amended answer-only non-full variants because the original non-full outputs did not consistently meet the frozen extraction threshold on completed compliant-panel outputs. These variants preserve the intended ablations while enforcing the same answer-only output contract as the amended full path:

- `question_only` -> `question_only_answer_only_v2`
- `choices_only` -> `choices_only_answer_only_v2`
- `randomized_choices` -> `randomized_choices_answer_only_v2`
- `answer_letter_only` -> `answer_letter_only_v2`

Original non-full outputs remain separate protocol-development artifacts. They are not mixed with amended non-full aggregates or matrices.

## 11. Diagnostics Allowed Under Amended Protocol

After amended go/no-go passes, later dry-run or audit phases may schedule only diagnostics supported by complete amended artifacts. This document does not authorize interpretation by itself.

## 12. Diagnostics Blocked Under Amended Protocol

Shortcut and prompt-sensitivity diagnostics remain blocked unless non-full variant coverage is complete at the required model count and passes input-validation checks. Any partial non-full analysis must be labeled preliminary.

## 13. Materiality Thresholds

The amended primary path keeps the extraction success threshold at `0.95` and the model-count threshold at `8` for the amended full matrix.

## 14. Multiplicity Correction

The original Benjamini-Hochberg item-level flag correction plan at `q = 0.10` remains unchanged for later diagnostic phases.

## 15. Go/No-Go Criteria

Amended go/no-go requires a valid GPQA Diamond item file, the amended preregistration file, the amended audit config, a complete `full_answer_only_v2` matrix with at least 8 models, and extraction success at or above `0.95` for the amended primary path.

## 16. Deviations Log

The v2 prompt was introduced as exploratory in `docs/protocols/gpqa_diamond_preregistration_deviations.md` and is adopted here only after formal amendment. Original artifacts remain available for provenance.

## 17. Do-Not-Claim List

- Do not claim the original extraction failure is a GPQA validity result.
- Do not claim v2 results are benchmark diagnostics.
- Do not claim GPQA has shortcuts, contamination, bad items, saturation, or any validity issue from input-validation artifacts.
- Do not report model rankings or benchmark health from this amendment.

## 18. Reproduction Commands

```bash
python3 -m valideval generate-outputs --benchmark gpqa_diamond --items data/gpqa/gpqa_diamond.jsonl --panel gpqa_minimal_open_local --prompt-variant full_answer_only_v2 --output-dir local_outputs/gpqa/full_answer_only_v2
python3 -m valideval matrix-from-predictions --benchmark gpqa_diamond --panel gpqa_minimal_open_local --variant full_answer_only_v2
python3 -m valideval audit-manifest --benchmark gpqa_diamond --items data/gpqa/gpqa_diamond.jsonl --panel gpqa_minimal_open_local --config configs/audits/gpqa_diamond_amended_v2.yaml
python3 -m valideval gpqa-go-no-go --benchmark gpqa_diamond --items data/gpqa/gpqa_diamond.jsonl --panel gpqa_minimal_open_local --config configs/audits/gpqa_diamond_amended_v2.yaml
```

## Phase 28 Status Addendum

A first preliminary amended-v2 audit was run after the compliant panel passed go/no-go. The audit was explicitly labeled `preliminary`, `amended-v2`, `local-model-only`, and `compliant-panel-only`.

Diagnostics run under this addendum:

- `answer_distribution`
- `irt`
- `saturation`
- `extraction_robustness`
- `redundancy`
- `ranking_uncertainty`
- `power`
- `data_forensics`

Diagnostics still blocked for primary interpretation:

- `shortcut`
- `prompt_sensitivity`
- variant/test-retest reliability
- `distractor_quality` until sanitized output mode exists
- diagnostics requiring non-full 8-model prompt coverage

This addendum does not authorize broad GPQA validity claims or paper-grade conclusions.

## Phase 29 Status Addendum

The amended non-full prompt variants are authorized only for preliminary amended-v2, local-model-only, compliant-panel-only diagnostics after they pass coverage, alignment, and extraction checks. Shortcut, prompt-sensitivity, and variant-reliability diagnostics remain blocked until those checks pass for the required amended non-full variants.

Sanitized distractor-quality artifacts are required before any distractor-quality interpretation. Public Markdown must not include raw GPQA question text or full answer-choice text.
