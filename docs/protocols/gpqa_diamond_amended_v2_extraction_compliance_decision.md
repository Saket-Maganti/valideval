# GPQA Diamond Amended-v2 Extraction Compliance Decision

Artifact class: **amended GPQA extraction-compliance protocol decision**.

This decision memo contains no raw GPQA question text, no full raw model outputs, and no diagnostic interpretation.

## 1. Executive Summary

The amended-v2 primary path remains blocked by extraction compliance: 0.941 extraction success versus the 0.95 threshold. The selected decision is to keep the 0.95 threshold, avoid threshold lowering, and apply an extraction-compliance-only exclusion/replacement rule before any diagnostic interpretation.

## 2. Current Blocker

- Active prompt variant: `full_answer_only_v2`
- Current amended panel: `gpqa_minimal_open_local`
- Predictions: 1584
- Extraction failures: 93
- Extraction success: 0.941
- Required threshold: 0.95
- Current amended go/no-go: `no_go`

## 3. Evidence Available Before Diagnostic Interpretation

Available evidence is limited to input-validation artifacts: item validation, output coverage, extraction success, alignment, matrix readiness, and sanitized extraction-failure categories. No GPQA diagnostics have been interpreted.

## 4. Failure Distribution

Failures are concentrated in two non-compliant models:

- `mistral:latest`: 73 extraction failures
- `llama3.2:1b`: 19 extraction failures

One otherwise compliant model has a single extraction failure:

- `qwen2.5:1.5b-instruct`: 1 extraction failure

## 5. Option A: Keep Threshold and Remain No-Go

This is the most conservative stopping option. It avoids post hoc threshold changes but does not attempt to recover a usable preliminary panel.

## 6. Option B: Lower Threshold

Lowering the threshold after observing failures risks adapting the protocol to observed artifacts. This option is rejected for this phase. Any threshold change would require a separate formal amendment before interpretation.

## 7. Option C: Regenerate Same Models With Stricter Prompt

The amended prompt already instructs models to return exactly one letter. Regenerating the same non-compliant models with another prompt would require a new prompt amendment and could still fail. This option is not selected in this phase.

## 8. Option D: Exclude/Replace Non-Compliant Models Under Pre-Specified Criteria

This option treats extraction compliance as an input/output validity requirement only. It preserves all original outputs, excludes only models that fail the compliance rule, adds replacement local/open models when feasible, and reruns validation before any interpretation.

## 9. Selected Decision

Selected decision: keep the 0.95 threshold and apply extraction-compliance-only exclusion/replacement. This is not performance filtering and does not use accuracy, item diagnostics, model rankings, or GPQA validity evidence.

## 10. Model Compliance Rule

A model is eligible for the amended-v2 primary panel only if its `full_answer_only_v2` extraction success is at least 0.95 on GPQA Diamond under the frozen extractor, with no item dropping and no answer-label modification. The aggregate panel extraction success must also be at least 0.95.

## 11. Models Flagged by Compliance Rule

Flagged as non-compliant:

- `llama3.2:1b`
- `mistral:latest`

Retained from the original panel:

- `qwen2.5:1.5b-instruct`
- `qwen2.5:3b-instruct`
- `llama3.2:3b`
- `gemma2:2b`
- `qwen2.5:7b-instruct`
- `llama3:latest`

## 12. Replacement Model Plan

Attempted practical replacement search:

- Prefer small or medium local/open Ollama models.
- Do not use paid or closed-model APIs.
- Do not force oversized models when local resources are unsuitable.

Selected replacement attempt:

- `qwen2.5:latest`
- `mistral:7b-instruct-q5_K_M`

`phi3.5:3.8b` was attempted as a pull candidate but was stopped because the pull became impractically slow for this phase.

## 13. What Was Not Used for This Decision

- Model accuracy was not used.
- GPQA diagnostic outputs were not used.
- Item-level diagnostic flags were not used.
- Model rankings were not used.
- Benchmark-validity claims were not used.

## 14. Risks

- Replacement models may also fail extraction compliance.
- The compliant panel is preliminary and local, not paper-grade.
- Exclusion/replacement must remain documented as input/output compliance, not model-performance filtering.
- Any future threshold amendment must be separate and explicit.

## 15. Reproduction Commands

```bash
python3 -m valideval generate-outputs --benchmark gpqa_diamond --items data/gpqa/gpqa_diamond.jsonl --panel gpqa_minimal_open_local_amended_v2_compliant --prompt-variant full_answer_only_v2 --output-dir local_outputs/gpqa/full_answer_only_v2
python3 -m valideval matrix-from-predictions --benchmark gpqa_diamond --panel gpqa_minimal_open_local_amended_v2_compliant --variant full_answer_only_v2
python3 -m valideval gpqa-go-no-go --benchmark gpqa_diamond --items data/gpqa/gpqa_diamond.jsonl --panel gpqa_minimal_open_local_amended_v2_compliant --config configs/audits/gpqa_diamond_amended_v2.yaml
```

## 16. Deviations Log

This decision adds an extraction-compliance-only replacement path for the amended-v2 preliminary panel. Original outputs are preserved and remain available for provenance.

## 17. Do-Not-Claim List

- Do not claim any GPQA validity finding.
- Do not claim model rankings or performance findings.
- Do not describe model exclusion as accuracy or performance filtering.
- Do not delete original non-compliant outputs.
- Do not interpret diagnostics until amended go/no-go passes.
