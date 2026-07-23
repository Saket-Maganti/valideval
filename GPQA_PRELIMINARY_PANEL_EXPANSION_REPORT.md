# GPQA Preliminary Panel Expansion Report

This report intentionally omits raw GPQA question text and raw model output text.

## 1. Executive Summary

- Official GPQA Diamond input remains acquired and validated locally with 198 items.
- The preliminary local Ollama panel was expanded to three real local/open models.
- All five preregistered prompt variants now have real preliminary raw outputs, scored predictions, aggregate prediction files, and matrices.
- Current go/no-go status: `no_go`.
- No diagnostic interpretation was run and no benchmark-validity claims are made.

## 2. Models Available

- `qwen2.5:1.5b-instruct`: runner `ollama`, availability `available_cached_outputs`, cached variants `full, question_only, choices_only, randomized_choices, answer_letter_only`.
- `qwen2.5:3b-instruct`: runner `ollama`, availability `available_cached_outputs`, cached variants `full, question_only, choices_only, randomized_choices, answer_letter_only`.
- `llama3.2:1b`: runner `ollama`, availability `available_cached_outputs`, cached variants `full, question_only, choices_only, randomized_choices, answer_letter_only`.

## 3. Models Added / Failed

- Added for Phase 22 preliminary generation: `qwen2.5:3b-instruct` and `llama3.2:1b`.
- Preserved existing model: `qwen2.5:1.5b-instruct`.
- Model pull/generation failures: none recorded in this phase.
- This remains a preliminary/local workflow-validation panel, not a paper-grade panel.

## 4. Prompt Variants Generated

- `full`: 3 real model files, row counts [198].
- `question_only`: 3 real model files, row counts [198].
- `choices_only`: 3 real model files, row counts [198].
- `randomized_choices`: 3 real model files, row counts [198].
- `answer_letter_only`: 3 real model files, row counts [198].

## 5. Output Generation Status

- Real preliminary raw output files: 15.
- Smoke/mock files explicitly excluded: 2.
- Full-prompt generation resumed/skipped the existing qwen 1.5B file and generated full outputs for the two added models.
- No raw output text is included in this report.

## 6. Extraction Failure Pattern Summary

| Variant | Status | Outputs | Usable extraction success | Invalid | Ambiguous |
| --- | --- | ---: | ---: | ---: | ---: |
| `full` | `blocked` | 594 | 0.678 | 191 | 25 |
| `question_only` | `blocked` | 594 | 0.707 | 174 | 8 |
| `choices_only` | `blocked` | 594 | 0.806 | 115 | 3 |
| `randomized_choices` | `blocked` | 594 | 0.684 | 188 | 9 |
| `answer_letter_only` | `blocked` | 594 | 0.828 | 102 | 7 |

- Full-prompt extraction remains below the preregistered threshold; this blocks go/no-go.
- Failure-pattern reports contain item IDs and pattern categories only.

## 7. Scoring Status

- `full`: three per-model prediction files plus aggregate `cache/gpqa_diamond/gpqa_minimal_open_local/predictions_full.jsonl` with 594 rows.
- `question_only`: three per-model prediction files plus aggregate `cache/gpqa_diamond/gpqa_minimal_open_local/predictions_question_only.jsonl` with 594 rows.
- `choices_only`: three per-model prediction files plus aggregate `cache/gpqa_diamond/gpqa_minimal_open_local/predictions_choices_only.jsonl` with 594 rows.
- `randomized_choices`: three per-model prediction files plus aggregate `cache/gpqa_diamond/gpqa_minimal_open_local/predictions_randomized_choices.jsonl` with 594 rows.
- `answer_letter_only`: three per-model prediction files plus aggregate `cache/gpqa_diamond/gpqa_minimal_open_local/predictions_answer_letter_only.jsonl` with 594 rows.

## 8. Alignment Status

| Variant | Status | Predictions | Models | Matrix complete | Extraction failures recorded |
| --- | --- | ---: | ---: | --- | ---: |
| `full` | `pass` | 594 | 3 | True | 153 |
| `question_only` | `pass` | 594 | 3 | True | 143 |
| `choices_only` | `pass` | 594 | 3 | True | 94 |
| `randomized_choices` | `pass` | 594 | 3 | True | 153 |
| `answer_letter_only` | `pass` | 594 | 3 | True | 101 |

- Alignment was checked with `min_models=3` for this preliminary panel; the preregistered go/no-go still requires the configured higher model threshold.

## 9. Matrix Status

- `full`: `cache/gpqa_diamond/gpqa_minimal_open_local/matrix_full.csv` exists: True, metadata exists: True.
- `question_only`: `cache/gpqa_diamond/gpqa_minimal_open_local/matrix_question_only.csv` exists: True, metadata exists: True.
- `choices_only`: `cache/gpqa_diamond/gpqa_minimal_open_local/matrix_choices_only.csv` exists: True, metadata exists: True.
- `randomized_choices`: `cache/gpqa_diamond/gpqa_minimal_open_local/matrix_randomized_choices.csv` exists: True, metadata exists: True.
- `answer_letter_only`: `cache/gpqa_diamond/gpqa_minimal_open_local/matrix_answer_letter_only.csv` exists: True, metadata exists: True.

## 10. Prompt Variant Completeness

- Status: `pass`.
- Present prediction variants: answer_letter_only, choices_only, full, question_only, randomized_choices.
- Present matrix variants: answer_letter_only, choices_only, full, question_only, randomized_choices.

## 11. Manifest Status

- Audit manifest refreshed at `results/gpqa_diamond/input_validation/audit_manifest.json`.
- Item file hash: `bd6f79c7b1b460564ae6bcec2afb86756b0071c809b042bc7613cb1896f8e88c`.
- Manifest includes hashes for raw output files, per-model predictions, aggregate predictions, matrices, configs, prompt templates, and the frozen extractor version.

## 12. Go/No-Go Result

- Status: `no_go`.
- Blocked checks:
  - `required_model_count_met` with evidence `{'min_models': 8, 'model_count': 3}`.
  - `extraction_success_threshold_met` with evidence `{'success_rate': 0.6784511784511784, 'threshold': 0.95}`.

## 13. Dry-Run-Real Result

- Not run in Phase 22 because go/no-go returned `no_go`.

## 14. Diagnostics Allowed Later

- Diagnostic interpretation is not allowed in this phase.
- After input blockers are resolved and go/no-go passes, cached matrices are available for scheduling under the preregistered audit shell.

## 15. Diagnostics Blocked

- Real diagnostic interpretation remains blocked by go/no-go.
- IRT/proxy psychometrics remain blocked/limited by three-model panel size versus the configured eight-model threshold.
- Extraction robustness gate remains blocked by full-prompt extraction success below threshold.

## 16. Deviations From Pre-Registration

- Prompt templates: no changes in this phase.
- Scoring/extraction rules: no changes in this phase.
- Workflow code fix: `validate-alignment` now honors variant-specific `--required-variants` instead of always requiring full-prompt predictions.
- Generation parameter change: Ollama default `num_predict` was reduced to 8 for new local generations to encourage concise answer-format compliance; generated rows record runner metadata.
- Panel expansion: `gpqa_minimal_open_local` was expanded from one to three real Ollama models for preliminary workflow validation only.

## 17. Do-Not-Claim List

- Do not claim GPQA validity issues from these artifacts.
- Do not claim contamination, shortcuts, saturation, bad items, or model ranking findings.
- Do not treat this preliminary three-model panel as paper-grade evidence.
- Do not mix `gpqa_smoke_local` outputs with `gpqa_minimal_open_local` outputs.

## 18. Next Commands

```bash
python3 -m valideval gpqa-go-no-go --benchmark gpqa_diamond --items data/gpqa/gpqa_diamond.jsonl --panel gpqa_minimal_open_local
python3 -m valideval check-panel --panel gpqa_open_local
# To improve the preliminary blocker, add more real local/open models and regenerate/score full outputs.
```

## Phase 23 Update

The preliminary panel was expanded to five real local Ollama models by adding `llama3.2:3b` and `gemma2:2b`.

- Full-prompt outputs now exist for all five models.
- Non-full variants remain complete for the original three models only.
- Full aggregate predictions now have 990 rows; other primary aggregates have 594 rows.
- All primary matrices were rebuilt.
- Current go/no-go remains **no_go** because 5 models are available versus the 8-model threshold and full-prompt extraction success is 0.746 versus the 0.95 threshold.

Phase 23 also documented a `scoring_parser_bugfix` and a separate exploratory `full_answer_only_v2` prompt-compliance probe. Neither changes the primary preregistered diagnostic path, and no diagnostics were interpreted.

## Phase 24 Update

The preliminary panel now has eight local Ollama models. Full-prompt coverage is complete for all eight; non-full primary variants are complete for five.

Go/no-go remains **no_go** because primary full extraction success is 0.721 versus the 0.95 threshold. Model count now passes. The exploratory `full_answer_only_v2` path crosses the extraction threshold at 0.980 across five models, but it remains a secondary prompt-compliance path requiring formal amendment before any primary use.
