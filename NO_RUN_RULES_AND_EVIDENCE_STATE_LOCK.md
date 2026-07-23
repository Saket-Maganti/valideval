# No-Run Rules and Evidence-State Lock

## Summary

This file freezes the current no-run boundary for the ValidEval NeurIPS-facing build. It is a
build/fix/polish artifact only. It does not create, rerun, recompute, or upgrade evidence.

## Evidence states locked

| Evidence block | Locked state |
|---|---|
| Legacy controlled synthetic flaw detection | Demoted to wiring/sanity-check only; not independent diagnostic-validation evidence |
| Synthetic FPR/null controls | Demoted to legacy synthetic-generator sanity checks only |
| Cross-flaw specificity | WEAK |
| Held-out generator transfer | WEAK |
| Materiality | WEAK |
| Toy-only power | WEAK |
| Numeric calibration without confidence/logprob outputs | BLOCKED |
| Synthetic-to-real threshold validation | NOT_RUN |
| Decoupled synthetic diagnostic validation | RESULT_REQUIRED |
| Decoupled synthetic protocol guards | Build-only / dry-run-only; no evidence upgrade |
| Confirmatory synthetic follow-up | RESULT_REQUIRED |
| MMLU-Redux | Weak/negative external stress test |
| GPQA | Protocol/demo unless future wide-panel evidence exists |
| HELM MMLU panel | Real input exists; real-panel finding remains RESULT_REQUIRED |

## Forbidden commands

Do not run validation experiments, synthetic generation, model inference, downloads, metric
recomputation, threshold tuning, MMLU-Redux reruns, confirmatory cross-flaw or held-out runs, or
real-panel ranking analysis under this no-run pass.

## Allowed commands

Allowed work is static inspection, code scaffolding, dry-run or preflight commands, report/template
creation, claim hygiene, `ruff check .`, and targeted tests for newly added no-run code. Dry-run
manifests may report guard status, but those fields are not empirical evidence.

## Files created/modified

This lock is referenced by the README, claims ledger, paper claims, and limitations surfaces. Those
pointers do not change empirical status.

## Commands run

No empirical or metric-producing commands are authorized by this document.

## Recommendation

Treat every later real-panel, calibration, power/materiality, second-benchmark, and confirmatory
synthetic claim as `[RESULT REQUIRED]` until a matching local artifact exists and the claim ledger is
updated. Current synthetic AUCs are historical wiring/sanity-check artifacts only and remain demoted
pending a decoupled, flaw-agnostic harness.
