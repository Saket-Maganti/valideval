# MMLU-Redux V5 Identity Resolution

## Verdict

**Status: `REDUX_EXPLORATORY_ONLY`; confirmatory item identity is `BLOCKED`.** The V5 fail-closed
linker found 0 confirmed matches among 370 normalized MMLU-Redux issue rows. All 370 rows are
`UNMATCHED`. The existing item-level external-validation claim is therefore `RETIRED` from the
main paper.

Outputs:

- `results/mmlu_redux/linkage_v5.csv`
- `results/mmlu_redux/linkage_summary_v5.json`

## Available identity surfaces

The Redux artifact contains stable Redux row IDs, subject/config, source-row index, issue type,
and issue-source metadata. It does not contain a stable HELM item ID, canonical question text,
options, answer hash, or another shared content hash.

The reproduced HELM response artifact contains benchmark item IDs such as subject-scoped HELM
instance IDs, gold choices, subject, and model responses. It does not contain canonical question
text/options or a documented mapping from Redux source-row indices to HELM instance IDs.

Because the two sides lack a shared stable or content identity, positional alignment cannot be
promoted to confirmed identity.

## V5 matching order and safeguards

The linker implements the required fail-closed order:

1. stable upstream identifiers;
2. original source row/index candidate;
3. exact normalized question;
4. exact normalized options;
5. question + options + answer hash;
6. canonical subject + source index candidate;
7. reproducible token fuzzy candidate;
8. manual-review queue for ambiguous or high-confidence candidates.

Normalization covers Unicode NFKC, whitespace, HTML entities/tags, quote and dash variants,
selected LaTeX spacing, case folding, option-label stripping, and option-set hashing. Collision
buckets are detected. Output contains identifiers and hashes, never raw question text.

Confidence tiers are exactly `CONFIRMED_EXACT`, `CONFIRMED_CANONICAL`,
`HIGH_CONFIDENCE_MANUAL_REVIEW`, `AMBIGUOUS`, and `UNMATCHED`. Structural position is always
manual-review-only.

## Resolution counts

| Tier | Count |
|---|---:|
| `CONFIRMED_EXACT` | 0 |
| `CONFIRMED_CANONICAL` | 0 |
| `HIGH_CONFIDENCE_MANUAL_REVIEW` | 0 |
| `AMBIGUOUS` | 0 |
| `UNMATCHED` | 370 |

There were no emitted collisions and no structural-only candidate because the HELM artifact
does not expose a defensible common source-row mapping.

## Retirement of the old validation result

The archived validation artifact reports AUROC 0.53917, AUPRC 0.02891, and precision at 10 of
0.0 for one matrix anomaly score. These values are `VERIFIED_FROM_PRIMARY_ARTIFACT` as historical
file contents, but their item-level external-validation interpretation is `RETIRED` because
identity was not confirmed. Later structurally aligned issue-type analyses inherit the same
identity defect and remain exploratory.

The only defensible wording is:

> An unsuccessful exploratory linkage attempt did not establish shared item identity between
> the available MMLU-Redux labels and the historical HELM-derived response matrix.

No claim that a diagnostic predicts Redux flaws belongs in the main paper under the current
artifacts.

## Unlock condition

Obtain a lawfully usable canonical source containing question text/options or a documented
stable-ID mapping for both datasets. Rerun the sanitized linker, manually adjudicate ambiguous
candidates, and freeze confirmed matches before computing any metric. If identity becomes
confirmed, validation must use confirmed rows only with prevalence-aware baselines, AUROC,
AUPRC, preregistered precision at k, uncertainty, issue-type breakdowns, disputed-label
sensitivity, and simple heuristic baselines.

Until then: `REDUX_STATUS = RETIRED_UNCONFIRMED_IDENTITY`.
