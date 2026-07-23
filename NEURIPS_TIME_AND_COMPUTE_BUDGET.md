# NeurIPS Time And Compute Budget

## Build Completed In This Prep Pass

- Importers, validation scaffolds, panel-validity checks, IRT wrappers, stats check, fixtures, and
  documentation were built without executing real benchmark runs.

## Runs Still Needed

| Run | Command | Expected CPU time | GPU |
|---|---|---:|---|
| Import MMLU published details | `python3 -m valideval import-published-details ...` | 10-90 min | no |
| Build MMLU wide matrix | `python3 -m valideval matrix-from-wide-predictions ...` | 10-60 min | no |
| Import MMLU-Redux labels | `python3 -m valideval import-ground-truth ...` | 5-20 min | no |
| Panel validity | `python3 -m valideval panel-validity ...` | 5-30 min | no |
| MMLU-Redux validation | `python3 -m valideval mmlu-redux-validation ...` | 30 min-4 hr | no |
| Cross-flaw validation | `python3 -m valideval validate-diagnostics-cross-flaw ...` | 30-90 min | no |
| Held-out validation | `python3 -m valideval validate-diagnostics-heldout ...` | 10-60 min | no |
| Wide IRT | `python3 -m valideval fit-irt ...` | 30 min-4 hr | optional |
| Final readiness | `python3 -m valideval neurips-readiness --strict ...` | 5-30 min | no |

The expensive path is large local-file processing, not paid APIs or Codex-driven generation.
