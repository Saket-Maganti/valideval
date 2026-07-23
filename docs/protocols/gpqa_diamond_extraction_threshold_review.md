# GPQA Diamond Extraction Threshold Review

Artifact class: **amended GPQA input-validation threshold review**.

This review contains no raw GPQA question text, no full raw model outputs, and no diagnostic interpretation.

## 1. Current Threshold

- Active amended primary variant: `full_answer_only_v2`
- Required extraction success threshold: 0.95
- Achieved extraction success: 0.941
- Extraction failures: 93 of 1584

## 2. Failure Causes

Sanitized failure analysis found no true parser-bug candidates. Failures are classified as model non-compliance or non-recoverable outputs under the amended answer-only instruction.

Failures by type:

- `ambiguous_multiple_letters`: 19
- `final_answer_missing`: 5
- `invalid_no_letter`: 67
- `refusal_or_uncertain`: 2

Failures by model:

- `llama3.2:1b`: 19
- `mistral:latest`: 73
- `qwen2.5:1.5b-instruct`: 1

## 3. Concentration

Failures are concentrated in a small subset of models, especially `mistral:latest`, with additional failures from `llama3.2:1b` and one from `qwen2.5:1.5b-instruct`.

## 4. Excluding Models

Dropping or replacing a non-compliant model is not justified unless a separate protocol rule is created before interpretation. No model was dropped in this phase.

## 5. Risks of Lowering Threshold

- Lowering the threshold after seeing extraction failures risks adapting the protocol to observed artifacts.
- A lower threshold could admit enough non-compliance to affect downstream diagnostic scheduling.
- Threshold changes should be formal, explicit, and separated from diagnostic interpretation.

## 6. Options

- Keep threshold and remain no-go.
- Formally amend the threshold with justification before any interpretation.
- Regenerate with an even stricter answer-only prompt if the protocol is amended again.
- Replace or drop a model only under pre-specified criteria.

## 7. Recommendation

Conservative recommendation: keep the 0.95 threshold and keep amended go/no-go as `no_go`. Do not lower the threshold in this phase.
