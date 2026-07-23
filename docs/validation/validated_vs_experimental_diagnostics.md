# Validated Vs Experimental Diagnostics

As of the current synthetic validation run, `validation_reports/diagnostic_validation_summary.md` is the source of truth.

Credible under the synthetic harness:

- shortcut / shortcut_signal
- answer_distribution / answer_length_artifact
- redundancy / redundancy
- irt / low_discrimination
- irt / negative_discrimination
- reliability / prompt_format_fragility
- extraction_robustness / extraction_ambiguity
- extraction_robustness / scoring_ambiguity
- saturation / too_easy_saturation
- saturation / too_hard_floor

Prototype-only:

- answer_distribution / label_imbalance
- distractor_quality / dead_distractors

Quarantined under this harness:

- None.

If a pairing is quarantined, it should not be used as a calibrated detector without more validation. It may still be useful as exploratory evidence if reported with limitations.

`irt / negative_discrimination` is credible only under the revised anchored synthetic protocol. The generator preserves clean ability-ordering items and uses an ordered synthetic model panel; a benchmark dominated by anti-correlated items remains difficult to orient from the response matrix alone.

The current validation results are synthetic detector-validation results only. They should not be described as findings about real benchmarks.
