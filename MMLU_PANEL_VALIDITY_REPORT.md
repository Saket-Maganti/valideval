# MMLU Panel Validity Report

Timestamp: 2026-06-12

## Summary

Panel validity was rerun on the expanded real HELM-derived MMLU wide matrix:

```bash
python3 -m valideval panel-validity \
  --matrix cache/mmlu/wide/matrix.csv \
  --output results/mmlu/panel_validity \
  --strict
```

Runtime:

```text
real 0.65
user 0.43
sys 0.06
```

## Inputs

- Matrix: `cache/mmlu/wide/matrix.csv`
- Source predictions: `cache/mmlu/wide/predictions.jsonl`
- Evidence source: HELM MMLU `v1.13.0`
- Models: 39
- Items: 14,042
- Missing cells: 0

No raw MMLU question text is included in this report.

## Result

- Status: `pass`
- Blockers: none
- Interpretation from the command: panel supports item-level psychometric interpretation under this diagnostic protocol.

## Accuracy Distribution

Model accuracy:

- n: 39
- min: 0.2874
- mean: 0.6901
- max: 0.8676
- p10: 0.5442
- p90: 0.8142
- std: 0.1209

Item accuracy:

- n: 14,042
- min: 0.0000
- mean: 0.6901
- max: 1.0000
- p10: 0.2308
- p90: 0.9744
- std: 0.2853

## Variance And Separation

- Ability spread: 0.5802
- Accuracy std: 0.1209
- Near-chance model fraction: 0.0256
- Missing fraction: 0.0000

The previous blockers, `model_count_below_30` and `ability_spread_too_narrow`, are cleared for this 39-model HELM panel.

## Diagnostics Gate

- IRT item discrimination allowed by panel gate: yes
- Ranking uncertainty allowed by panel gate: yes
- Protocol/demo-only status: no
- MMLU-Redux validation allowed as evidence under this protocol: yes, with the structural-alignment caveat in `results/mmlu/redux_alignment/alignment_report.md`

## Proxy IRT Follow-Up

Quick proxy IRT has now been run:

```bash
python3 -m valideval fit-irt \
  --matrix cache/mmlu/wide/matrix.csv \
  --model proxy \
  --output results/mmlu/irt \
  --strict
```

- Status: `ok`
- Output: `results/mmlu/irt`
- Proxy-only: yes
- Full parametric 2PL: not run
- Negative discrimination items: 1,037
- Near-zero discrimination items: 1,342
- Extreme difficulty items: 2,676

MMLU-Redux validation of these proxy-IRT flags remains weak. Full-universe combined proxy-IRT flags have AUROC 0.495, AUPRC 0.030, Precision@10 0.000, and Precision@25 0.000. See `MMLU_REDUX_WEAK_SIGNAL_DIAGNOSIS.md`.

## Remaining Limits

- This pass does not itself establish MMLU validity or invalidity.
- Proxy IRT has run, but full psychometric IRT / full 2PL has not.
- Redux labels remain aligned by subject plus numeric source index, not by direct id or hash.
- Current proxy-IRT flags do not support a detection-success claim against MMLU-Redux labels.
- Public HELM artifacts include some non-A-D raw prediction strings; matrix correctness uses HELM `exact_match` correctness.
