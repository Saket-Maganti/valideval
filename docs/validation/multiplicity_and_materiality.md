# Multiplicity And Materiality

Audits often inspect many items and many diagnostics. Without multiplicity control, some flags are expected by chance.

The validation harness implements:

- Benjamini-Hochberg false discovery rate control.
- Benjamini-Yekutieli correction.
- Bonferroni correction.
- Holm correction.
- Empirical p-values from null diagnostic scores.
- Expected false flags under clean/null synthetic runs.

Per-item flags include raw scores, empirical p-values when available, corrected q-values, effect sizes, and expected false-flag context.

Materiality is separate from detectability. A flaw can be statistically detectable but practically negligible. The first materiality rules distinguish:

- statistically detectable
- practically material
- ranking-changing
- decision-changing
- negligible
- uncalibrated

Examples:

- A shortcut is material when shortcut-only retention explains a meaningful fraction of full performance.
- A scoring artifact is material when extractor choice changes scores or model ordering.
- Saturation is material when top-model differences are smaller than uncertainty or too compressed to interpret.
- Redundancy is material when effective item count is far below raw item count.

These rules are configurable and should be preregistered before a serious audit.
