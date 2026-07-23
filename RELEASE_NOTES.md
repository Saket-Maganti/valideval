# Release Notes

## 0.2.1-neurips-evidence-pivot

This build prepares ValidEval for evidence-first NeurIPS work without running new model
generation. It adds local importers for published per-instance predictions, MMLU-Redux-style
external issue labels, panel-validity gates, wide-matrix IRT reports, and build-only paper/review
scaffolds.

Empirical claims remain blocked until the queued runs in `NEURIPS_FIX_PROMPTS_EXECUTION_ORDER.md`
are executed on real local artifacts.
