# CPU Max-Out Claim Policy

Generated from structured artifacts. It is an engineering/scientific audit record, not a final paper claim.

## Structured sources

- `results/final_cpu_maxout/claim_policy/selection_metrics.json`
- `results/final_cpu_maxout/claim_policy/confirmation_summary.json`

## Frozen result

`CLAIM_POLICY_CONFIRMATION_SUPPORTING_ONLY` with policy `NATIVE_BALANCED`. Across 36000 confirmation scenarios, false-license rate was 0.634% (Wilson upper 0.759%), true-license power was 35.040%, and abstention was 82.736%.

## Family scope

- ITEM_DIAGNOSTICS: false-license 0.200%; simultaneous upper 0.559%; power 50.867%; PASS.
- PRIMARY_PAIRWISE: false-license 0.667%; simultaneous upper 1.189%; power 30.833%; PASS.
- REPAIR: false-license 1.091%; simultaneous upper 1.681%; power 24.704%; PASS.
- THRESHOLD_PASS: false-license 1.067%; simultaneous upper 1.687%; power 19.500%; PASS.
- TOP_K: false-license 0.000%; simultaneous upper 0.231%; power 30.867%; PASS.
- TRANSPORT: false-license 0.727%; simultaneous upper 1.234%; power 54.370%; PASS.

Aggregate family checks pass, but 21 of 60 prespecified family-by-critical-stratum checks fail (39 pass). The policy is therefore supporting evidence, not publication-grade universal calibration. It was not retuned after confirmation.
