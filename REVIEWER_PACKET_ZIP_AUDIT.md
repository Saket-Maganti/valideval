# Reviewer Packet ZIP Audit

## 1. Executive Summary

The reviewer packet ZIP was rebuilt after the prompt-03-through-14 artifact updates. It includes source, configs, tests, paper draft/PDF, paper tables/figures, claim ledgers, result reports, Kaggle build instructions, and reviewer guidance. It excludes raw/cache artifacts, raw HELM/MMLU dumps, `results/mmlu/`, JSONL files, large CSVs, and ZIP files.

Final verdict: `REVIEWER_ZIP_READY`

## 2. ZIP Path

```text
dist/valideval_reviewer_packet.zip
```

SHA-256:

```text
da05f2d1f9225f643be4c52a17ccfec6fbaae66e7cc9b37971f6eb157e5d509f
```

## 3. ZIP Size

- Compressed size: 1,463,606 bytes.
- File count: 587.

## 4. Included Evidence Reports

Confirmed present:

- `VALID_EVAL_EVIDENCE_RECONCILIATION_AUDIT.md`
- `CLAIMS_AND_STORY_SYNC_AUDIT.md`
- `ARTIFACT_MANIFEST_FOR_PAPER.md`
- `MMLU_REAL_PANEL_CORE_RUN_REPORT.md`
- `MMLU_REDUX_DIRECT_ALIGNMENT_VALIDATION_REPORT.md`
- `MMLU_IRT_PSYCHOMETRIC_RUN_REPORT.md`
- `MMLU_RANKING_DISAGREEMENT_BASELINES_REPORT.md`
- `DECOUPLED_SYNTHETIC_EXECUTION_REPORT.md`
- `SECOND_BENCHMARK_RUN_REPORT.md`
- `KAGGLE_NOTEBOOK_BUILD_REPORT.md`
- `KAGGLE_OUTPUT_IMPORT_AND_VALIDATION_REPORT.md`
- `PAPER_REWRITE_AND_COMPILE_REPORT.md`
- `paper/main.pdf`
- `kaggle/valideval_lm_eval_panel_runner.ipynb`

The Kaggle package ZIP itself is excluded, as intended.

## 5. Excluded Files Confirmed Absent

Checked absent:

- `cache/mmlu/wide/predictions.jsonl`
- `data/external/mmlu/prediction_details_wide.jsonl`
- `results/mmlu/panel_validity/panel_validity.json`
- `kaggle/valideval_kaggle_panel_package.zip`
- all entries under `cache/`
- all entries under `data/external/`
- all entries under `results/mmlu/`
- all `.jsonl` entries
- all `.zip` entries

Raw/cache artifact check result: pass.

## 6. Commands Run

```bash
ruff check .
python3 -m pytest -q tests/test_make_reviewer_packet.py
python3 scripts/make_reviewer_packet.py
```

Structured ZIP inspection was performed with Python's standard `zipfile` module.

## 7. Evidence State Check

Packaging did not upgrade evidence states:

- active MMLU panel: 39-model HELM wide matrix, supported.
- 3-model MMLU files: historical/provenance only.
- real-panel ranking/disagreement: artifact-backed for active MMLU panel.
- proxy IRT: supported proxy diagnostics.
- full 2PL: `RESULT_REQUIRED`.
- MMLU-Redux direct/hash alignment: blocked/not confirmed.
- MMLU-Redux structural validation: weak/negative.
- decoupled synthetic validation: blocked/`RESULT_REQUIRED`.
- second-benchmark evidence: `RESULT_REQUIRED`.
- Kaggle outputs: absent/import blocked.
- NeurIPS readiness: blocked.

## 8. Final Verdict

`REVIEWER_ZIP_READY`
