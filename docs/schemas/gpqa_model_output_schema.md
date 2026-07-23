# GPQA Cached Model Output Schemas

Artifact class: **gpqa_real_input_validation**.

Two local cached-output modes are supported. Neither mode calls paid APIs or closed services.

## Mode A: scored predictions

Use `schemas/gpqa_model_prediction_scored.schema.json` when the output file already contains `prediction`, `score`, and `is_correct`.

```json
{
  "model_id": "qwen2_5_7b_instruct",
  "item_id": "gpqa_diamond_000001",
  "prompt_variant": "full",
  "prediction": "C",
  "is_correct": true,
  "score": 1.0,
  "raw_output": "The answer is C.",
  "metadata": {
    "temperature": 0,
    "seed": 0,
    "source": "local_cached_output"
  }
}
```

Import command:

```bash
python3 -m valideval import-outputs --input local_outputs/gpqa_full.jsonl --output cache/gpqa_diamond/gpqa_open_local/predictions_full.jsonl --adapter generic-jsonl --benchmark-id gpqa_diamond --prompt-variant full
```

## Mode B: raw unscored outputs

Use `schemas/gpqa_model_output_raw.schema.json` when only raw text outputs are available. ValidEval scores these with the frozen GPQA extractor: strict letter first, lenient letter second, normalized choice-text match third.

```json
{
  "model_id": "qwen2_5_7b_instruct",
  "item_id": "gpqa_diamond_000001",
  "prompt_variant": "full",
  "raw_output": "The answer is C.",
  "metadata": {
    "temperature": 0,
    "seed": 0,
    "source": "local_cached_output"
  }
}
```

Scoring command:

```bash
python3 -m valideval score-outputs --benchmark gpqa_diamond --items data/gpqa/gpqa_diamond.jsonl --input local_outputs/gpqa_full_raw.jsonl --output cache/gpqa_diamond/gpqa_open_local/predictions_full.jsonl --prompt-variant full
```

Then build a matrix:

```bash
python3 -m valideval matrix-from-predictions --benchmark gpqa_diamond --panel gpqa_open_local --variant full
```

Input-validation reports must be interpreted only as readiness checks. They are not GPQA Diamond validity findings.
