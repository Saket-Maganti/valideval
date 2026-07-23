# Power and Materiality Analysis Plan

## Summary

Added a static `power-materiality-preflight --dry-run` command and placeholders for future power and
materiality reporting. No simulations or calculations were run.

## Future metrics

- Minimum detectable effect
- Expected CI width
- Sample-size/item-count sensitivity
- False-positive budget
- Materiality threshold
- Detectability vs materiality gap

## Current state

Power/materiality evidence remains `WEAK` / `RESULT_REQUIRED`.

## Command

```bash
python3 -m valideval power-materiality-preflight --dry-run
```
