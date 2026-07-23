# GPQA Diamond Audit Readiness

## Current Status

Official GPQA Diamond data is available locally and validates successfully.

- Item file: `data/gpqa/gpqa_diamond.jsonl`
- Item count: 198
- Item validation status: pass
- No raw GPQA item text is included in this readiness note.

## Phase 21 Update

The first preliminary real local output path has been exercised with Ollama:

- Panel: `gpqa_minimal_open_local`
- Model: `qwen2.5:1.5b-instruct`
- Prompt variant: `full`
- Raw outputs: `local_outputs/gpqa/full/qwen2.5_1.5b-instruct.jsonl`
- Scored predictions: `cache/gpqa_diamond/gpqa_minimal_open_local/predictions_full.jsonl`
- Matrix: `cache/gpqa_diamond/gpqa_minimal_open_local/matrix_full.csv`

This is preliminary workflow validation only. It is not paper-grade evidence and does not replace the preregistered `gpqa_open_local` panel.

## Go/No-Go

Current `gpqa_minimal_open_local` go/no-go status: **no_go**.

Blocked checks:

- `required_prompt_variants_present`
- `required_model_count_met`
- `extraction_success_threshold_met`


## Diagnostics

No GPQA diagnostics have been interpreted. Prompt-variant diagnostics, IRT/proxy psychometrics, saturation, extraction robustness, and paper-grade real-audit diagnostics remain blocked until the relevant go/no-go checks pass.

## Next Command

```bash
python3 -m valideval generate-outputs \
  --benchmark gpqa_diamond \
  --items data/gpqa/gpqa_diamond.jsonl \
  --panel gpqa_minimal_open_local \
  --prompt-variant question_only \
  --output-dir local_outputs/gpqa/question_only
```

## Phase 22 Update

`gpqa_minimal_open_local` now has three real local Ollama models with complete preliminary outputs and matrices for all preregistered variants:

- `full`
- `question_only`
- `choices_only`
- `randomized_choices`
- `answer_letter_only`

Current go/no-go remains **no_go**. Prompt-variant completeness and full-matrix presence now pass, but the configured model-count threshold and full-prompt extraction-success threshold remain blocked. No diagnostics have been interpreted.

## Updated Next Command

```bash
python3 -m valideval gpqa-go-no-go \
  --benchmark gpqa_diamond \
  --items data/gpqa/gpqa_diamond.jsonl \
  --panel gpqa_minimal_open_local
```

## Phase 23 Update

`gpqa_minimal_open_local` now has five real local Ollama models configured. Full-prompt outputs and `matrix_full.csv` cover all five models; the other preregistered variants remain complete for the original three models.

Current go/no-go remains **no_go**.

Blocked checks:

- `required_model_count_met`: 5 models available versus 8 required.
- `extraction_success_threshold_met`: full-prompt extraction success 0.746 versus threshold 0.95.

No diagnostics have been interpreted. A documented parser bugfix and an exploratory answer-only prompt-compliance probe exist, but the primary preregistered audit remains blocked until go/no-go passes or a later phase formally changes scope.

## Updated Next Command

```bash
python3 -m valideval generate-outputs \
  --benchmark gpqa_diamond \
  --items data/gpqa/gpqa_diamond.jsonl \
  --panel gpqa_minimal_open_local \
  --prompt-variant randomized_choices \
  --output-dir local_outputs/gpqa/randomized_choices
```

## Phase 24 Update

Current `gpqa_minimal_open_local` status:

- Full-prompt matrix: 8 models x 198 items.
- Non-full primary matrices: 5 models x 198 items.
- Exploratory `full_answer_only_v2` matrix: 5 models x 198 items.
- Go/no-go: **no_go**.
- Remaining blocker: primary full extraction success 0.721 versus threshold 0.95.

No diagnostics have been interpreted. A formal preregistration amendment is recommended before using `full_answer_only_v2` as any primary audit prompt.

## Phase 25 Update

A formal amended v2 preregistration and audit config now exist:

- `docs/protocols/gpqa_diamond_preregistration_amended_v2.md`
- `configs/audits/gpqa_diamond_amended_v2.yaml`

`full_answer_only_v2` outputs, scored predictions, and `matrix_full_answer_only_v2.csv` now cover all 8 models in `gpqa_minimal_open_local`. Amended alignment passes, but amended go/no-go remains **no_go** because amended v2 extraction success is 0.941 versus the 0.95 threshold.

No diagnostic interpretation has been run. Original `full` artifacts remain preserved as protocol-development evidence.

## Phase 26 Update

Amended v2 extraction failures were analyzed without exposing raw GPQA item text or full raw outputs. No true parser bugs were found, and the extractor was not changed.

Amended go/no-go remains **no_go** because `full_answer_only_v2` extraction success is 0.941 versus the 0.95 threshold. The conservative threshold review recommends keeping the threshold and remaining blocked unless a formal threshold amendment is created before interpretation.

## Phase 27 Update

A separate amended-v2 extraction-compliant preliminary panel now passes input-validation go/no-go:

- Panel: `gpqa_minimal_open_local_amended_v2_compliant`
- Primary variant: `full_answer_only_v2`
- Models: 8
- Predictions: 1584
- Extraction success: 0.994 versus threshold 0.95
- Matrix: `cache/gpqa_diamond/gpqa_minimal_open_local_amended_v2_compliant/matrix_full_answer_only_v2.csv`
- Go/no-go: **go**
- Dry-run-real: ready shell only, with no diagnostics interpreted

The original 8-model amended-v2 panel remains archived as a no-go protocol-development artifact. Shortcut and prompt-sensitivity diagnostics remain blocked until non-full variants have complete 8-model coverage.

## Phase 28 Update

The first preliminary amended-v2 audit ran from the compliant local panel cache.

- Panel: `gpqa_minimal_open_local_amended_v2_compliant`
- Primary variant: `full_answer_only_v2`
- Audit label: `preliminary amended-v2 local-model-only compliant-panel-only`
- Diagnostics run: `answer_distribution`, `irt`, `saturation`, `extraction_robustness`, `redundancy`, `ranking_uncertainty`, `power`, `data_forensics`
- Report card: `reportcards/gpqa_diamond_amended_v2_compliant_preliminary.md`
- Audit report: `GPQA_PRELIMINARY_AMENDED_V2_AUDIT_REPORT.md`
- Reviewer-risk: 0 static risks

Shortcut, prompt-sensitivity, and variant reliability diagnostics remain blocked until complete 8-model non-full coverage exists. This phase does not support broad GPQA validity claims.
