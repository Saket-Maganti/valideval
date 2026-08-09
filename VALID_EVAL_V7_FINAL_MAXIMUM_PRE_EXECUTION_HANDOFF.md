# ValidEval V7 Final Maximum Pre-Execution Handoff

Final gate: `ICML2027_STRONG_PRE_EXECUTION_BUILD_PARTIAL`.

The repository has a complete V7 claim-licensing implementation, frozen S2/S3/S4/S5 execution
contracts, 10 T4×2 notebooks, secure ingest-and-analyze routing, deterministic release profiles,
and CPU studies. It is not scientifically complete.

## Evidence gates

- Claim licensing: `CLAIM_LICENSING_METHOD_READY` (contract behavior only).
- Inferential diagnostics: `INFERENTIAL_DIAGNOSTICS_READY`; stable flags = 0.
- Study H: `STUDY_H_REPRODUCED_WITH_LIMITATIONS` because conclusions vary strongly across nulls.
- Generalizability: `GENERALIZABILITY_ANALYSIS_READY` with descriptive unbalanced components.
- Decision materiality: `DECISION_MATERIALITY_READY` on historical MMLU only.
- Benchmark influence: `BENCHMARK_INFLUENCE_READY`; winner-changing items = 0.
- Measurement regime: `MEASUREMENT_REGIME_STUDY_COMPLETE`; counts = {'CAUTION': 1, 'SUPPORTED': 16, 'UNIDENTIFIABLE': 1, 'UNRELIABLE': 1}.
- Synthetic execution: `SYNTHETIC_CONFIRMATORY_COMPLETE`; acceptance = `FROZEN_ACCEPTANCE_GATES_FAILED`.
- Transport build: `TRANSPORTABILITY_BUILD_READY`; evidence = `BLOCKED`.
- Human protocol: `HUMAN_CONFIRMATORY_PROTOCOL_READY`; labels not collected.

## Study C

S1, S2, S3, S4, and robustness infrastructure are ready to execute. S3/S4 scientific interpretation
is conditional on S1/S2 acceptance, exact family coverage, extraction reliability, and power
recalibration. Planning power for a 0.01 pairwise difference is
0.081–0.658; it does not
meet 0.80. GPU execution remains 441–
1804 uncalibrated T4×2 hours for the
primary route.

## Primary next action

Run the existing S1 controlled smoke, import all three ZIPs, then run S2 MMLU/GSM8K/BBH. Recalibrate
runtime, extraction, memory, and paired-difference power before authorizing S3. Do not tune the V7
synthetic readout and reuse its confirmatory label; any new detector is V8 exploratory until frozen.
