# GPQA Auto Prep and Input Validation Report

## 1. Executive Summary

GPQA Diamond was acquired from the official GPQA GitHub repository, exported to `data/gpqa/gpqa_diamond.jsonl`, and validated successfully.

The real audit remains **no-go** because `gpqa_open_local` has no available real local/open models, cached prediction files, or matrices. A five-item smoke workflow was run with `gpqa_smoke_local`; those outputs are workflow validation only and are not scientific evidence.

Phase 20 confirmed the same real-output blocker. A preliminary Ollama-backed panel config, `configs/panels/gpqa_minimal_open_local.yaml`, was added for future local workflow validation only.

No raw GPQA question text is included in this report. No diagnostics were interpreted.

## 2. Data Discovery

- Expected item file: present at `data/gpqa/gpqa_diamond.jsonl`
- Official repo clone: `data/raw/gpqa_official_repo/`
- Official extracted archive: `data/raw/gpqa_official/`
- Official source file: `data/raw/gpqa_official/dataset/gpqa_diamond.csv`
- Local smoke outputs: present under `local_outputs/gpqa/full/`
- Real open/local cache: no files under `cache/gpqa_diamond/gpqa_open_local/`

## 3. GPQA Export Status

Status: **passed**.

- Source: official GitHub archive file `gpqa_diamond.csv`
- Output: `data/gpqa/gpqa_diamond.jsonl`
- Item count: 198
- ValidEval stable file hash: `bd6f79c7b1b460564ae6bcec2afb86756b0071c809b042bc7613cb1896f8e88c`
- Raw question text in export report: no

## 4. Item Validation Status

Status: **passed**.

- Unique item IDs: 198
- Fixture-like items: 0
- Fatal errors: 0
- Duplicate-choice warning items: 3
- Question/answer text-overlap warning items: 8

Warnings are item-ID-only and are not diagnostic interpretations.

## 5. Panel Readiness

`gpqa_open_local`:

- Configured models/baselines: 10
- Available real/cached models: 0
- Status: partial_or_blocked
- Recommended action: provide cached outputs or configure local/open runners

`gpqa_smoke_local`:

- Configured mock models: 2
- Available mock models: 2
- Status: ready
- Scientific status: smoke-only, not evidence

## 6. Existing Output Discovery

After smoke generation:

- `local_outputs/gpqa/full/always_a.jsonl`: 5 rows, smoke-only
- `local_outputs/gpqa/full/context_aware.jsonl`: 5 rows, smoke-only

No real `gpqa_open_local` output files were discovered.

Phase 20 discovery again found only smoke/mock files and excluded them from real audit preparation.

## 7. Output Generation Status

Real output generation: **not run** because no real local/open models or cached runners are available.

Smoke generation: **run** for workflow validation only:

```bash
python3 -m valideval generate-outputs --benchmark gpqa_diamond --items data/gpqa/gpqa_diamond.jsonl --panel gpqa_smoke_local --prompt-variant full --limit-items 5 --output-dir local_outputs/gpqa/full
```

## 8. Scoring/Import Status

Smoke raw outputs were scored into the smoke cache only:

- `cache/gpqa_diamond/gpqa_smoke_local/always_a_full_predictions.jsonl`
- `cache/gpqa_diamond/gpqa_smoke_local/context_aware_full_predictions.jsonl`

No real `gpqa_open_local` predictions were scored or imported.

Phase 20 did not score or import real outputs because none were present.

## 9. Extraction Audit Status

Smoke extraction audits passed for the two five-row raw-output files. These audits only validate extractor plumbing on smoke outputs.

No extraction audit was run on real open/local outputs because none exist.

## 10. Alignment Status

Real alignment was not run because there are no real `gpqa_open_local` prediction files.

## 11. Matrix Status

No real matrices were built. Matrices should only be built from validated real prediction files.

Missing real matrices:

- `cache/gpqa_diamond/gpqa_open_local/matrix_full.csv`
- `cache/gpqa_diamond/gpqa_open_local/matrix_question_only.csv`
- `cache/gpqa_diamond/gpqa_open_local/matrix_choices_only.csv`
- `cache/gpqa_diamond/gpqa_open_local/matrix_randomized_choices.csv`
- `cache/gpqa_diamond/gpqa_open_local/matrix_answer_letter_only.csv`

## 12. Prompt Variant Completeness

Status: **blocked** for `gpqa_open_local`.

Missing prediction and matrix variants:

- `full`
- `question_only`
- `choices_only`
- `randomized_choices`
- `answer_letter_only`

## 13. Audit Manifest Status

Manifest generated:

- `results/gpqa_diamond/input_validation/audit_manifest.json`

The manifest includes the validated item-file hash, config hashes, and prompt-template hashes. It has no real prediction or matrix hashes because no real output artifacts exist.

## 14. Go/No-Go Result

Result: **no_go**.

Passing checks:

- real GPQA JSONL valid
- no fixture data mixed
- prompt templates present/frozen
- pre-registration file exists
- model panel config exists
- no scoring-rule deviation recorded

Blocked checks:

- required prompt variants present
- complete full-prompt matrix
- required model count met
- extraction success threshold met

## 15. Dry-Run-Real Result

Not run. Dry-run-real is only allowed after go/no-go passes.

## 16. Diagnostics Allowed

None for real GPQA interpretation.

## 17. Diagnostics Blocked

All real GPQA diagnostics remain blocked until real cached/open-local outputs and matrices are available:

- answer distribution
- distractor quality
- IRT/proxy item analysis
- reliability
- extraction robustness
- saturation
- shortcut
- prompt sensitivity

## 18. Deviations From Pre-Registration

No prompt templates or extraction/scoring rules were changed.

Input-validation behavior was adjusted before diagnostic interpretation: question/answer text overlap is now warning-only while metadata answer leakage remains fatal. This avoids blocking official GPQA items on a non-schema heuristic while still surfacing the item IDs for review.

## 19. Do-Not-Claim List

- Do not claim any GPQA Diamond validity finding.
- Do not claim shortcut, contamination, saturation, item-quality, or ranking evidence.
- Do not treat smoke/mock outputs as scientific evidence.
- Do not treat input-validation warnings as diagnostic results.
- Do not run or interpret real diagnostics until go/no-go passes.

## 20. Exact Next Commands

Check the real panel after adding cached outputs or configuring local runners:

```bash
python3 -m valideval check-panel --panel gpqa_open_local
```

Generate or import real full-prompt outputs:

```bash
python3 -m valideval generate-outputs --benchmark gpqa_diamond --items data/gpqa/gpqa_diamond.jsonl --panel gpqa_open_local --prompt-variant full --output-dir local_outputs/gpqa/full
```

Then score/import, build matrices, and rerun go/no-go:

```bash
python3 -m valideval score-outputs --benchmark gpqa_diamond --items data/gpqa/gpqa_diamond.jsonl --input <raw_output_file.jsonl> --output cache/gpqa_diamond/gpqa_open_local/predictions_full.jsonl --prompt-variant full
python3 -m valideval matrix-from-predictions --benchmark gpqa_diamond --panel gpqa_open_local --variant full
python3 -m valideval gpqa-go-no-go --benchmark gpqa_diamond --items data/gpqa/gpqa_diamond.jsonl --panel gpqa_open_local
```
