# MMLU Deep Diagnostic Value Report

Real input: `cache/mmlu/wide/matrix.csv`

Outputs were written to `results/mmlu/deep_diagnostic_value`. The active panel has 39 models, 14042 item columns, and 57 subjects. The median subject-rank range is 19.00; 37 models meet the severe threshold of rank range >= 10.

Claims allowed: subject-level ranking sensitivity is material under the stated thresholds; aggregate MMLU rankings can hide subject-level variation; diagnostics should be reported with uncertainty and subject-level profiles.

Claims blocked: MMLU is invalid; ValidEval detects item errors; subject rank sensitivity proves benchmark invalidity.

Final verdict: `MMLU_DEEP_FINDING_STRONG`.
