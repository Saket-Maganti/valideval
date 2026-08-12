# ValidEval V7 ICML Preregistration

Status: `FROZEN_BEFORE_S3` at tag `valideval-v7-confirmatory-freeze` (commit `08336a3948db69de931e7582650abbd2f6ae0a70`).

The frozen file is `configs/preregistration/icml2027_primary_v7.yaml` with SHA-256
`1d2242f7957f2617326bc91770f7b6efe2f137b6f3f5758a57b6b91649a99681`. It fixes the primary hypothesis,
negative-discrimination/rank/fragility diagnostics, S3 panel, MMLU/GSM8K/BBH portfolio, held-out
decision regret, 0.01 materiality threshold, claim policy, exclusions, missing-data rule, BH primary
and BY sensitivity, human precision endpoint, transport metric, and cross-fitted repair policy.

The confirmatory synthetic protocol is independently frozen with SHA-256
`a7f98b074b5059a9f0f9c1290b3284573e8c9f6723a8a2577b90a290268ef1f6`. Later code may fix implementation defects, but
any change to a frozen protocol requires a new version and cannot be described as the V7 primary
analysis.
