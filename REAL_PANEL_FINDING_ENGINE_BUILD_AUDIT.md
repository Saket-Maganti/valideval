# Real-Panel Finding Engine Build Audit

## Summary

Added dry-run-only real-panel finding scaffolds for ranking disagreement, diagnostic disagreement,
and subject instability. These commands validate paths/schemas, write manifests, list planned
metrics and outputs, and refuse non-dry-run execution.

## Commands added

- `python3 -m valideval real-panel-ranking-audit --dry-run ...`
- `python3 -m valideval diagnostic-disagreement-audit --dry-run ...`
- `python3 -m valideval subject-instability-audit --dry-run ...`

## Planned finding types

1. Accuracy-only vs validity-adjusted ranking disagreement
2. Diagnostic-vs-diagnostic disagreement
3. Subject-specific validity instability
4. Suspicious-item subset ranking sensitivity
5. Multiple-diagnostic flagged item sets
6. MMLU-Redux weak/negative as blocked-claim case

## Evidence state

`RESULT_REQUIRED`. No real-panel ranking analysis was run.

## Implementation files

- `src/valideval/real_panel/finding_engine.py`
- `tests/test_real_panel_dryrun_commands.py`
