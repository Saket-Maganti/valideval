# Release Notes

## V7 ICML 2027 maximum pre-execution build

V7 is a CPU-reproducible, GPU-ready research build. It provides a multidimensional claim-licensing
system, expanded uncertainty and dependency-aware analyses, a frozen controlled model-panel design,
secure artifact ingestion, deterministic release profiles, and the complete pre-execution handoff.

The release gate is `ICML2027_STRONG_PRE_EXECUTION_BUILD_PARTIAL`. The software and protocols are
ready for staged execution, but the scientific program is not complete. The frozen synthetic
acceptance gates failed; diagnostic inference produced no stable FDR-controlled discoveries; Study
H is null-sensitive; planned 0.01 effect power is below 0.80; and GPU, human, transport, and held-out
repair evidence remain blocked. These limitations are retained as results, not tuned away.

Use `VALID_EVAL_V7_FINAL_MAXIMUM_PRE_EXECUTION_HANDOFF.md` for the next action and
`VALID_EVAL_ICML2027_EXECUTION_PLAN.md` for the ordered CPU, GPU, and human run ledger.

## 0.2.1-neurips-evidence-pivot

This build prepares ValidEval for evidence-first NeurIPS work without running new model
generation. It adds local importers for published per-instance predictions, MMLU-Redux-style
external issue labels, panel-validity gates, wide-matrix IRT reports, and build-only paper/review
scaffolds.

Empirical claims remain blocked until the queued runs in `NEURIPS_FIX_PROMPTS_EXECUTION_ORDER.md`
are executed on real local artifacts.
