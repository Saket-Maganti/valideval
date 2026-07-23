# Third-Benchmark Notebook Hardening Report

Updated notebooks:

- `kaggle_third_benchmark/valideval_third_benchmark_runner.ipynb`
- `kaggle_general/valideval_multi_model_matrix_runner.ipynb`

Default selected benchmark: `BBH`, consistent with `THIRD_BENCHMARK_SELECTION_REPORT.md`.

Hardening added:

- Smoke, subset, and full modes.
- `VALIDEVAL_TASK_SUBSET` task-subset override.
- Resume support through partial shard normalization.
- Output ZIP packaging with manifest, status CSVs, run log, environment, predictions, and matrix.
- Strict schema validation before packaging.
- Runtime tables and OOM fallback instructions.
- TruthfulQA remains import-supported but is not the default third-benchmark path.

No local BBH/TruthfulQA inference was run and no third-benchmark evidence was fabricated.

Final verdict: `THIRD_BENCHMARK_NOTEBOOK_READY`
