# GPQA Diamond Pre-Registration Deviations

This document records workflow deviations or secondary exploratory paths. It intentionally omits raw GPQA question text.

## Phase 23

### Scoring Parser Bugfix

- Classification: `scoring_parser_bugfix`
- Scope: GPQA MCQ extraction only.
- Change: clear final-answer patterns are parsed before broad first-letter matching, and multi-letter outputs without a robust final-answer cue are marked invalid/ambiguous.
- Reason: the previous extractor could miss clear final-answer forms or silently select the first isolated letter from an ambiguous response.
- Interpretation status: no diagnostic interpretation is allowed from this change alone.

### Secondary Prompt-Compliance Path

- Classification: `secondary_exploratory_extraction_compliance`
- Prompt file: `configs/prompts/gpqa/full_answer_only_v2.yaml`
- Scope: small answer-format compliance reruns only.
- Status: not part of the preregistered primary prompt-variant matrices.
- Rule: do not mix v2 outputs with preregistered `full`, `question_only`, `choices_only`, `randomized_choices`, or `answer_letter_only` matrices.

## Phase 24

### Answer-Only v2 Full Compliance Test

- Classification: `secondary_exploratory_extraction_compliance`
- Scope: five-model local Ollama extraction-compliance test.
- Output directory: `local_outputs/gpqa/full_answer_only_v2/`
- Matrix: `cache/gpqa_diamond/gpqa_minimal_open_local/matrix_full_answer_only_v2.csv`
- Status: separate exploratory path only.
- Result status: v2 crossed the extraction threshold in the input-validation workflow, while primary `full` remained below threshold.
- Amendment recommendation: before using v2 as a primary audit prompt, create a formal preregistration amendment and rerun under the amended protocol.
- Interpretation status: no GPQA diagnostics were interpreted from this result.

## Phase 25

### Formal Amended v2 Protocol

- Classification: `formal_preregistration_amendment`
- Amended preregistration: `docs/protocols/gpqa_diamond_preregistration_amended_v2.md`
- Amended audit config: `configs/audits/gpqa_diamond_amended_v2.yaml`
- Amended primary full variant: `full_answer_only_v2`
- Original `full` status: archived protocol-development artifact only.
- Output status: amended v2 generated, scored, aligned, and matrix-built for 8 local models.
- Go/no-go status: `no_go`.
- Blocker: amended v2 extraction success 0.941 versus threshold 0.95.
- Interpretation status: no GPQA diagnostics were interpreted.

## Phase 26

### Amended v2 Extraction Failure Review

- Classification: `extraction_failure_review_no_parser_change`
- Scope: amended `full_answer_only_v2` outputs for 8 local models.
- Failure analysis: sanitized output-pattern review only; no raw GPQA question text or full raw outputs were recorded.
- Parser bug candidates: 0.
- Extractor change: none.
- Threshold review: `docs/protocols/gpqa_diamond_extraction_threshold_review.md`.
- Go/no-go status: `no_go`.
- Interpretation status: no GPQA diagnostics were interpreted.

## Phase 27

### Extraction-Compliance Decision and Replacement Panel

- Classification: `formal_extraction_compliance_decision`
- Decision memo: `docs/protocols/gpqa_diamond_amended_v2_extraction_compliance_decision.md`
- Compliance config: `configs/audits/gpqa_diamond_amended_v2_compliance.yaml`
- Compliant panel: `configs/panels/gpqa_minimal_open_local_amended_v2_compliant.yaml`
- Decision: keep the 0.95 extraction threshold; do not lower it.
- Rule: model eligibility is based only on `full_answer_only_v2` extraction success under the frozen extractor, with no item dropping and no answer-label modification.
- Non-compliant original models: `llama3.2:1b`, `mistral:latest`.
- Replacement models: `qwen2.5:latest`, `mistral:7b-instruct-q5_K_M`.
- Go/no-go status for compliant panel: `go`.
- Dry-run-real status: ready shell only.
- Interpretation status: no GPQA diagnostics were interpreted.

## Phase 29

### Amended v2 Non-Full Answer-Only Prompt Variants

- Classification: `formal_non_full_extraction_compliance_amendment`
- Scope: compliant-panel GPQA non-full prompt variants only.
- Primary non-full status: original `question_only`, `choices_only`, `randomized_choices`, and `answer_letter_only` outputs remain separate protocol-development artifacts.
- Reason: extraction compliance checks on completed compliant-model primary non-full outputs showed that several variants were below the 0.95 success threshold under the frozen extractor. The issue is treated as prompt-output extractability, not as a GPQA validity finding.
- Replacement variants:
  - `question_only` -> `question_only_answer_only_v2`
  - `choices_only` -> `choices_only_answer_only_v2`
  - `randomized_choices` -> `randomized_choices_answer_only_v2`
  - `answer_letter_only` -> `answer_letter_only_v2`
- Rule: do not mix original non-full outputs with amended non-full outputs in one aggregate or matrix.
- Interpretation status: no shortcut, prompt-sensitivity, reliability, or distractor-quality diagnostics were interpreted before this amendment.
