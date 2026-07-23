# Reframed Introduction Draft: Negative External Validation Result

Benchmarks are measurement instruments. Their scores are often reported as if they directly measure a claimed construct, yet benchmark validity can fail for reasons that ordinary accuracy reporting does not expose: artifacts in answer choices, prompt-format fragility, low item discrimination, saturation, scoring ambiguity, contamination, or mismatch between item content and the claimed ability.

ValidEval is designed around a conservative premise: validity diagnostics should not be trusted merely because they produce plausible-looking warnings. They must themselves be audited. The toolkit therefore reports a multidimensional validity profile and keeps claim states explicit, including `RESULT_REQUIRED`, weak, blocked, and protocol-scoped findings.

This revision demotes the legacy controlled synthetic harness. The current harness remains useful for wiring and sanity checks, but a code audit found that controlled model behavior branches on injected flaw metadata and that item-score readout can switch by diagnostic/flaw family. Current synthetic AUCs are therefore historical sanity-check artifacts, not independent diagnostic-validation evidence.

The strongest current empirical spine is instead a real external-validation stress test on public HELM MMLU predictions. Using a 39-model HELM MMLU panel, matrix-derived diagnostics do not robustly recover structurally aligned MMLU-Redux issue labels. The result is weak/negative under the current protocol, with structural rather than direct/hash-confirmed alignment and no detection-success claim.

This negative result motivates the central paper thesis: benchmark-validity diagnostics need external validation and claim gates before they are used to license benchmark-quality conclusions. A decoupled flaw-agnostic synthetic harness is specified as future work, but this no-run update does not execute validation, generate synthetic items, tune thresholds, or change empirical values.
