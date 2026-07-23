# Real MMLU Evidence Creation Report

> Historical/provenance note: this report describes the earlier 3-model
> `mmlu_high_school_biology` pilot. It is superseded for active panel status by
> `VALID_EVAL_EVIDENCE_RECONCILIATION_AUDIT.md`,
> `MMLU_WIDE_PANEL_ACQUISITION_REPORT.md`, `MMLU_PANEL_VALIDITY_REPORT.md`, and
> `MMLU_EVIDENCE_GATE_REPORT.md`.

Timestamp UTC: 2026-06-12T10:04:24Z

## Answer

Real MMLU per-instance predictions were generated and imported for a limited
pilot. The completed scope in this historical report is
`mmlu_high_school_biology`, not the later active all-subject HELM MMLU wide
panel.

## What Was Created

- Raw lm-eval outputs: `data/external/mmlu/lm_eval_outputs/`
- Wide predictions: `cache/mmlu/wide/predictions.jsonl`
- Wide matrix: `cache/mmlu/wide/matrix.csv`
- Import report: `results/mmlu/import_mapping_report.md`
- Matrix report: `results/mmlu/wide_matrix_report.md`
- Completion report: `results/mmlu/REAL_WIDE_IMPORT_COMPLETED.md`

## Models And Samples

| Model | Samples | Scope |
|---|---:|---|
| `Qwen/Qwen2.5-0.5B-Instruct` | 310 | `mmlu_high_school_biology` |
| `Qwen/Qwen2.5-1.5B-Instruct` | 310 | `mmlu_high_school_biology` |
| `TinyLlama/TinyLlama-1.1B-Chat-v1.0` | 310 | `mmlu_high_school_biology` |

Final normalized prediction rows: `930`.

Final matrix shape: `3 x 310`.

Missing cells: `0`.

## Mock Avoidance

Mock/example files were not used as real evidence:

- `examples/mmlu_subset.jsonl`: not used
- `examples/mmlu_redux_mock.jsonl`: not used
- `examples/mmlu_redux_mock.csv`: not used
- `tests/fixtures/lm_eval_samples/**`: parser tests only

The final normalized predictions retain source-file provenance pointing to
real lm-eval `--log_samples` files under `data/external/mmlu/lm_eval_outputs`.

## Runs 1 And 2

Run 1, import real MMLU per-instance prediction details: completed for the
limited MMLU high-school-biology pilot.

Run 2, build the wide response matrix: completed for the same limited pilot.

For this historical pilot, full all-subject MMLU was not complete. The current
active evidence state is different: the reconciled HELM MMLU wide panel has 39
models over 14,042 items and clears the active panel-size gate.

## MMLU-Redux

Historical pilot note: at the time of this report, MMLU-Redux validation had
not been run for the limited pilot.

Current reconciled status: MMLU-Redux validation artifacts now exist for the
active 39-model HELM MMLU wide panel, but the result remains weak/negative under
structural alignment. Direct/hash MMLU-Redux alignment is not confirmed, and no
detection-success claim is allowed.

Current reference artifacts:

- `results/mmlu/redux_validation/metrics.json`
- `MMLU_REDUX_WEAK_SIGNAL_DIAGNOSIS.md`
- `MMLU_REDUX_SUBJECT_NORMALIZED_VALIDATION_REPORT.md`
- `MMLU_EVIDENCE_GATE_REPORT.md`

## Timings

- Install `lm-eval`: 9.83s
- Install `accelerate`: 0.60s
- Smoke successful run: 47.25s
- Qwen 0.5B pilot run: 43.15s
- Qwen 1.5B pilot run: 183.82s
- TinyLlama 1.1B pilot run: 130.72s
- Final import: 0.42s
- Final matrix build: 0.38s

## Next Exact Command

If the next step is to run ValidEval diagnostics on this limited real matrix:

```bash
python3 -m valideval panel-validity \
  --matrix cache/mmlu/wide/matrix.csv \
  --output results/mmlu/panel_validity
```

For current MMLU-Redux status, use the reconciled evidence reports above rather
than this historical pilot report.
