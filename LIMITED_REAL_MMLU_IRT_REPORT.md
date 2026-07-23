# Limited Real MMLU IRT Report

Timestamp UTC: 2026-06-12T10:20:51Z

## Evidence Boundary

This is real evidence.

This is limited to `mmlu_high_school_biology`.

This is not full all-subject MMLU.

This is not MMLU-Redux validation.

Mock/example files were not used as evidence.

## Command

The CLI supports this matrix path and the command ran:

```bash
python3 -m valideval fit-irt \
  --matrix cache/mmlu/wide/matrix.csv \
  --output results/mmlu/irt
```

Measured runtime:

```text
real 0.70s
user 0.63s
sys 0.05s
```

## Result

IRT command ran.

Status: `proxy_only_blocked_panel`

Requested model: `2pl`

The internal panel-validity check was `blocked` with:

- Models: `3`
- Items: `310`
- Blocker: `model_count_below_30`

## Estimation Layers

- Proxy layer: `true`
- Rasch/1PL: `false`
- 2PL proxy: `false`
- Full parametric 2PL: `false`

Warnings from the fit:

- Rasch/1PL fit skipped because the matrix is too small.
- 2PL proxy flagged as insufficient-data; reporting proxy slopes only.
- Full parametric 2PL is not claimed.

## Interpretation

The IRT pipeline can execute on the limited real matrix, but the output is a
blocked-panel proxy report only. It is useful as a wiring/provenance check, not
as evidence for item-level discrimination claims.

Allowed claim:

- The wide-matrix IRT pathway executed on real limited lm-eval evidence and
  produced blocked-panel artifacts.

Forbidden claims:

- Do not claim full IRT or full parametric 2PL fit.
- Do not claim reliable item-discrimination findings.
- Do not claim full all-subject MMLU.
- Do not claim MMLU-Redux validation.

## Artifacts

- `results/mmlu/irt/fit_summary.json`
- `results/mmlu/irt/fit_summary.md`
- `results/mmlu/irt/item_parameters.csv`
- `results/mmlu/irt/model_abilities.csv`
- `results/mmlu/irt/flags.jsonl`
