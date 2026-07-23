# GPQA Real Input Validation Report

Artifact scope: **gpqa_real_audit_blocked**.

This report summarizes real-input validation status only. It does not interpret GPQA Diamond diagnostics, does not make benchmark-validity claims, and does not report model rankings.

## 1. Executive Summary

The real GPQA item file now exists and passes validation:

```text
data/gpqa/gpqa_diamond.jsonl
```

The real audit remains blocked because no `gpqa_open_local` real/cached prediction files or response matrices are available. A smoke-only five-item workflow was run with mock models to validate plumbing; it is not GPQA evidence.

Phase 20 confirmed that no real `gpqa_open_local` outputs are available. Ollama is installed but was not running, and no real model was pulled or generated in this pass.

## 2. Files Provided

- Official source repo: `data/raw/gpqa_official_repo/`
- Official extracted archive: `data/raw/gpqa_official/`
- Official Diamond CSV: `data/raw/gpqa_official/dataset/gpqa_diamond.csv`
- ValidEval JSONL export: `data/gpqa/gpqa_diamond.jsonl`
- Smoke raw outputs: `local_outputs/gpqa/full/always_a.jsonl`, `local_outputs/gpqa/full/context_aware.jsonl`
- Smoke scored outputs: `cache/gpqa_diamond/gpqa_smoke_local/`

No real `gpqa_open_local` prediction or matrix files were provided.

The new `configs/panels/gpqa_minimal_open_local.yaml` panel is available for preliminary Ollama-backed workflow validation only.

## 3. Export Attempt

Hugging Face acquisition was blocked by gated access. Official GitHub acquisition succeeded from:

```text
https://github.com/idavidrein/gpqa.git
```

The official archive was extracted locally and `gpqa_diamond.csv` was exported into ValidEval JSONL.

Artifacts:

- `results/gpqa_diamond/input_validation/export_report.md`
- `results/gpqa_diamond/input_validation/export_report.json`
- `GPQA_DATA_ACQUISITION_REPORT.md`

## 4. Benchmark Item Validation

Command status: passed.

Validation summary:

- Item count: 198
- Unique item count: 198
- Fixture-like items: 0
- Fatal validation errors: 0
- Duplicate-choice warnings: 3 item IDs
- Question/answer text-overlap warnings: 8 item IDs

Artifact:

- `results/gpqa_diamond/input_validation/item_validation.json`

## 5. Model Output Discovery

Real open/local outputs: none discovered.

Smoke outputs:

- `local_outputs/gpqa/full/always_a.jsonl`: 5 rows
- `local_outputs/gpqa/full/context_aware.jsonl`: 5 rows

Smoke outputs are workflow validation only.

## 6. Extraction Audit

Smoke extraction audits were run for both smoke raw output files and passed on the five generated rows.

No extraction audit was run for real open/local outputs because none exist.

## 7. Scored Prediction Import

No external scored outputs were imported.

Smoke raw outputs were scored locally into:

- `cache/gpqa_diamond/gpqa_smoke_local/always_a_full_predictions.jsonl`
- `cache/gpqa_diamond/gpqa_smoke_local/context_aware_full_predictions.jsonl`

## 8. Alignment Check

Not run for real `gpqa_open_local` because no real prediction files exist.

## 9. Matrix Build Status

No real matrices were built.

Phase 20 did not build matrices because no validated real prediction files exist.

Expected but missing:

- `cache/gpqa_diamond/gpqa_open_local/matrix_full.csv`
- `cache/gpqa_diamond/gpqa_open_local/matrix_question_only.csv`
- `cache/gpqa_diamond/gpqa_open_local/matrix_choices_only.csv`
- `cache/gpqa_diamond/gpqa_open_local/matrix_randomized_choices.csv`
- `cache/gpqa_diamond/gpqa_open_local/matrix_answer_letter_only.csv`

## 10. Prompt Variant Completeness

Status: blocked for `gpqa_open_local`.

Missing prediction and matrix variants:

- `full`
- `question_only`
- `choices_only`
- `randomized_choices`
- `answer_letter_only`

Artifact:

- `results/gpqa_diamond/input_validation/prompt_variant_completeness.json`

## 11. Audit Manifest

Generated:

- `results/gpqa_diamond/input_validation/audit_manifest.json`

The manifest records the validated item-file hash and configuration/prompt-template hashes. Real prediction and matrix hashes are empty because no real `gpqa_open_local` outputs exist.

## 12. Go/No-Go Status

Status: **no_go**.

The item file now passes, but the real audit remains blocked by missing predictions, matrices, model count, and extraction-success evidence.

## 13. Diagnostics Allowed

None. No real GPQA audit diagnostics should be interpreted until go/no-go passes.

## 14. Diagnostics Blocked

All planned GPQA real-audit diagnostics remain blocked, including:

- answer distribution
- distractor quality
- IRT/proxy item analysis
- reliability
- extraction robustness
- saturation
- shortcut
- prompt sensitivity

## 15. Real-Audit Readiness

Not ready.

Ready pieces:

- Official GPQA source acquired
- Local GPQA Diamond JSONL exported
- Item validation passed
- Prompt templates and pre-registration present
- Audit manifest generated

Blocked pieces:

- Real/cached `gpqa_open_local` outputs
- Complete prediction files
- Matrices
- Minimum real model count
- Go/no-go pass

## 16. Deviations From Pre-Registration

No prompt templates, scoring rules, diagnostic thresholds, or model-panel definitions were changed.

Input-validation behavior was adjusted before diagnostic interpretation: question/answer text overlap is warning-only while metadata answer leakage remains fatal.

## 17. Do-Not-Claim List

- Do not claim any GPQA Diamond validity findings.
- Do not claim shortcut, saturation, item-quality, contamination, or ranking evidence.
- Do not cite smoke outputs as real GPQA evidence.
- Do not treat this no-go input-validation run as an audit result.

## 18. Next Commands

Provide or generate real open/local outputs:

```bash
python3 -m valideval check-panel --panel gpqa_open_local
python3 -m valideval generate-outputs --benchmark gpqa_diamond --items data/gpqa/gpqa_diamond.jsonl --panel gpqa_open_local --prompt-variant full --output-dir local_outputs/gpqa/full
```

Then score/import, build matrices, and rerun go/no-go:

```bash
python3 -m valideval score-outputs --benchmark gpqa_diamond --items data/gpqa/gpqa_diamond.jsonl --input <raw_output_file.jsonl> --output cache/gpqa_diamond/gpqa_open_local/predictions_full.jsonl --prompt-variant full
python3 -m valideval matrix-from-predictions --benchmark gpqa_diamond --panel gpqa_open_local --variant full
python3 -m valideval gpqa-go-no-go --benchmark gpqa_diamond --items data/gpqa/gpqa_diamond.jsonl --panel gpqa_open_local
```
