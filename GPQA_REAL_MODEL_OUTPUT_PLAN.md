# GPQA Real Model Output Plan

## 1. Current Panel Status

`gpqa_minimal_open_local` now has the first preliminary real local full-prompt output artifact.

- Configured models: 1
- Available real/cached models: 1
- Cached prediction variants: `full`
- Cached matrix variants: `full`
- Full-prompt matrix: `cache/gpqa_diamond/gpqa_minimal_open_local/matrix_full.csv`

`gpqa_open_local` remains blocked for paper-grade real audit use until real outputs are configured or imported for that panel.

Smoke/mock files exist under `local_outputs/gpqa/full/`, but they are excluded from real audit paths.

## 2. Local Runner Status

- Ollama CLI: installed at `/opt/homebrew/bin/ollama`
- Ollama server: ran successfully during Phase 21 generation
- Pulled/available small model: `qwen2.5:1.5b-instruct`
- Other local runners in this repo: no non-mock runner beyond Ollama was found in `src/valideval/models/`

## 3. Recommended Minimal Real Local Panel

Current preliminary local workflow panel:

```text
configs/panels/gpqa_minimal_open_local.yaml
```

Configured Ollama model:

- `qwen2.5:1.5b-instruct`

Purpose: real local workflow validation / preliminary audit only. It is not paper-grade and is not a replacement for `gpqa_open_local`.

## 4. Recommended Paper-Grade Panel

Use the preregistered `configs/panels/gpqa_open_local.yaml` plan, or import equivalent cached outputs with documented model IDs, runner settings, seed, temperature, prompt-template hash, and prompt variant.

Recommended minimum:

- 8 non-baseline real open/local models
- 2 baselines
- At least 95 percent parseable outputs under the preregistered extraction threshold
- Matrices for `full` and all planned prompt variants

## 5. Ollama Setup Commands

Start the local server:

```bash
ollama serve
```

Pull the current minimal workflow-validation model:

```bash
ollama pull qwen2.5:1.5b-instruct
```

Check readiness:

```bash
python3 -m valideval check-panel --panel gpqa_minimal_open_local
```

## 6. Estimated Output-Generation Commands

Generate another preregistered prompt variant for the preliminary panel:

```bash
python3 -m valideval generate-outputs \
  --benchmark gpqa_diamond \
  --items data/gpqa/gpqa_diamond.jsonl \
  --panel gpqa_minimal_open_local \
  --prompt-variant question_only \
  --output-dir local_outputs/gpqa/question_only
```

Preregistered panel generation, once real local/cached models are configured:

```bash
python3 -m valideval generate-outputs \
  --benchmark gpqa_diamond \
  --items data/gpqa/gpqa_diamond.jsonl \
  --panel gpqa_open_local \
  --prompt-variant full \
  --output-dir local_outputs/gpqa/full
```

## 7. Runtime Caveats

GPQA Diamond has 198 items. One full-prompt pass is 198 generations per model. All five preregistered variants are 990 generations per model.

Use resume behavior by rerunning the same generation command after interruption. Use `--overwrite` only with a documented reason.

## 8. Diagnostics Blocked Until Outputs Exist

For `gpqa_minimal_open_local`, full matrix construction is complete, but go/no-go remains blocked by missing variants, one-model panel size, and extraction threshold. For `gpqa_open_local`, all real diagnostics remain blocked until real outputs and matrices exist.

IRT/proxy psychometrics should remain blocked or explicitly limited below the preregistered model-count threshold.

## 9. Importing Outputs Generated Elsewhere

For raw outputs:

```bash
python3 -m valideval score-outputs \
  --benchmark gpqa_diamond \
  --items data/gpqa/gpqa_diamond.jsonl \
  --input <raw_output_file.jsonl> \
  --output cache/gpqa_diamond/gpqa_open_local/predictions_full.jsonl \
  --prompt-variant full
```

For already scored outputs:

```bash
python3 -m valideval import-outputs \
  --input <scored_output_file.jsonl> \
  --output cache/gpqa_diamond/gpqa_open_local/predictions_full.jsonl \
  --adapter generic-jsonl \
  --benchmark-id gpqa_diamond \
  --prompt-variant full
```

Do not import smoke/mock outputs into real panels.

## 10. Do-Not-Claim List

- Do not claim GPQA validity findings from this model-output plan.
- Do not claim smoke/mock outputs are scientific evidence.
- Do not claim `gpqa_minimal_open_local` is paper-grade.
- Do not interpret diagnostics until real outputs pass the relevant go/no-go gate.
- Do not expose raw GPQA question text in reports or logs.

## Phase 22 Update

`gpqa_minimal_open_local` now contains three real local Ollama models and has complete preliminary outputs for all five preregistered prompt variants. The panel remains preliminary workflow-validation only.

Current blockers:

- `required_model_count_met`: 3 models available versus the configured 8-model go/no-go threshold.
- `extraction_success_threshold_met`: full-prompt extraction success remains below the preregistered threshold.

Next work should either add more real local/open models or improve answer-format compliance through documented generation-side changes. Do not change scoring/extraction rules unless a fatal workflow bug is found.

## Phase 23 Update

`gpqa_minimal_open_local` now has five configured and available local Ollama models:

- `qwen2.5:1.5b-instruct`
- `qwen2.5:3b-instruct`
- `llama3.2:1b`
- `llama3.2:3b`
- `gemma2:2b`

Full-prompt outputs exist for all five models. Non-full variants still need to be generated for `llama3.2:3b` and `gemma2:2b` if five-model prompt-variant coverage is required.

Current blockers:

- `required_model_count_met`: 5 models available versus the configured 8-model go/no-go threshold.
- `extraction_success_threshold_met`: full-prompt extraction success 0.746 versus threshold 0.95.

The next practical model-output work is either to add at least three more real local/open models, or to complete non-full variants for the two added models while keeping all artifacts labeled preliminary.
