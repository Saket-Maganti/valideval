# GPQA v2 Extraction Failure Review

## 1. Executive Summary

The amended v2 extraction review found 93 failures out of 1584 predictions. No true parser-bug candidates were found, no extractor change was made, and amended go/no-go remains `no_go` because extraction success is 0.941 versus the 0.95 threshold.

## 2. Starting State

- GPQA Diamond item file is validated.
- Amended primary prompt: `full_answer_only_v2`.
- Model panel: 8 local Ollama models.
- Alignment and matrix coverage passed before this review.
- No diagnostics had been interpreted.

## 3. Failure Analysis Method

Failures were classified using raw v2 output files and scored prediction metadata, but only sanitized pattern labels and item IDs were written to reports.

## 4. Failure Counts by Model

- `llama3.2:1b`: 19
- `mistral:latest`: 73
- `qwen2.5:1.5b-instruct`: 1

## 5. Failure Counts by Pattern

- JSON-like response without clear answer field: 1
- contains multiple option letters with no final marker: 19
- short response with no extractable option letter: 8
- text response with no extractable option letter: 63
- uncertain/refusal-style response with no extractable letter: 2

## 6. Parser Bug Candidates

Parser bug candidates found: 0

No parser fix was justified.

## 7. Genuine Model Non-Compliance

Genuine model non-compliance or non-recoverable failures: 93

## 8. Extractor Changes

No extractor changes were made. No prediction files were backed up or re-scored because no parser bug was found.

## 9. Before/After Extraction Success

- Before review: 0.941
- After review: 0.941
- Parser changed: false

## 10. Alignment and Matrix Status

- Alignment: `pass`
- Model count: 8
- Prediction count: 1584
- Matrix: `cache/gpqa_diamond/gpqa_minimal_open_local/matrix_full_answer_only_v2.csv`

## 11. Threshold Review

Created `docs/protocols/gpqa_diamond_extraction_threshold_review.md`. Recommendation: keep the 0.95 threshold and remain no-go unless a separate formal threshold amendment is made before interpretation.

## 12. Amended Go/No-Go Result

Amended go/no-go: `no_go`

Blocked checks:

- `extraction_success_threshold_met`: {'success_rate': 0.9412878787878788, 'threshold': 0.95}

## 13. Dry-Run-Real Result

Dry-run-real was not run because amended go/no-go returned `no_go`.

## 14. Deviations Log

Phase 26 records a no-parser-change extraction review. No `scoring_parser_bugfix_v2` was applied.

## 15. Do-Not-Claim List

- Do not claim any GPQA validity finding.
- Do not claim benchmark shortcuts, contamination, saturation, item-quality, or model-ranking evidence.
- Do not interpret diagnostics while amended go/no-go is `no_go`.
- Do not lower the threshold silently.

## 16. Next Commands

```bash
python3 -m valideval gpqa-go-no-go --benchmark gpqa_diamond --items data/gpqa/gpqa_diamond.jsonl --panel gpqa_minimal_open_local --config configs/audits/gpqa_diamond_amended_v2.yaml
```

## Phase 27 Update

The Phase 26 conclusion was preserved: no parser bug was found and the extractor was not changed. Phase 27 kept the 0.95 threshold and created an extraction-compliance decision memo rather than lowering the threshold.

A separate compliant preliminary panel was created under `gpqa_minimal_open_local_amended_v2_compliant`. `llama3.2:1b` and `mistral:latest` remain archived as non-compliant under extraction-only criteria; they were not deleted. Replacement outputs were generated for `qwen2.5:latest` and `mistral:7b-instruct-q5_K_M`.

Compliant-panel amended v2 go/no-go is `go`, and dry-run-real completed without diagnostic interpretation.
