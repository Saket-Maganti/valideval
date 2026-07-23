# ValidEval V5 Initial State Freeze

Recorded before V5 implementation on 2026-07-15 (Asia/Kolkata). This is the immutable
comparison point for this pass; later forensic reports describe the post-repair tree.

## Repository state

- Repository root: `/Users/saketmaganti/Projects/Valideval`
- Git: unborn `master` branch, no commit, no remote, and therefore no tracked-file diff base
- Initial working-tree inventory: 3,585 untracked files and 2,724 ignored files
- Initial disk footprint: approximately 2.1 GB
- Python: 3.11.9
- Real V5 Kaggle output directories: absent

Because Git has no first commit, this pass cannot truthfully classify every touched path as
“added” versus “modified” from Git history. The repair changelog therefore reports a combined
pass-scope count and separately identifies known new V5 surfaces.

## Initial quality baseline

| Gate | Initial result |
|---|---|
| `python3 -m pytest -q` | 214 passed, 0 failed, 0 skipped, 2 pandas constant-input warnings, 9.30 s |
| `ruff check .` | pass |
| `ruff format --check .` | fail; 37 files required formatting |
| Clean V5 install | not yet executed |
| V5 type check | not yet configured |
| V5 paper build | absent |
| V5 release build | absent |

## Frozen primary inputs

| Input | SHA-256 |
|---|---|
| `data/external/mmlu/prediction_details_wide.jsonl` | `38485dc89aa44f44cd5f8078df246d76aad3570ce15295559fa0a72d6f9379c6` |
| `cache/mmlu/wide/predictions.jsonl` | `06e88501819f9ad3d7d5121f55adeaf89314f09d2c771559d9a7bed0a420dd54` |
| `cache/mmlu/wide/matrix.csv` | `f85a0a44f3203de2863d86bf13b2c81d8e934ae4c07b826193b5e93a3fc86e74` |

## Initial evidence boundary

- The public HELM-derived MMLU matrix existed, but V5 had not independently reconstructed it.
- The legacy rank-range threshold labeled effects “severe” without a defensible null/materiality
  calibration.
- The legacy diagnostic-family ablation reused accuracy-derived values for seven named families.
- MMLU-Redux linkage did not establish shared item identity.
- Study H aliases were mixed conceptually with a future controlled common panel.
- V4 importer/cross routing could pass without the V5 artifact-derived identity and integrity
  requirements.
- Existing notebooks assumed single-device paths and had no canonical T4x2 fixture-validated suite.

The V4 readiness statement is preserved historically in `FINAL_V4_PRE_EXECUTION_GATE.md`, now
marked `SUPERSEDED_BY_V5`.
