# Related Work Positioning Matrix

## Positioning sentence

ValidEval is not another leaderboard runner; it is a diagnostic-validation and claim-gating
framework for benchmark-validity diagnostics.

| Area | Examples | ValidEval positioning |
|---|---|---|
| Construct validity / psychometrics | Measurement validity, IRT, reliability | Uses measurement concepts to validate diagnostics before claims |
| Benchmark validity critique | Contamination, shortcuts, saturation | Turns threats into auditable diagnostic families |
| Evaluation harnesses | HELM, lm-eval-harness, OpenCompass, Inspect AI | Complements runners by auditing what benchmark scores support |
| Benchmark families | MMLU, MMLU-Redux, MMLU-Pro, GPQA, GSM8K, TruthfulQA | Treats benchmark evidence as protocol-scoped and claim-gated |
| Calibration and judge reliability | Confidence/logprob calibration, LLM-as-judge reliability | Blocks claims until required outputs and validation exist |

## Claims not made

ValidEval does not claim to be the first benchmark-validity toolkit, a replacement for existing
evaluation harnesses, validation for all diagnostics, or proof of real benchmark error detection.
