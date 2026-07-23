# Real MMLU Input Acquisition Report

Timestamp: 2026-06-12T14:40:57Z

## Summary

Real public MMLU per-instance prediction details were acquired from HELM MMLU public release `v1.13.0`, normalized into `data/external/mmlu/prediction_details.jsonl`, imported into `cache/mmlu/wide/predictions.jsonl`, and converted into `cache/mmlu/wide/matrix.csv`.

MMLU-Redux issue labels were also normalized from `edinburgh-dawg/mmlu-redux-2.0` into `data/ground_truth/mmlu_redux_issues.normalized.jsonl`. Raw question text, choices, prompts, and raw instances were not persisted in the normalized files or this report.

This is real public-source evidence. It is not fixture/mock evidence, not local model inference, not an expensive audit run, and not a benchmark-validity claim.

## Sources Checked

- HELM MMLU raw results / per-instance predictions: used.
- Hugging Face Open LLM Leaderboard detailed prediction datasets: checked, not used because sampled detail datasets exposed MMLU-Pro files rather than original MMLU per-instance files.
- OpenCompass result dumps: searched locally, not found.
- Local lm-evaluation-harness outputs: found under `data/external/mmlu/lm_eval_outputs/`, not used for the final official/public normalized file.

## Files Created

- `scripts/acquire_real_mmlu_inputs.py`
- `data/external/mmlu/README.md`
- `data/external/mmlu/SOURCE_STATUS.md`
- `data/external/mmlu/prediction_details.jsonl`
- `data/external/mmlu/source_manifest.json`
- `data/ground_truth/mmlu_redux_issues.normalized.jsonl`
- `cache/mmlu/wide/predictions.jsonl`
- `cache/mmlu/wide/matrix.csv`
- `results/mmlu/import_mapping_report.md`
- `results/mmlu/wide_matrix_report.md`

## Prediction Details

- Source: HELM MMLU public release `v1.13.0`
- Source page: `https://crfm.stanford.edu/helm/mmlu/latest/`
- Release data base: `https://storage.googleapis.com/crfm-helm-public/gzip/mmlu/benchmark_output`
- Models:
  - `google/gemma-7b`
  - `mistralai/mistral-7b-v0.1`
  - `qwen/qwen1.5-7b`
- Subjects: 57
- Unique item ids: 14,042
- Prediction rows: 42,126
- Missing HELM runs: 0
- Normalized prediction SHA-256: `0ac97f31239966c1e986274d59f55e8778e900aa58aaf2a766b9425f332a707e`

The script reads HELM `instances.json` only to map the correct reference tag to `gold`; it does not persist raw MMLU question text.

## MMLU-Redux Labels

- Source dataset: `edinburgh-dawg/mmlu-redux-2.0`
- Output: `data/ground_truth/mmlu_redux_issues.normalized.jsonl`
- Rows: 370
- Subjects with issue labels: 49
- Raw question text persisted: no
- SHA-256: `811a92386a4c343faf98209aceaf598e92e305776177f479102d1de095b2cd69`

Important limitation: the normalized MMLU-Redux rows currently use stable dataset row ids and do not expose HELM instance ids. MMLU-Redux validation still requires an explicit alignment/import step before making any Redux validation claim.

## Commands Used

Acquire public-source inputs:

```bash
/usr/bin/time -p python3 scripts/acquire_real_mmlu_inputs.py
```

Final successful runtime:

```text
real 333.34
user 9.05
sys 0.85
```

Import normalized prediction details:

```bash
/usr/bin/time -p python3 -m valideval import-published-details \
  --benchmark mmlu \
  --input data/external/mmlu/prediction_details.jsonl \
  --format auto \
  --output cache/mmlu/wide/predictions.jsonl \
  --mapping-report results/mmlu/import_mapping_report.md
```

Runtime:

```text
real 1.69
user 1.38
sys 0.13
```

Build the wide matrix:

```bash
/usr/bin/time -p python3 -m valideval matrix-from-wide-predictions \
  --predictions cache/mmlu/wide/predictions.jsonl \
  --output cache/mmlu/wide/matrix.csv \
  --report results/mmlu/wide_matrix_report.md
```

Runtime:

```text
real 1.29
user 1.14
sys 0.08
```

## Import And Matrix Results

- Import status: `ok`
- Rows read: 42,126
- Rows written: 42,126
- Duplicate rows: 0
- Missing required fields: 0
- Imported prediction SHA-256: `a512ba995c8021e3d72bf48c32cc9c42c306351b2710014f7fe2d8571c46c2c6`
- Matrix rows: 3
- Matrix item columns: 14,042
- Missing cells: 0
- Matrix SHA-256: `d265a471d07ae89c8ffa1e72c93e7f506ea7ca3661b48ae7093ec8b1aeacc9db`

## Acquisition Notes

The first acquisition attempt wrote MMLU-Redux labels but selected zero HELM prediction rows because the initial script defaults used HELM run-name-style underscore model ids instead of HELM `adapter_spec.model` slash ids. The selector was fixed to use:

- `mistralai/mistral-7b-v0.1`
- `google/gemma-7b`
- `qwen/qwen1.5-7b`

The successful rerun produced the files and counts recorded above.

## Blockers And Limits

- No model inference was run.
- No expensive ValidEval audits were run.
- No mock/example files were used as evidence.
- MMLU-Redux validation has not been run.
- The MMLU-Redux label file is normalized, but alignment to HELM item ids is still unresolved.
- These files support later diagnostics; they do not establish that MMLU is valid or invalid.

## Next Command

The next narrow evidence-generation command, if approved, is a panel-validity run on the real HELM-derived matrix:

```bash
python3 -m valideval panel-validity \
  --matrix cache/mmlu/wide/matrix.csv \
  --output results/mmlu/panel_validity
```
