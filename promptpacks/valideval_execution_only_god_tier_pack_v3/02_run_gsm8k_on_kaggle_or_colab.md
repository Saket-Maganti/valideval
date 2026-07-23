# Prompt 02 — Run GSM8K on Kaggle or Colab

## Objective

Produce real GSM8K outputs. This is the main V3 blocker.

## Existing notebook

Use:

```text
kaggle_gsm8k/valideval_gsm8k_panel_runner.ipynb
```

If it is missing or broken, fix only enough to run.

## Target panel

Preferred: 10–20 small open models.
Minimum acceptable: 6 models, unless failures are documented.

Suggested panel:

- Qwen2.5-0.5B-Instruct
- Qwen2.5-1.5B-Instruct
- Qwen2.5-3B-Instruct
- TinyLlama-1.1B-Chat
- Gemma-2-2B-it if accessible
- Phi-3-mini if accessible
- Llama-3.2-1B/3B if accessible
- Mistral-7B-Instruct quantized if feasible

## Required output ZIP

```text
valideval_outputs.zip
```

It must contain:

```text
predictions.jsonl
matrix.csv
manifest.json
model_status.csv
run_log.txt
```

## If this environment cannot run Kaggle/Colab

Create:

```text
GSM8K_USER_KAGGLE_EXECUTION_REQUIRED.md
```

Include:

- exact notebook path,
- how to upload/open it on Kaggle,
- accelerator setting,
- expected runtime,
- cell order,
- expected ZIP name,
- download instructions,
- where to place ZIP locally: `kaggle_outputs/gsm8k/`,
- next prompt: `03_import_gsm8k_outputs.md`.

## Final verdict

```text
GSM8K_REAL_OUTPUT_READY
USER_KAGGLE_EXECUTION_REQUIRED
GSM8K_RUN_FAILED
```
