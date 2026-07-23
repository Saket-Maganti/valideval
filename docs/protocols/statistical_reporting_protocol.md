# Statistical Reporting Protocol

Validity evidence must be reported as a profile, not a scalar score.

## Required Reporting Elements

- Effect sizes where a diagnostic estimates a magnitude.
- Confidence intervals or bootstrap intervals when available.
- Paired comparisons for model-to-model differences on the same item set.
- Rank uncertainty and top-k stability for leaderboards.
- Multiple-comparison correction or a clear statement that analyses are exploratory.
- Benchmark selection criteria and exclusion rules.
- Model-panel sensitivity and seed sensitivity when the decision depends on rankings.
- Missing-diagnostics disclosure.
- Negative-result reporting, including diagnostics that found no local evidence.
- Corpus searched and corpus not searched for contamination/overlap claims.

## Language Standard

Use phrases like "evidence consistent with," "possible validity threat," and "under this protocol." Avoid claims that a diagnostic proves global validity, contamination, cleanliness, or a true ranking.

## Minimum Table Fields

- Benchmark ID and version/hash.
- Panel ID and model list.
- Diagnostic name/version.
- Assumptions.
- Point estimates.
- Confidence intervals or missing-CI reason.
- Warnings and limitations.
- Reproduction command.
