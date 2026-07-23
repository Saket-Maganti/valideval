# Calibration Infrastructure Build Report

## Summary

Added calibration/logprob schema inspection and a `calibration-preflight --dry-run` command. The
preflight lists future metrics but computes none.

## Future metrics

- ECE
- Adaptive ECE
- Brier
- NLL
- Accuracy-confidence curve
- Calibration by subject
- Calibration by diagnostic flag

## Current state

Numeric calibration remains `BLOCKED` until confidence/logprob outputs exist.

## Command

```bash
python3 -m valideval calibration-preflight --dry-run
```
