# ValidEval V5 Pre-Execution Gate

## Overall verdict

`PRE_EXECUTION_BUILD_PARTIAL`

This is a build verdict, not a paper-readiness verdict. The old V4 readiness gate did not
survive independent reproduction and scientific red-team review.

## Separate gates

| Gate | Verdict | Reason |
|---|---|---|
| Existing MMLU evidence | `EXISTING_MMLU_EVIDENCE_REPRODUCED_WITH_MAJOR_CAVEATS` | The 547,638-cell matrix is byte-for-byte reconstructed, but the severe-threshold and legacy ablation interpretations do not survive. |
| Leakage | `P0_LEAKAGE_REMAINS` | Code guards pass; full controlled overlap inputs and the BBH few-shot freeze are absent. |
| Model identity | `COMMON_PANEL_PARTIAL` | Five immutable checkpoints are frozen; S3 requires 32 models across at least eight families under the stated planning rule. |
| Statistical | `RANK_ANALYSIS_REQUIRES_REPAIR` | The 500/500 analysis is reproducible and null-sensitive; family-cluster/model bootstrap gaps remain. |
| Measurement | `MEASUREMENT_MODEL_PLAN_LIMITED` | The transparent decomposition is reproduced, but core psychometric assumptions and held-out validation remain blocked. |
| Redux | `REDUX_VALIDATION_RETIRED` | Zero of 370 Redux rows have confirmed identity under the available artifacts. |
| Notebook | `KAGGLE_T4X2_FIXTURE_VALIDATED` | All six notebooks execute fixture mode; non-fixture inference is not connected. |
| Importer | `IMPORTER_V5_ADVERSARIAL_VALIDATED` | Secure fixture imports and fail-closed V5 routing pass; no real ZIP was imported. |
| Cross-benchmark build | `CROSS_BENCHMARK_BUILD_PARTIAL` | Gates and analysis code exist; matrices, receipts, and fitted hierarchical interaction are absent. |
| Human protocol | `HUMAN_VALIDATION_PROTOCOL_PARTIAL` | Blinding/import/agreement components pass fixtures; sampling frame and integrated pilot remain blocked. |
| Synthetic protocol | `SYNTHETIC_PROTOCOL_PREFLIGHT_ONLY` | Freeze and isolation tests pass; confirmatory generators/grid are not implemented. |

## Exact next action

Do not launch a scientific Kaggle job yet. First freeze the BBH few-shot artifact and connect a
real, configuration-driven V5 benchmark runner to the three notebook stages while preserving the
tested manifest, scheduler, gold-isolation, resume, and packaging boundaries. Then rerun the full
local validation chain and perform only the five-checkpoint S1 engineering smoke.

Machine-readable source: `reports/v5/final_gates_v5.json`.
