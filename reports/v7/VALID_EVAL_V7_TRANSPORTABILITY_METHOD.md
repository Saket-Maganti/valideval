# ValidEval V7 Transportability Method

Build gate: `TRANSPORTABILITY_BUILD_READY`. Evidence gate: `BLOCKED`.

Six estimands are defined separately: score, ranking, flag, calibration, decision, and repair
transport. Random-effects pooling reports tau-squared, I-squared, confidence intervals, direction
reversals, leave-one-benchmark-out requirements, and leave-one-family-out requirements. Exact item
and model identity, held-out evaluation, at least three benchmarks, and at least five independent
families fail closed.

Current evidence remains blocked: No exact-model controlled cross-benchmark effects exist before GPU Study C. The MMLU→GSM8K, MMLU→BBH, and GSM8K→BBH
directions must be populated from exact-model Study C outputs. A blank schema is at
`results/v7/transport/transport_effects_template.csv`.
