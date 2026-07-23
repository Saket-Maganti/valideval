# GPQA Real Output Preparation Report

## 1. Executive Summary

Phase 21 produced the first real local GPQA output artifact for the preliminary `gpqa_minimal_open_local` panel. The run generated and scored full-prompt outputs for all 198 GPQA Diamond items using local Ollama model `qwen2.5:1.5b-instruct`, then built `matrix_full.csv`.

This is preliminary workflow validation, not a paper-grade real audit. `gpqa_open_local` remains blocked. No diagnostics were run or interpreted.

## 2. Item File Status

- Path: `data/gpqa/gpqa_diamond.jsonl`
- Validation status: pass
- Item count: 198
- Hash: `bd6f79c7b1b460564ae6bcec2afb86756b0071c809b042bc7613cb1896f8e88c`

## 3. Panel Readiness

`gpqa_minimal_open_local`:

- Configured models: 1
- Available models: 1
- Cached prediction variants: full
- Cached matrix variants: full

`gpqa_open_local` remains the paper-grade/preregistered target and still needs real outputs.

## 4. Existing Output Discovery

Discovery report: `results/gpqa_diamond/input_validation/discovered_outputs.md`.

- Real minimal-panel raw files: 1
- Excluded smoke/mock files: 2

## 5. Output Generation Status

- Real local model: `qwen2.5:1.5b-instruct`
- Raw output rows: 198
- Raw output file: `local_outputs/gpqa/full/qwen2.5_1.5b-instruct.jsonl`
- Smoke/mock files remain excluded.

## 6. Scoring / Import Status

- Per-model scored predictions: `cache/gpqa_diamond/gpqa_minimal_open_local/qwen2.5_1.5b-instruct_full_predictions.jsonl`
- Aggregate predictions: `cache/gpqa_diamond/gpqa_minimal_open_local/predictions_full.jsonl`
- Prediction rows: 198

## 7. Extraction Audit

- Status: blocked
- Lenient extraction success rate: 0.894
- Invalid output count: 21
- Ambiguous output count: 21
- Threshold met: no

## 8. Alignment Validation

- Preliminary one-model alignment status: pass
- Missing item IDs: 0
- Extra item IDs: 0
- Duplicate predictions: 0

## 9. Matrix Build Status

- Full matrix: `cache/gpqa_diamond/gpqa_minimal_open_local/matrix_full.csv`
- Exists: yes

## 10. Prompt Variant Completeness

- Status: blocked
- Present variants: full
- Missing variants: answer_letter_only, choices_only, question_only, randomized_choices

## 11. Audit Manifest

Manifest refreshed at `results/gpqa_diamond/input_validation/audit_manifest.json` with item, raw output, prediction, matrix, config, prompt-template, pre-registration, and code hashes.

## 12. Go/No-Go Result

Status: **no_go**.

Blocked checks: required_prompt_variants_present, required_model_count_met, extraction_success_threshold_met.

## 13. Dry-Run-Real Result

Not run because go/no-go is `no_go`.

## 14. Diagnostics Allowed

None in this phase.

## 15. Diagnostics Blocked

- Prompt-variant diagnostics
- IRT/proxy psychometrics
- Saturation/top-model comparison
- Extraction robustness under preregistered threshold
- Paper-grade `gpqa_open_local` diagnostics

## 16. Deviations From Pre-Registration

No prompt, scoring, or extraction rule changes. The local Ollama runner was bounded for batch generation. The minimal panel remains explicitly preliminary.

## 17. Do-Not-Claim List

- Do not claim a GPQA validity finding.
- Do not treat one small model as a paper-grade panel.
- Do not mix smoke/mock outputs with real outputs.
- Do not interpret diagnostics in this phase.

## 18. Next Commands

```bash
python3 -m valideval validate-prompt-variants \
  --benchmark gpqa_diamond \
  --panel gpqa_minimal_open_local

python3 -m valideval gpqa-go-no-go \
  --benchmark gpqa_diamond \
  --items data/gpqa/gpqa_diamond.jsonl \
  --panel gpqa_minimal_open_local
```

## Phase 22 Update

The preliminary panel has been expanded from one to three real local Ollama models. All five preregistered prompt variants now have:

- 198 raw outputs per model
- per-model scored prediction files
- aggregate `predictions_<variant>.jsonl` files
- `matrix_<variant>.csv` files

Prompt variant completeness now passes for `gpqa_minimal_open_local`, but go/no-go remains **no_go** because the panel is below the configured model-count threshold and full-prompt extraction success remains below the preregistered threshold. Dry-run-real was not run.

## Phase 23 Update

The preliminary panel was expanded to five local Ollama models. Full-prompt raw outputs and scored predictions were generated for `llama3.2:3b` and `gemma2:2b`, then aggregate predictions and matrices were rebuilt.

- Full matrix: 5 models.
- Other primary matrices: 3 models.
- Prompt variant aggregate completeness: pass.
- Go/no-go: **no_go**.
- Blockers: model count 5 versus 8 required, and full-prompt extraction success 0.746 versus 0.95 required.

A parser bugfix and a separate exploratory `full_answer_only_v2` prompt-compliance probe were documented. No raw GPQA text is included here, and no diagnostics were interpreted.
