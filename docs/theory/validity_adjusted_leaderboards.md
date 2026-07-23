# Diagnostic-Sensitive Leaderboards

Diagnostic-sensitive leaderboard views are sensitivity analyses. They do not
identify the true ranking and they do not replace the full validity profile.
Each view must be reported with its assumptions, confidence intervals or
missing-evidence warnings, and misuse cautions.

## Ranking Views

`python3 -m valideval leaderboard --benchmark toy_mcq --panel mock` writes:

- `ranking_views.json`
- `ranking_views.csv`
- `ranking_significance.json`
- `ranking_flips.json`
- `health_badges.json`
- dashboard and atlas exports

Implemented views:

- raw accuracy
- conservative bootstrap accuracy
- IRT latent ability
- reliability sensitivity score
- shortcut sensitivity view
- prompt-stable ranking
- extraction-robust ranking
- contamination-risk-aware view
- saturation-aware interpretation
- human-validated subset ranking

When evidence is missing, a view falls back to raw accuracy and records an
explicit warning rather than inventing measurements.

## Ranking Flips

The flip detector compares raw accuracy against IRT, reliability sensitivity,
shortcut sensitivity, prompt-stable, extraction-robust, contamination-aware, and
saturation-aware views. It also reports full-vs-repaired-subset flips when a
repair diff exists. Strict-vs-lenient scorer, judge A/B, and full-panel-vs-subset
panel comparisons are marked unavailable unless those artifacts exist.

## Significance

Ranking significance uses paired bootstrap resampling over benchmark items. It
reports pairwise model differences, probability model A beats model B under the
bootstrap protocol, rank distributions, top-k stability, and a
`do_not_overinterpret_within_points` warning.

## Registry, Atlas, Dashboard, Site

The audit registry records benchmark hash, panel, diagnostics, evidence profile,
report paths, certificate paths, ranking paths, creation date, and status.

The benchmark atlas compares dimensions separately: shortcut resistance, item
quality, reliability, contamination/provenance, saturation, power, human
validation, coverage, and evidence profile. It does not average these into a
single health score.

`python3 -m valideval site build` creates a static HTML/CSS/JSON site with
pages for home, benchmark atlas, audit registry, report cards, certificates,
ranking comparisons, item-forensics downloads, methodology, and misuse warnings.

## Audit Diff

`python3 -m valideval audit-diff old_dir new_dir` compares two audit artifact
directories by item count, diagnostic coverage, shortcut/reliability/IRT
changes, evidence profile, ranking changes when ranking views exist, and new or
resolved warnings. This is an artifact diff, not proof that validity improved or
declined.

## Health Badges

Health badges are per-dimension statuses only:

- shortcut resistance
- reliability
- item quality
- scoring stability
- saturation
- contamination risk
- coverage

There is intentionally no total badge or scalar score.
