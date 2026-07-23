# GPQA First Real Local Output Report

## 1. Executive Summary

Phase 21 reached success state A for preliminary workflow validation: Ollama ran locally, `qwen2.5:1.5b-instruct` generated full-prompt raw outputs for all 198 GPQA Diamond items, those outputs were scored, alignment passed with a one-model preliminary threshold, and `matrix_full.csv` was built for `gpqa_minimal_open_local`.

The run is **preliminary real local output generation**, not paper-grade evidence. Go/no-go remains `no_go`; no diagnostics were run or interpreted.

## 2. Item File Status

- Path: `data/gpqa/gpqa_diamond.jsonl`
- Validation status: pass
- Item count: 198
- Unique item count: 198
- File hash: `bd6f79c7b1b460564ae6bcec2afb86756b0071c809b042bc7613cb1896f8e88c`

## 3. Ollama Status

- Ollama CLI: available at `/opt/homebrew/bin/ollama`
- Ollama server: running during generation
- Runner: local Ollama HTTP API
- Paid or closed APIs used: no

## 4. Model Pull / Availability

- Minimal panel: `configs/panels/gpqa_minimal_open_local.yaml`
- Available model: `qwen2.5:1.5b-instruct`
- Panel readiness status: ready
- Cached prediction variants: full
- Cached matrix variants: full

## 5. Tiny Smoke Generation

- Command path: real Ollama/local runner, not mock
- Prompt variant: `full`
- Limit: 5 items
- Raw output file: `local_outputs/gpqa/full/qwen2.5_1.5b-instruct.jsonl`
- Status: completed and then resumed for the full run
- Use: workflow validation only

## 6. Full-Prompt Output Generation

- Raw output file: `local_outputs/gpqa/full/qwen2.5_1.5b-instruct.jsonl`
- Rows: 198
- Model ID: `qwen2.5:1.5b-instruct`
- Prompt variant: `full`
- Prompt template hash recorded by generator: `884eaabefec59a1c69c85a5b0257fe6bd270c925c17bb29c6f320697ff4387e7`
- Raw output hash: `444f956bd66ba4535d175841081c688404fce4b7fcf81904a56c2a6ba1bb10fe`

## 7. Scoring Status

- Per-model scored predictions: `cache/gpqa_diamond/gpqa_minimal_open_local/qwen2.5_1.5b-instruct_full_predictions.jsonl`
- Aggregate full predictions: `cache/gpqa_diamond/gpqa_minimal_open_local/predictions_full.jsonl`
- Prediction rows: 198
- Extraction failures during scoring: 21
- Scoring/extraction rule deviation: none

## 8. Extraction Audit

- Status: blocked
- Strict letter success rate: 0.520
- Lenient letter success rate: 0.894
- Invalid output count: 21
- Ambiguous output count: 21
- Extractor disagreement count: 1
- Pre-registered threshold met: no

Failure details are item IDs only in `results/gpqa_diamond/input_validation/extraction_audit_full.md`.

## 9. Alignment Status

- Alignment report: `results/gpqa_diamond/input_validation/alignment_report.json`
- Status with one-model preliminary threshold: pass
- Prediction count: 198
- Model count: 1
- Missing item IDs: 0
- Extra item IDs: 0
- Duplicate predictions: 0

## 10. Matrix Status

- Matrix path: `cache/gpqa_diamond/gpqa_minimal_open_local/matrix_full.csv`
- Matrix exists: yes
- Matrix hash: `0a2045d3e001eb3310bb25aa7d2db880363e1ba0e29c3bd43c6332e16b4c6ac9`
- Scope: preliminary minimal panel only

## 11. Prompt Variant Completeness

- Present prediction variants: full
- Present matrix variants: full
- Missing variants: answer_letter_only, choices_only, question_only, randomized_choices
- Status: blocked

## 12. Audit Manifest

- Manifest path: `results/gpqa_diamond/input_validation/audit_manifest.json`
- Raw output hash included: yes
- Prediction hash included: yes
- Matrix hash included: yes
- `no_results_interpreted`: yes

## 13. Go/No-Go Status

- Panel: `gpqa_minimal_open_local`
- Status: no_go
- Blocked checks: required_prompt_variants_present, required_model_count_met, extraction_success_threshold_met

## 14. Dry-Run-Real Status

Dry-run-real was not run because go/no-go is `no_go`.

## 15. Diagnostics Allowed Later

No diagnostics are allowed in this phase. A later phase may use the full matrix only after the relevant go/no-go policy is satisfied or explicitly scoped as preliminary workflow validation.

## 16. Diagnostics Blocked

- Prompt-variant diagnostics are blocked because four preregistered variants are missing.
- IRT/proxy psychometrics are blocked or severely limited because the minimal panel has one model.
- Saturation/top-model comparison is blocked because the panel is too small.
- Extraction robustness is blocked by the preregistered extraction threshold.
- Paper-grade `gpqa_open_local` audit remains blocked because `gpqa_open_local` still lacks real outputs/matrices.

## 17. Deviations From Pre-Registration

No prompt templates, scoring rules, or extraction rules were changed. The Ollama runner was bounded with a short generation limit and a longer request timeout to make local batch generation complete. The minimal panel was narrowed to the small local model for preliminary workflow validation only.

## 18. Do-Not-Claim List

- Do not claim any GPQA validity finding.
- Do not claim shortcut, contamination, saturation, or item-quality evidence.
- Do not treat this one-model minimal run as paper-grade evidence.
- Do not mix smoke/mock outputs with real local outputs.
- Do not interpret diagnostics until a later phase explicitly authorizes it.

## 19. Next Commands

```bash
python3 -m valideval generate-outputs \
  --benchmark gpqa_diamond \
  --items data/gpqa/gpqa_diamond.jsonl \
  --panel gpqa_minimal_open_local \
  --prompt-variant question_only \
  --output-dir local_outputs/gpqa/question_only
```

Or add more real local/open models, regenerate/import outputs, then rerun scoring, alignment, matrices, manifest, and go/no-go.

## Phase 22 Update

The preliminary panel was expanded to three real local Ollama models:

- `qwen2.5:1.5b-instruct`
- `qwen2.5:3b-instruct`
- `llama3.2:1b`

All five preregistered prompt variants now have real preliminary raw outputs, scored aggregate prediction files, and matrices under `cache/gpqa_diamond/gpqa_minimal_open_local/`.

Current `gpqa_minimal_open_local` go/no-go remains **no_go** because the configured model-count threshold is not met and full-prompt extraction success remains below the preregistered threshold. No diagnostics were interpreted.

## Phase 23 Update

`gpqa_minimal_open_local` now has five real local Ollama models configured. Full-prompt outputs, scored predictions, and `matrix_full.csv` have been refreshed for all five models.

Current state:

- Full-prompt aggregate predictions: 990 rows across 5 models.
- Other preregistered variants: 594 rows across the original 3 models.
- Go/no-go: **no_go**.
- Blockers: 5 models versus 8 required, and full-prompt extraction success 0.746 versus threshold 0.95.

No diagnostics were interpreted. This remains preliminary workflow validation only.
