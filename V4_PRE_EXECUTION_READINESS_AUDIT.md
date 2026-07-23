# V4 Pre-Execution Readiness Audit

Generated: 2026-07-09

## Current Real Evidence

- Active real panel: `cache/mmlu/wide/matrix.csv`.
- MMLU panel: 39 models, 14,042 item columns, 57 subjects, zero missingness according to the existing reports.
- Real MMLU diagnostics already present:
  - `MMLU_DEEP_DIAGNOSTIC_VALUE_REPORT.md`
  - `SCALABLE_IRT_UPGRADE_REPORT.md`
  - `BOOTSTRAP_MATERIALITY_REPORT.md`
  - `DIAGNOSTIC_FAMILY_ABLATION_REPORT.md`
  - `MMLU_RANKING_DISAGREEMENT_BASELINES_REPORT.md`
- Paper-ready claim boundary: subject-level MMLU ranking sensitivity and proxy psychometric summaries are artifact-backed under the stated protocol.

## Blocked Evidence

- GSM8K real outputs: `RESULT_REQUIRED`.
- BBH or TruthfulQA third-benchmark outputs: `RESULT_REQUIRED`.
- Cross-benchmark evidence: blocked until at least two imported matrices exist.
- Human labels: absent.
- External labels beyond the weak/structural MMLU-Redux path: absent.
- Full parametric 2PL: not claimed.
- `FINAL_GOD_TIER_GATE_V3.md` is not present at repository root; the adjacent V3 prompt file exists at `valideval_execution_only_god_tier_pack_v3/19_final_god_tier_gate.md`.

## Execution Dependencies

- User-run Kaggle GPU/accelerator session.
- Internet/model-download availability on Kaggle, unless models are supplied as Kaggle inputs.
- `lm_eval`, `transformers`, `datasets`, `torch`, `pandas`, `numpy`, and `pyyaml` in the Kaggle environment.
- Local post-run import with `python3 -m valideval import-kaggle-outputs --strict`.

## Exact Files Needed From Kaggle

Place returned ZIPs under one of:

- `kaggle_outputs/gsm8k/valideval_outputs.zip`
- `kaggle_outputs/bbh/valideval_outputs.zip`
- `kaggle_outputs/third_benchmark/valideval_outputs.zip`
- `kaggle_outputs/truthfulqa/valideval_outputs.zip`

Each ZIP must contain:

- `predictions.jsonl`
- `matrix.csv`
- `manifest.json`
- `model_status.csv`
- `failed_models.csv`
- `run_log.txt`
- `environment.json`

## Exact Import Flow

```bash
python3 -m valideval import-kaggle-outputs \
  --input-dir kaggle_outputs \
  --output-root data/external/kaggle_imported \
  --cache-root cache \
  --results-root results \
  --strict
```

Then run the router, for example:

```bash
python3 -m valideval post-import-analysis \
  --benchmark gsm8k \
  --matrix cache/gsm8k/wide/matrix.csv \
  --predictions cache/gsm8k/wide/predictions.jsonl \
  --output results/gsm8k \
  --execute
```

## Exact Paper Update Flow

```bash
python3 -m valideval cross-benchmark-analysis \
  --benchmarks mmlu,gsm8k,bbh \
  --cache-root cache \
  --results-root results \
  --output results/cross_benchmark \
  --execute

python3 scripts/update_paper_from_artifacts_v4.py
```

## Risks Before Execution

- Kaggle OOM or timeout for medium/full panels.
- Model download or gated-model access failure.
- `lm_eval` sample schema drift.
- Partial outputs with no normalized `correct` field.
- Small panels may import successfully but remain panel-validity blocked for strong psychometric claims.

## What To Do After Kaggle Finishes

1. Download `valideval_outputs.zip`.
2. Put GSM8K ZIP under `kaggle_outputs/gsm8k/`.
3. Put BBH ZIP under `kaggle_outputs/bbh/` or `kaggle_outputs/third_benchmark/`.
4. Run `bash scripts/run_after_kaggle_outputs_v4.sh`.
5. Inspect `results/kaggle_import_v4/import_summary.json`, `results/gsm8k/post_import_analysis_manifest.json`, and `results/cross_benchmark/cross_benchmark_manifest.json`.
6. Only update paper claims if the imported manifests and validation reports are real and passing.

Final verdict: `V4_EXECUTION_READY_WITH_USER_GPU_RUN_REQUIRED`
