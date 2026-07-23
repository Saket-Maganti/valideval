# GPQA Output Generation Plan

## Current State

Phase 21 generated the first real local GPQA full-prompt outputs with Ollama for the preliminary `gpqa_minimal_open_local` panel.

- Model: `qwen2.5:1.5b-instruct`
- Raw output rows: 198
- Scored prediction rows: 198
- Full matrix: `cache/gpqa_diamond/gpqa_minimal_open_local/matrix_full.csv`
- Go/no-go: `no_go`

Smoke/mock outputs remain excluded from all real audit artifacts.

## Completed Commands

```bash
ollama pull qwen2.5:1.5b-instruct
python3 -m valideval generate-outputs \
  --benchmark gpqa_diamond \
  --items data/gpqa/gpqa_diamond.jsonl \
  --panel gpqa_minimal_open_local \
  --prompt-variant full \
  --output-dir local_outputs/gpqa/full
python3 -m valideval score-outputs \
  --benchmark gpqa_diamond \
  --items data/gpqa/gpqa_diamond.jsonl \
  --input local_outputs/gpqa/full/qwen2.5_1.5b-instruct.jsonl \
  --output cache/gpqa_diamond/gpqa_minimal_open_local/qwen2.5_1.5b-instruct_full_predictions.jsonl \
  --prompt-variant full
python3 -m valideval matrix-from-predictions \
  --benchmark gpqa_diamond \
  --panel gpqa_minimal_open_local \
  --variant full
```

## Current Blockers

- Missing prompt variants: answer_letter_only, choices_only, question_only, randomized_choices
- Model count is below the preregistered threshold.
- Extraction success is below the preregistered threshold.
- `gpqa_open_local` still lacks real outputs and matrices.

## Next Real Local Command

```bash
python3 -m valideval generate-outputs \
  --benchmark gpqa_diamond \
  --items data/gpqa/gpqa_diamond.jsonl \
  --panel gpqa_minimal_open_local \
  --prompt-variant question_only \
  --output-dir local_outputs/gpqa/question_only
```

Do not run diagnostic interpretation in this phase.

## Phase 22 Update

The preliminary local panel has been expanded and generated:

- Models: `qwen2.5:1.5b-instruct`, `qwen2.5:3b-instruct`, `llama3.2:1b`
- Generated variants: `full`, `question_only`, `choices_only`, `randomized_choices`, `answer_letter_only`
- Real preliminary raw files: 15
- Per-model scored prediction files: 15
- Aggregate prediction files: 5
- Matrices: 5

Current blockers:

- Model count remains below the configured go/no-go threshold: 3 available versus 8 required.
- Full-prompt extraction success remains below the preregistered threshold.
- `gpqa_open_local` remains paper-grade blocked until real outputs and matrices are provided for that configured panel.

Next command:

```bash
python3 -m valideval gpqa-go-no-go \
  --benchmark gpqa_diamond \
  --items data/gpqa/gpqa_diamond.jsonl \
  --panel gpqa_minimal_open_local
```

## Phase 23 Update

The preliminary panel now has five real local Ollama models. Full-prompt output generation was completed for the two added models:

- `local_outputs/gpqa/full/llama3.2_3b.jsonl`
- `local_outputs/gpqa/full/gemma2_2b.jsonl`

Full-prompt aggregate predictions now include 990 rows across five models, and `matrix_full.csv` was rebuilt. Non-full variants remain complete for the original three models only.

Current blockers:

- Model count remains below the configured go/no-go threshold: 5 available versus 8 required.
- Full-prompt extraction success remains below the preregistered threshold: 0.746 versus 0.95.

Next real local generation priority:

```bash
python3 -m valideval generate-outputs \
  --benchmark gpqa_diamond \
  --items data/gpqa/gpqa_diamond.jsonl \
  --panel gpqa_minimal_open_local \
  --prompt-variant randomized_choices \
  --output-dir local_outputs/gpqa/randomized_choices
```

## Phase 24 Update

Completed in Phase 24:

- Five-model primary coverage for all prompt variants.
- Eight-model `full` coverage.
- Five-model exploratory `full_answer_only_v2` coverage.

Not completed in Phase 24:

- Non-full variants for `qwen2.5:7b-instruct`, `mistral:latest`, and `llama3:latest`.

Reason: measured local runtime for the added medium models made the remaining 2,376 non-full generations impractical for this phase. Existing outputs are resume-safe, so rerunning the commands later will fill only missing model files.
