# GPQA Amended v2 Protocol Report

## 1. Executive Summary

The GPQA preregistration was formally amended to adopt `full_answer_only_v2` as the amended primary full-prompt extraction-compliance path. Amended v2 outputs now exist for all 8 models in `gpqa_minimal_open_local`, and the amended v2 prediction aggregate and matrix were rebuilt. Amended go/no-go remains `no_go` because amended v2 extraction success is 0.941 versus the 0.95 threshold.

No GPQA diagnostic interpretation was performed.

## 2. Why Amendment Was Needed

The original primary `full` prompt did not meet the extraction threshold. This is recorded as an evaluation-protocol extractability issue, not a GPQA validity finding.

## 3. Original Primary Prompt Status

Original `full` artifacts are preserved and remain separate:

- `local_outputs/gpqa/full/`
- `cache/gpqa_diamond/gpqa_minimal_open_local/predictions_full.jsonl`
- `cache/gpqa_diamond/gpqa_minimal_open_local/matrix_full.csv`

The original full extraction success recorded by amended go/no-go is 0.721.

## 4. Exploratory v2 Evidence Before Amendment

Before amendment, `full_answer_only_v2` had five-model exploratory coverage and crossed the extraction threshold. No diagnostics were interpreted from that exploratory result.

## 5. Formal Amendment

Created:

- `docs/protocols/gpqa_diamond_preregistration_amended_v2.md`
- `configs/audits/gpqa_diamond_amended_v2.yaml`

The amendment states that v2 is adopted only for output extractability/compliance and does not change GPQA items, answer labels, or frozen extraction/scoring rules.

## 6. Amended Primary Prompt

Amended primary full path:

```text
configs/prompts/gpqa/full_answer_only_v2.yaml
```

Original `full` remains archived as protocol-development evidence.

## 7. Amended Output Generation

Generated or confirmed 198-row `full_answer_only_v2` raw files for all 8 local models:

- `qwen2.5:1.5b-instruct`
- `qwen2.5:3b-instruct`
- `llama3.2:1b`
- `llama3.2:3b`
- `gemma2:2b`
- `qwen2.5:7b-instruct`
- `mistral:latest`
- `llama3:latest`

## 8. Scoring and Extraction

Re-scored all 8 amended v2 files after backing up the previous 5 exploratory v2 prediction files.

Aggregate:

```text
cache/gpqa_diamond/gpqa_minimal_open_local/predictions_full_answer_only_v2.jsonl
```

Extraction summary:

- Predictions: 1584
- Models: 8
- Extraction success: 0.941
- Threshold: 0.95
- Invalid outputs: 93
- Ambiguous outputs: 19
- Threshold status: blocked

## 9. Alignment

Amended v2 alignment passed:

- 8 models
- 198 predictions per model
- no missing items
- no extra items
- no duplicate predictions
- no invalid labels

Extraction failures are counted but do not break schema alignment.

## 10. Matrix Status

Rebuilt amended v2 matrix:

```text
cache/gpqa_diamond/gpqa_minimal_open_local/matrix_full_answer_only_v2.csv
```

The original `matrix_full.csv` was not replaced.

## 11. Non-Full Variant Coverage

Non-full variants remain complete for 5 models, not all 8 models. Shortcut and prompt-sensitivity diagnostics remain blocked until non-full variants have complete 8-model coverage and pass input-validation checks.

## 12. Amended Manifest

Amended manifest was generated with:

```bash
python3 -m valideval audit-manifest --benchmark gpqa_diamond --items data/gpqa/gpqa_diamond.jsonl --panel gpqa_minimal_open_local --config configs/audits/gpqa_diamond_amended_v2.yaml
```

The manifest records hashes for the amended preregistration, amended config, v2 prompt, original prompt, v2 predictions, v2 matrix, panel config, and related validation artifacts.

## 13. Amended Go/No-Go Result

Amended go/no-go status: `no_go`.

Passing checks:

- valid GPQA JSONL
- no fixture data mixed
- amended prompt template exists
- amended preregistration exists
- panel config exists
- amended v2 prediction and matrix artifacts present
- complete amended full matrix
- required model count met: 8 of 8
- frozen extractor version recorded

Blocked check:

- `extraction_success_threshold_met`: 0.941 versus 0.95

## 14. Dry-Run-Real Status

Dry-run-real was not run because amended go/no-go returned `no_go`.

## 15. Diagnostics Allowed Later

No diagnostics are allowed for interpretation from this phase. A later phase may proceed only after amended go/no-go passes or the protocol is further amended before interpretation.

## 16. Diagnostics Blocked

- Amended primary full-path diagnostics are blocked by extraction threshold failure.
- Shortcut and prompt-sensitivity diagnostics are blocked by incomplete 8-model non-full coverage.
- Original `full` diagnostics are archived as protocol-development artifacts.
- Paper-grade claims remain blocked for this preliminary local panel.

## 17. Deviations Log

The deviations log now records Phase 25 formal adoption of v2 under amendment and the resulting amended go/no-go blocker.

## 18. Do-Not-Claim List

- Do not claim a GPQA validity finding.
- Do not claim v2 results are benchmark diagnostics.
- Do not claim shortcut, contamination, saturation, item-quality, or model-ranking evidence.
- Do not mix original `full` artifacts with amended v2 artifacts.
- Do not run interpreted diagnostics while go/no-go is `no_go`.

## 19. Next Commands

Primary blocker check:

```bash
python3 -m valideval gpqa-go-no-go --benchmark gpqa_diamond --items data/gpqa/gpqa_diamond.jsonl --panel gpqa_minimal_open_local --config configs/audits/gpqa_diamond_amended_v2.yaml
```

If further protocol work is desired, inspect amended v2 extraction failure patterns by model without exposing raw GPQA item text.

## Phase 26 Update

Sanitized amended v2 extraction failure analysis was completed:

- Failure count: 93 of 1584 predictions.
- Extraction success: 0.941 versus threshold 0.95.
- Parser bug candidates: 0.
- Extractor changes: none.
- Amended go/no-go: `no_go`.

The threshold review recommends keeping the 0.95 threshold and remaining blocked unless a separate formal threshold amendment is created before interpretation.

## Phase 27 Update

A formal extraction-compliance decision memo now exists at `docs/protocols/gpqa_diamond_amended_v2_extraction_compliance_decision.md`. The 0.95 extraction threshold was kept, and non-compliant models were excluded/replaced only under a pre-specified answer-extraction compliance rule.

New compliant panel: `gpqa_minimal_open_local_amended_v2_compliant`.

- Models: 8
- Amended v2 predictions: 1584
- Extraction success: 0.994
- Matrix: `cache/gpqa_diamond/gpqa_minimal_open_local_amended_v2_compliant/matrix_full_answer_only_v2.csv`
- Go/no-go: `go`
- Dry-run-real: ready shell only

No diagnostics were interpreted. Shortcut and prompt-sensitivity diagnostics remain blocked until non-full variants have complete 8-model coverage under the active protocol.

## Phase 28 Update

The amended-v2 compliant panel passed go/no-go and was used for the first preliminary local-model-only audit. The run used only the amended primary `full_answer_only_v2` matrix and did not use original `full`, non-compliant-panel, smoke, mock, paid API, or closed-model outputs.

Artifacts:

- Allowed diagnostics ledger: `results/gpqa_diamond/preliminary_amended_v2/allowed_diagnostics.json`
- Diagnostic summary: `results/gpqa_diamond/preliminary_amended_v2/diagnostic_summary.json`
- Preliminary report card: `reportcards/gpqa_diamond_amended_v2_compliant_preliminary.md`
- Interpretation-controlled report: `GPQA_PRELIMINARY_AMENDED_V2_AUDIT_REPORT.md`

This remains preliminary local-model-only evidence. Non-full prompt diagnostics remain blocked for primary interpretation.
