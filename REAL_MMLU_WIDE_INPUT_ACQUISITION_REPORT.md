# Real MMLU Wide Input Acquisition Report

## Summary

Expanded real MMLU per-instance prediction details were acquired from public HELM MMLU artifacts without model inference. Raw MMLU question text was not persisted.

## Discovery

- Candidate models: 79
- Complete by release manifest: 79
- Partial by release manifest: 0
- Default selected models: 39

## Expanded Prediction File

- Status: `ok`
- Output: `data/external/mmlu/prediction_details_wide.jsonl`
- HELM release: `v1.13.0`
- Complete models: 39
- Partial selected models: 0
- Items per complete model: 14042
- Rows: 547638
- Empty prediction rows after normalization: 0
- SHA-256: `38485dc89aa44f44cd5f8078df246d76aad3570ce15295559fa0a72d6f9379c6`
- Runtime seconds: 1600.377

## Compatibility

- Same HELM release: `True`
- Same subjects: `True`
- Same item IDs: `True`
- Same gold labels: `True`
- Duplicate rows: 0
- Invalid gold labels: 0
- Invalid prediction labels: 1331

## Complete Models

- `01-ai/yi-34b`
- `01-ai/yi-6b`
- `01-ai/yi-large-preview`
- `allenai/olmo-1.7-7b`
- `allenai/olmo-7b`
- `databricks/dbrx-instruct`
- `deepseek-ai/deepseek-llm-67b-chat`
- `deepseek-ai/deepseek-v3`
- `google/gemma-2-27b`
- `google/gemma-2-9b`
- `google/gemma-7b`
- `meta/llama-2-13b`
- `meta/llama-2-70b`
- `meta/llama-2-7b`
- `meta/llama-3-70b`
- `meta/llama-3-8b`
- `meta/llama-3.1-405b-instruct-turbo`
- `meta/llama-3.1-70b-instruct-turbo`
- `meta/llama-3.1-8b-instruct-turbo`
- `meta/llama-3.2-11b-vision-instruct-turbo`
- `meta/llama-3.2-90b-vision-instruct-turbo`
- `meta/llama-3.3-70b-instruct-turbo`
- `microsoft/phi-2`
- `microsoft/phi-3-medium-4k-instruct`
- `microsoft/phi-3-small-8k-instruct`
- `mistralai/mistral-7b-instruct-v0.3`
- `mistralai/mistral-7b-v0.1`
- `mistralai/mixtral-8x22b`
- `mistralai/mixtral-8x7b-32kseqlen`
- `mistralai/open-mistral-nemo-2407`
- `qwen/qwen1.5-110b-chat`
- `qwen/qwen1.5-14b`
- `qwen/qwen1.5-32b`
- `qwen/qwen1.5-72b`
- `qwen/qwen1.5-7b`
- `qwen/qwen2-72b-instruct`
- `qwen/qwen2.5-72b-instruct-turbo`
- `qwen/qwen2.5-7b-instruct-turbo`
- `snowflake/snowflake-arctic-instruct`

## Warnings

- No raw MMLU question text was persisted.
- The default model set excludes known closed or paid API provider prefixes when enough public-artifact models are available.
- Some model predictions are outside A-D; correctness fields remain from HELM.
