# Limited Real MMLU Panel Validity Report

> Historical/provenance note: this report describes an older 3-model,
> 310-item `mmlu_high_school_biology` pilot only. It is not the active
> MMLU panel. The active reconciled panel is the 39-model HELM MMLU wide
> matrix at `cache/mmlu/wide/matrix.csv`, with panel validity passing in
> `results/mmlu/panel_validity/panel_validity.json`.

Timestamp UTC: 2026-06-12T10:20:51Z

## Evidence Boundary

This is real evidence.

This is historical limited-pilot evidence for `mmlu_high_school_biology`.

This is not full all-subject MMLU.

This is not MMLU-Redux validation.

This is not the current active MMLU panel state.

Mock/example files were not used as evidence.

## Command

```bash
python3 -m valideval panel-validity \
  --matrix cache/mmlu/wide/matrix.csv \
  --output results/mmlu/panel_validity
```

Measured runtime:

```text
real 0.42s
user 0.36s
sys 0.05s
```

## Result

Panel validity ran.

Status: `blocked`

Reason: `model_count_below_30`

The limited real matrix has:

- Models: `3`
- Items: `310`
- Missing fraction: `0.000`
- Ability spread: `0.506`
- Near-chance model fraction: `0.333`
- Mean model/item accuracy: `0.5118`

Current active-panel clarification: the active all-subject HELM MMLU wide
matrix now has 39 models and clears the panel-size blocker. The blocked status
in this report applies only to the historical limited pilot above.

## Interpretation

The matrix is real and complete for the limited pilot, but the model panel is
too small for item-level psychometric or item-discrimination claims.

Allowed claim:

- ValidEval successfully ingested and analyzed a real lm-eval
  `mmlu_high_school_biology` pilot matrix.

Forbidden claims:

- Do not claim full all-subject MMLU evidence.
- Do not claim MMLU-Redux validation.
- Do not claim IRT item-discrimination validity from this historical 3-model
  pilot.
- Do not claim benchmark-wide validity or invalidity from this panel.
- Do not describe this pilot as the current active panel.

## Artifacts

- `results/mmlu/panel_validity/panel_validity.json`
- `results/mmlu/panel_validity/panel_validity.md`
