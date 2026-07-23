# lm-eval MMLU Acquisition Runbook

This runbook explains how to create the missing real per-instance prediction details. Do not run
MMLU evaluation until model names and GPU/CPU usage are explicitly approved.

## 1. Install / Confirm lm-evaluation-harness

Use the environment you want for the actual evaluation. Example:

```bash
python3 -m pip install "lm-eval"
lm_eval --help
```

## 2. Choose Model Names First

Do not guess models. Record the approved model list before running. The
2026-06-12 acquisition pilot used:

```text
MODEL_ID_1=Qwen/Qwen2.5-0.5B-Instruct
MODEL_ID_2=Qwen/Qwen2.5-1.5B-Instruct
MODEL_ID_3=TinyLlama/TinyLlama-1.1B-Chat-v1.0
```

## 3. Run lm-eval With Sample Logging

Example Hugging Face model command:

```bash
mkdir -p data/external/mmlu/lm_eval_outputs/<MODEL_SLUG>

lm_eval \
  --model hf \
  --model_args pretrained=<HF_MODEL_ID>,dtype=auto \
  --tasks mmlu \
  --num_fewshot 5 \
  --batch_size auto \
  --device cuda:0 \
  --log_samples \
  --output_path data/external/mmlu/lm_eval_outputs/<MODEL_SLUG>
```

MPS/CPU-constrained pilot shape:

```bash
lm_eval \
  --model hf \
  --model_args pretrained=<HF_MODEL_ID>,dtype=auto \
  --tasks mmlu_high_school_biology \
  --num_fewshot 0 \
  --limit 500 \
  --batch_size 1 \
  --device mps \
  --log_samples \
  --output_path data/external/mmlu/lm_eval_outputs/<MODEL_SLUG>
```

Repeat once per approved model. Keep each model in its own output folder.

## 4. Verify The Output Is Real

Run:

```bash
find data/external/mmlu/lm_eval_outputs -type f -name '*.jsonl' | sort | head -20
rg -n '"filtered_resps"|"resps"|"target"|"acc"|"exact_match"' data/external/mmlu/lm_eval_outputs
rg -n 'PARSER TEST ONLY|model_alpha|mock_mmlu_redux|wide_predictions_mock|mmlu_subset' data/external/mmlu/lm_eval_outputs
```

The first command should show lm-eval sample files. The second should show per-sample prediction
or score fields. The third should return no fixture/mock markers.

## 5. Convert lm-eval Outputs To ValidEval Wide Predictions

After the real lm-eval output directory exists:

```bash
python3 -m valideval import-published-details \
  --benchmark mmlu \
  --input data/external/mmlu/lm_eval_outputs \
  --format lm_eval \
  --output cache/mmlu/wide/predictions.jsonl \
  --mapping-report results/mmlu/import_mapping_report.md
```

Expected output:

```text
cache/mmlu/wide/predictions.jsonl
results/mmlu/import_mapping_report.md
cache/mmlu/wide/predictions.jsonl.summary.json
```

## 6. Build The Wide Matrix

Strict complete-matrix mode:

```bash
python3 -m valideval matrix-from-wide-predictions \
  --predictions cache/mmlu/wide/predictions.jsonl \
  --output cache/mmlu/wide/matrix.csv \
  --report results/mmlu/wide_matrix_report.md \
  --disallow-missing
```

If different models cover different subsets, omit `--disallow-missing` and report missingness:

```bash
python3 -m valideval matrix-from-wide-predictions \
  --predictions cache/mmlu/wide/predictions.jsonl \
  --output cache/mmlu/wide/matrix.csv \
  --report results/mmlu/wide_matrix_report.md
```

## 7. Verify The Matrix

```bash
python3 - <<'PY'
import pandas as pd
frame = pd.read_csv("cache/mmlu/wide/matrix.csv", index_col=0)
print("models", frame.shape[0])
print("items", frame.shape[1])
print("missing_cells", int(frame.isna().sum().sum()))
print("model_ids", list(frame.index)[:10])
print("item_ids", list(frame.columns)[:10])
PY
```

Then run:

```bash
python3 -m valideval panel-validity \
  --matrix cache/mmlu/wide/matrix.csv \
  --output results/mmlu/panel_validity
```

## 8. Evidence Boundary

Runs 1 and 2 count as complete only after:

- `cache/mmlu/wide/predictions.jsonl` is created from real lm-eval sample files
- `cache/mmlu/wide/matrix.csv` is built from that normalized file
- mapping reports show real source paths under `data/external/mmlu/lm_eval_outputs`
- fixture/mock marker scans are clean

The 2026-06-12 pilot is real but limited: it covers
`mmlu_high_school_biology`, not full all-subject MMLU.
