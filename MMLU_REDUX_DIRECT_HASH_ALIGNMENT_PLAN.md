# MMLU-Redux Direct/Hash Alignment Plan

## Summary

Added `mmlu-redux-alignment-preflight --dry-run` to inspect local field names for direct IDs or
stable hashes without exposing raw MMLU text.

## Accepted alignment fields

- `item_id`
- `question_id`
- `stable_hash`
- `content_hash`
- `prompt_hash`

## Current state

MMLU-Redux remains weak/negative external validation. Detection-success claims remain blocked until
direct/hash alignment and stronger validation evidence exist.

## Command

```bash
python3 -m valideval mmlu-redux-alignment-preflight --dry-run \
  --predictions PATH_TO_SANITIZED_PREDICTIONS \
  --redux PATH_TO_SANITIZED_REDUX_LABELS
```
