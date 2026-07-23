# Real-Panel Baselines Plan

## Summary

This plan defines reviewer-required baseline and ablation scaffolds for future real-panel work. It
does not compute any metrics.

## Baselines

1. Accuracy-only ranking
2. Random item subset
3. Subject-stratified subset
4. Naive difficulty
5. Naive disagreement
6. Diagnostic-vs-diagnostic
7. MMLU-Redux external label baseline
8. Subject confounding baseline

## Current status

`RESULT_REQUIRED`. MMLU-Redux external-label use remains blocked until direct/hash alignment exists.

## Files

- `src/valideval/real_panel/baselines.py`
- `configs/real_panel/baselines_mmlu.yaml`
- `tests/test_real_panel_baselines_scaffold.py`

## Command

```bash
python3 -m valideval real-panel-baselines-preflight --dry-run
```
