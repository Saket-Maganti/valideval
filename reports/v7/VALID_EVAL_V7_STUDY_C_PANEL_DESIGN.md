# ValidEval V7 Study C Panel Design

Build gate: `STUDY_C_FULL_EXECUTION_BUILD_READY`; evidence gate: `GPU_NOT_EXECUTED`.

| Panel | Models | Lineage families | Declared download |
|---|---:|---:|---:|
| s2_pilot_v7 | 8 | 7 | 29.6 GB |
| s3_scientific_v7 | 11 | 9 | 55.6 GB |
| s4_maximum_ceiling_v7 | 13 | 11 | 64.0 GB |
| s4_fallback_v7 | 11 | 9 | 55.6 GB |

S2 emphasizes public checkpoint loading and extraction across seven families. S3 is the minimum
scientific panel (11 models, 9 families). S4 adds gated Llama and Gemma families; its 11-model,
9-family public fallback was frozen before S3 and has exact alternative run configs. The
DeepSeek-R1-Qwen distill is marked as a hybrid and must be merged with Qwen in dependence
sensitivity. Every checkpoint and tokenizer is pinned to a 40-character commit and remote code is
disabled.

The 0.01 paired-difference planning power is only 0.081–
0.658 under declared correlation assumptions, below 0.80.
S2 must recalibrate power before confirmatory interpretation. Full primary-route runtime is an
uncalibrated 441–
1804 T4×2 hours; reserve
95 GB.

Benchmark portfolio decision: retain MMLU, GSM8K, and BBH. A fourth benchmark is deferred because
the current portfolio already spans knowledge, arithmetic reasoning, and diverse symbolic/logical
tasks, while the frozen maximum plan is already compute-heavy. Adding a benchmark without S2
calibration would increase cost more clearly than construct coverage.
