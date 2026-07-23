# GPQA Extraction and Panel Expansion Report

This report intentionally omits raw GPQA question text and raw model output text.

## 1. Executive Summary

Phase 23 handled the extraction bottleneck first, then expanded the preliminary local Ollama panel.

- Official GPQA Diamond input remains validated locally with 198 items.
- The GPQA extraction parser received a documented `scoring_parser_bugfix` for clear final-answer patterns.
- Original scored predictions were backed up before re-scoring.
- A secondary `full_answer_only_v2` prompt-compliance probe was created and tested separately from preregistered primary matrices.
- `gpqa_minimal_open_local` was expanded from 3 to 5 real local Ollama models.
- Full-prompt outputs now exist for all 5 models; the other preregistered variants remain complete for the original 3 models.
- All five primary matrices were rebuilt.
- Go/no-go remains `no_go`.
- No diagnostics were run or interpreted.

## 2. Starting State

- Item file: `data/gpqa/gpqa_diamond.jsonl`
- Item count: 198
- Starting preliminary models: `qwen2.5:1.5b-instruct`, `qwen2.5:3b-instruct`, `llama3.2:1b`
- Starting primary variants: `full`, `question_only`, `choices_only`, `randomized_choices`, `answer_letter_only`
- Starting blockers: model count below 8 and extraction success below 0.95.

## 3. Extraction Failure Pattern Analysis

Metadata-only failure analysis was refreshed at:

- `results/gpqa_diamond/input_validation/extraction_failure_patterns.md`
- `results/gpqa_diamond/input_validation/extraction_failure_patterns.json`

Current primary extraction summary:

| Variant | Outputs | Usable extraction success | Invalid/unusable | Ambiguous | Passes 0.95 |
| --- | ---: | ---: | ---: | ---: | --- |
| `full` | 990 | 0.746 | 251 | 40 | false |
| `question_only` | 594 | 0.630 | 220 | 8 | false |
| `choices_only` | 594 | 0.722 | 165 | 3 | false |
| `randomized_choices` | 594 | 0.672 | 195 | 7 | false |
| `answer_letter_only` | 594 | 0.823 | 105 | 3 | false |

Failure categories are reported by model, variant, and item ID only. The dominant pattern remains model or prompt answer-format non-compliance, with some parser limitation addressed by the bugfix.

## 4. Extractor Decision

A parser bugfix was justified because some outputs contained clear final-answer patterns that the prior extractor did not reliably recover.

The extractor was not loosened to accept genuinely invalid or ambiguous responses. Outputs with multiple conflicting answer letters and no clear final-answer rule remain ambiguous or invalid.

## 5. Extractor Changes, If Any

Change classification: `scoring_parser_bugfix`.

Updated files:

- `src/valideval/scoring/extraction.py`
- `src/valideval/benchmarks/gpqa_inputs.py`
- `tests/test_gpqa_scoring.py`

Patterns now covered include clear forms such as `Answer: C`, `Final answer: C`, `The correct option is C`, `I choose option C`, JSON-like answer fields, and a final isolated option letter. Negative ambiguous cases remain rejected.

Original scored predictions were backed up under:

```text
cache/gpqa_diamond/gpqa_minimal_open_local/backups/pre_parser_bugfix_20260604T084935Z
```

The parser comparison is recorded at:

- `results/gpqa_diamond/input_validation/parser_bugfix_comparison.md`
- `results/gpqa_diamond/input_validation/parser_bugfix_comparison.json`

## 6. Prompt-Compliance Variant, If Any

A secondary exploratory prompt was added:

```text
configs/prompts/gpqa/full_answer_only_v2.yaml
```

Deviation documentation:

```text
docs/protocols/gpqa_diamond_preregistration_deviations.md
```

This is not part of the preregistered primary matrix path. It is an extraction-compliance probe only. A 10-item real Ollama probe for `qwen2.5:1.5b-instruct` completed with no extraction failures, but it must not be mixed into primary matrices without a later preregistration amendment or explicit secondary analysis plan.

## 7. Models Before / After

Before Phase 23:

- `qwen2.5:1.5b-instruct`
- `qwen2.5:3b-instruct`
- `llama3.2:1b`

After Phase 23:

- `qwen2.5:1.5b-instruct`
- `qwen2.5:3b-instruct`
- `llama3.2:1b`
- `llama3.2:3b`
- `gemma2:2b`

The panel remains preliminary/local workflow validation only. It is not paper-grade and does not replace `gpqa_open_local`.

## 8. Output Generation Status

New full-prompt real local outputs generated:

- `local_outputs/gpqa/full/llama3.2_3b.jsonl`: 198 rows
- `local_outputs/gpqa/full/gemma2_2b.jsonl`: 198 rows

Existing full outputs for the first three models were resumed and skipped without regeneration.

Non-full variants remain complete for the original three models only. The two newly added models do not yet have `question_only`, `choices_only`, `randomized_choices`, or `answer_letter_only` raw outputs.

## 9. Scoring Status

New full-prompt scored prediction files:

- `cache/gpqa_diamond/gpqa_minimal_open_local/llama3.2_3b_full_predictions.jsonl`
- `cache/gpqa_diamond/gpqa_minimal_open_local/gemma2_2b_full_predictions.jsonl`

Aggregate prediction files were rebuilt from real per-model predictions only. Smoke/mock files remain excluded.

| Variant | Aggregate rows | Models included |
| --- | ---: | ---: |
| `full` | 990 | 5 |
| `question_only` | 594 | 3 |
| `choices_only` | 594 | 3 |
| `randomized_choices` | 594 | 3 |
| `answer_letter_only` | 594 | 3 |

## 10. Extraction Audit Results

Combined extraction summary:

- `results/gpqa_diamond/input_validation/extraction_audit_summary.md`
- `results/gpqa_diamond/input_validation/extraction_audit_summary.json`

The full-prompt primary extraction success after adding two models is 0.746, below the preregistered 0.95 threshold. Extraction remains a go/no-go blocker.

## 11. Alignment Results

Alignment summary:

- `results/gpqa_diamond/input_validation/alignment_summary.md`
- `results/gpqa_diamond/input_validation/alignment_summary.json`

Alignment passed for included real models:

| Variant | Models | Rows | Complete for included models | Missing configured model outputs |
| --- | ---: | ---: | --- | --- |
| `full` | 5 | 990 | true | none |
| `question_only` | 3 | 594 | true | `llama3.2:3b`, `gemma2:2b` |
| `choices_only` | 3 | 594 | true | `llama3.2:3b`, `gemma2:2b` |
| `randomized_choices` | 3 | 594 | true | `llama3.2:3b`, `gemma2:2b` |
| `answer_letter_only` | 3 | 594 | true | `llama3.2:3b`, `gemma2:2b` |

## 12. Matrix Status

All primary matrices were rebuilt:

- `cache/gpqa_diamond/gpqa_minimal_open_local/matrix_full.csv`: 5 models
- `cache/gpqa_diamond/gpqa_minimal_open_local/matrix_question_only.csv`: 3 models
- `cache/gpqa_diamond/gpqa_minimal_open_local/matrix_choices_only.csv`: 3 models
- `cache/gpqa_diamond/gpqa_minimal_open_local/matrix_randomized_choices.csv`: 3 models
- `cache/gpqa_diamond/gpqa_minimal_open_local/matrix_answer_letter_only.csv`: 3 models

## 13. Prompt Variant Completeness

`validate-prompt-variants` status: `pass`.

All five primary aggregate prediction files and matrices exist. This does not mean every configured model has every non-full variant; those missing model/variant outputs are documented in the alignment summary.

## 14. Manifest Status

Audit manifest refreshed:

```text
results/gpqa_diamond/input_validation/audit_manifest.json
```

The manifest includes item, raw output, per-model prediction, aggregate prediction, matrix, config, prompt-template, preregistration, and code hashes. No diagnostics were interpreted.

## 15. Go/No-Go Result

Current status: `no_go`.

Blocked checks:

- `required_model_count_met`: 5 available models versus 8 required.
- `extraction_success_threshold_met`: full-prompt extraction success 0.746 versus threshold 0.95.

Passing checks include item validation, fixture exclusion, frozen prompt templates, preregistration presence, panel config presence, required prompt-variant aggregate presence, complete full matrix, and scoring-rule tracking.

## 16. Dry-Run-Real Result

Dry-run-real was not run because go/no-go returned `no_go`.

## 17. Diagnostics Allowed Later

No diagnostic interpretation is allowed from this phase. If a later phase explicitly scopes a preliminary workflow-only audit shell, it must still avoid GPQA validity claims unless go/no-go and preregistered conditions are satisfied or formally amended.

## 18. Diagnostics Blocked

- Preregistered real diagnostic interpretation is blocked by go/no-go.
- IRT/proxy psychometrics remain blocked by 5 models versus the 8-model threshold.
- Extraction robustness remains blocked by primary full-prompt extraction success below 0.95.
- Complete five-model prompt-variant comparisons remain blocked until the two added models have non-full variant outputs.
- Paper-grade `gpqa_open_local` remains blocked until real outputs are configured or imported for that panel.

## 19. Deviations From Pre-Registration

- `scoring_parser_bugfix`: final-answer extraction bugfix documented and tested.
- `secondary_exploratory_extraction_compliance`: `full_answer_only_v2` prompt-compliance probe added and kept separate from primary matrices.
- Panel expansion: `gpqa_minimal_open_local` expanded from 3 to 5 real local Ollama models for preliminary workflow validation only.
- No primary preregistered prompt template was silently replaced.
- No diagnostic interpretation was run.

## 20. Do-Not-Claim List

- Do not claim any GPQA validity finding.
- Do not claim shortcut, contamination, saturation, bad-item, or model-ranking evidence.
- Do not treat `gpqa_minimal_open_local` as paper-grade.
- Do not mix `full_answer_only_v2` with primary preregistered matrices.
- Do not mix smoke/mock files with real local outputs.
- Do not interpret diagnostics while go/no-go is `no_go`.

## 21. Next Commands

To complete non-full variants for the two added models, rerun the existing resume-safe generation commands:

```bash
python3 -m valideval generate-outputs --benchmark gpqa_diamond --items data/gpqa/gpqa_diamond.jsonl --panel gpqa_minimal_open_local --prompt-variant randomized_choices --output-dir local_outputs/gpqa/randomized_choices
python3 -m valideval generate-outputs --benchmark gpqa_diamond --items data/gpqa/gpqa_diamond.jsonl --panel gpqa_minimal_open_local --prompt-variant question_only --output-dir local_outputs/gpqa/question_only
python3 -m valideval generate-outputs --benchmark gpqa_diamond --items data/gpqa/gpqa_diamond.jsonl --panel gpqa_minimal_open_local --prompt-variant choices_only --output-dir local_outputs/gpqa/choices_only
python3 -m valideval generate-outputs --benchmark gpqa_diamond --items data/gpqa/gpqa_diamond.jsonl --panel gpqa_minimal_open_local --prompt-variant answer_letter_only --output-dir local_outputs/gpqa/answer_letter_only
```

To address the model-count blocker:

```bash
ollama pull phi3.5:3.8b
ollama pull qwen2.5:7b-instruct
ollama pull mistral:7b
```

Only add models that are actually available locally, then regenerate/score/rebuild matrices and rerun go/no-go.

## Phase 24 Update

`gpqa_minimal_open_local` now has eight configured local Ollama models. Full-prompt raw outputs, scored predictions, and `matrix_full.csv` are complete for all eight models.

Primary non-full variants are complete for five models. The three newly added medium models are missing non-full variants because local generation was measured as too slow for this phase.

Current primary full extraction success is 0.721, below the 0.95 threshold, so go/no-go remains **no_go**. The separate exploratory `full_answer_only_v2` path has 5-model coverage and extraction success 0.980, but it is not a preregistered primary prompt and must not be mixed into primary matrices.

## Phase 25 Update

`full_answer_only_v2` has been formally adopted under an amended preregistration and rerun across all 8 models in `gpqa_minimal_open_local`.

Amended v2 status:

- Raw outputs: 8 models x 198 rows.
- Aggregate predictions: 1584 rows.
- Matrix: `cache/gpqa_diamond/gpqa_minimal_open_local/matrix_full_answer_only_v2.csv`.
- Alignment: pass.
- Extraction success: 0.941 versus threshold 0.95.
- Amended go/no-go: **no_go**.

No diagnostics were interpreted. Original `full` artifacts remain separate.
