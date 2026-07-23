# GPQA Answer-Only and Panel Completion Report

This report intentionally omits raw GPQA question text and raw model output text.

## 1. Executive Summary

Phase 24 completed five-model coverage for all primary prompt variants, ran a controlled exploratory answer-only extraction-compliance test, expanded the preliminary panel to eight locally available Ollama models for full-prompt coverage, rebuilt matrices, refreshed manifest and go/no-go, and stopped before diagnostic interpretation.

Current go/no-go remains `no_go`. The model-count gate now passes, but primary full-prompt extraction success remains below the preregistered 0.95 threshold. The separate `full_answer_only_v2` path crosses the extraction threshold, but it is exploratory and must not replace the preregistered primary prompt without a formal amendment.

## 2. Starting State

- GPQA Diamond local item file: `data/gpqa/gpqa_diamond.jsonl`
- Item count: 198
- Starting panel size: 5 local Ollama models
- Starting primary coverage: `full` had 5 models; non-full variants had 3 models.
- Starting go/no-go: `no_go`
- Starting blockers: model count below 8 and primary extraction success below 0.95.

## 3. Current Model Panel

`gpqa_minimal_open_local` now contains eight real local Ollama models:

- `qwen2.5:1.5b-instruct`
- `qwen2.5:3b-instruct`
- `llama3.2:1b`
- `llama3.2:3b`
- `gemma2:2b`
- `qwen2.5:7b-instruct`
- `mistral:latest`
- `llama3:latest`

This remains a preliminary/local workflow-validation panel, not paper-grade.

## 4. Added Models

Added in Phase 24:

- `qwen2.5:7b-instruct`
- `mistral:latest`
- `llama3:latest`

All three were already installed locally in Ollama and were generated for the primary `full` prompt. The measured runtime for these medium models was slow, so non-full variants for these three models were not launched in this phase and are documented as a compute/time blocker.

## 5. Primary Prompt Variant Completion

Primary aggregate coverage:

| Variant | Models | Rows | Missing configured model outputs |
| --- | ---: | ---: | --- |
| `full` | 8 | 1584 | none |
| `question_only` | 5 | 990 | `qwen2.5:7b-instruct`, `mistral:latest`, `llama3:latest` |
| `choices_only` | 5 | 990 | `qwen2.5:7b-instruct`, `mistral:latest`, `llama3:latest` |
| `randomized_choices` | 5 | 990 | `qwen2.5:7b-instruct`, `mistral:latest`, `llama3:latest` |
| `answer_letter_only` | 5 | 990 | `qwen2.5:7b-instruct`, `mistral:latest`, `llama3:latest` |

The five smaller/current models now have complete coverage across all five primary variants.

## 6. Answer-Only v2 Experiment

Exploratory prompt:

```text
configs/prompts/gpqa/full_answer_only_v2.yaml
```

Outputs:

- Directory: `local_outputs/gpqa/full_answer_only_v2/`
- Aggregate predictions: `cache/gpqa_diamond/gpqa_minimal_open_local/predictions_full_answer_only_v2.jsonl`
- Matrix: `cache/gpqa_diamond/gpqa_minimal_open_local/matrix_full_answer_only_v2.csv`
- Coverage: 5 models, 990 rows

This path is explicitly separate from primary preregistered matrices.

## 7. Extraction Comparison

| Path | Outputs | Success | Invalid | Ambiguous | Passes 0.95 |
| --- | ---: | ---: | ---: | ---: | --- |
| Primary `full` | 1584 | 0.721 | 442 | 53 | false |
| Exploratory `full_answer_only_v2` | 990 | 0.980 | 20 | 19 | true |

Comparison artifacts:

- `results/gpqa_diamond/input_validation/answer_only_v2_extraction_comparison.md`
- `results/gpqa_diamond/input_validation/answer_only_v2_extraction_comparison.json`

The v2 result supports only an extraction-compliance observation. It is not a GPQA diagnostic result and is not a validity claim.

## 8. Scoring Status

New Phase 24 scoring jobs: 16.

- Three full-prompt files for added medium models.
- Eight non-full files for `llama3.2:3b` and `gemma2:2b`.
- Five exploratory `full_answer_only_v2` files.

Scoring job metadata:

```text
results/gpqa_diamond/input_validation/phase24_scoring_jobs.json
```

## 9. Alignment Status

Alignment summary:

```text
results/gpqa_diamond/input_validation/alignment_summary.md
results/gpqa_diamond/input_validation/alignment_summary.json
```

Alignment passed for all included complete aggregate files. Primary non-full aggregates are complete for the five included models but not for the three newly added medium models.

## 10. Matrix Status

Primary matrices:

- `matrix_full.csv`: 8 model rows, 198 item columns
- `matrix_question_only.csv`: 5 model rows, 198 item columns
- `matrix_choices_only.csv`: 5 model rows, 198 item columns
- `matrix_randomized_choices.csv`: 5 model rows, 198 item columns
- `matrix_answer_letter_only.csv`: 5 model rows, 198 item columns

Exploratory matrix:

- `matrix_full_answer_only_v2.csv`: 5 model rows, 198 item columns

The exploratory matrix does not replace `matrix_full.csv`.

## 11. Prompt Variant Completeness

`validate-prompt-variants` status: `pass`.

All five primary aggregate prediction files and matrix files exist. This check does not assert eight-model coverage for every non-full variant; model-level coverage is recorded in the alignment and aggregate summaries.

## 12. Manifest Status

Manifest refreshed:

```text
results/gpqa_diamond/input_validation/audit_manifest.json
```

The primary manifest includes hashes for primary item, output, prediction, matrix, config, prompt-template, preregistration, and code artifacts. The v2 prompt hash is present as a prompt-template hash, but v2 remains exploratory and separate from the primary manifest path.

## 13. Go/No-Go Result

Current status: `no_go`.

Passing checks now include:

- real GPQA JSONL valid
- no fixture data mixed
- prompt templates frozen
- preregistration exists
- panel config exists
- required primary prompt variants present
- complete full-prompt matrix
- required model count met: 8 of 8
- scoring-rule tracking recorded

Blocked check:

- `extraction_success_threshold_met`: primary full success 0.721 versus threshold 0.95.

## 14. Dry-Run-Real Result

Dry-run-real was not run because go/no-go returned `no_go`.

## 15. Diagnostics Allowed Later

No diagnostic interpretation is allowed from this phase. A later phase may use these artifacts only after go/no-go passes or after an explicitly amended protocol scopes exploratory output separately.

## 16. Diagnostics Blocked

- Primary preregistered diagnostic interpretation remains blocked by extraction threshold failure.
- Eight-model prompt-variant comparisons remain incomplete because non-full variants are only five-model complete.
- `full_answer_only_v2` cannot be treated as the official audit prompt without formal preregistration amendment.
- Paper-grade `gpqa_open_local` remains separate from this preliminary panel.

## 17. Deviations / Amendment Recommendation

Existing documented deviation:

- `scoring_parser_bugfix`
- `secondary_exploratory_extraction_compliance`

Recommendation: if answer-only prompting is to be used for a real audit, create a formal preregistration amendment before rerunning primary outputs. Otherwise, keep v2 as a separate exploratory extraction-compliance artifact and report it separately from preregistered primary results.

## 18. Do-Not-Claim List

- Do not claim any GPQA validity finding.
- Do not claim shortcut, contamination, saturation, bad-item, or ranking evidence.
- Do not claim v2 is the official audit prompt.
- Do not mix v2 outputs into primary matrices.
- Do not mix smoke/mock files with real preliminary outputs.
- Do not run interpreted diagnostics while go/no-go is `no_go`.

## 19. Next Commands

To complete eight-model non-full primary coverage:

```bash
python3 -m valideval generate-outputs --benchmark gpqa_diamond --items data/gpqa/gpqa_diamond.jsonl --panel gpqa_minimal_open_local --prompt-variant question_only --output-dir local_outputs/gpqa/question_only
python3 -m valideval generate-outputs --benchmark gpqa_diamond --items data/gpqa/gpqa_diamond.jsonl --panel gpqa_minimal_open_local --prompt-variant choices_only --output-dir local_outputs/gpqa/choices_only
python3 -m valideval generate-outputs --benchmark gpqa_diamond --items data/gpqa/gpqa_diamond.jsonl --panel gpqa_minimal_open_local --prompt-variant randomized_choices --output-dir local_outputs/gpqa/randomized_choices
python3 -m valideval generate-outputs --benchmark gpqa_diamond --items data/gpqa/gpqa_diamond.jsonl --panel gpqa_minimal_open_local --prompt-variant answer_letter_only --output-dir local_outputs/gpqa/answer_letter_only
```

To proceed with v2 as primary, first write a formal preregistration amendment and rerun under that amended protocol.

## Phase 25 Update

The preregistration has been formally amended in `docs/protocols/gpqa_diamond_preregistration_amended_v2.md`, with `configs/audits/gpqa_diamond_amended_v2.yaml` as the amended audit config.

`full_answer_only_v2` now has 8-model coverage and a rebuilt aggregate prediction file and matrix. The amended path remains blocked because extraction success across the 8-model panel is 0.941 versus the 0.95 threshold.

Dry-run-real was not run. No diagnostics were interpreted.

## Phase 26 Update

The amended v2 extraction failures were reviewed using sanitized output patterns only. No true parser-bug candidates were found, so no extractor change or re-score was performed.

Current amended status remains `no_go`: v2 extraction success is 0.941 versus the 0.95 threshold. A separate threshold review was written at `docs/protocols/gpqa_diamond_extraction_threshold_review.md`.
