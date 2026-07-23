# Decoupled Synthetic Execution Report

## Executive Summary

The decoupled synthetic validation was not executed. The available guard test passed, and the preflight scaffold reported dry-run readiness, but required preconditions are missing.

Final verdict: `DECOUPLED_SYNTHETIC_EXECUTION_BLOCKED`

## Preconditions

| Requirement | Status |
|---|---|
| `DECOUPLED_SYNTHETIC_SCHEMA_CONTRACTS.md` | missing |
| `DECOUPLED_SYNTHETIC_PREREGISTERED_EXECUTION_MANIFEST.md` | present |
| `DECOUPLED_SYNTHETIC_BASELINES_PLAN.md` | present |
| `DECOUPLED_SYNTHETIC_REVIEWER_AUDIT_CHECKLIST.md` | missing |
| `src/valideval/validation/decoupled_synthetic.py` | present |
| `tests/test_decoupled_synthetic_protocol_guards.py` | present and passing |
| `tests/test_decoupled_synthetic_preregistration_freeze.py` | missing |

## Commands

- `python3 -m pytest -q tests/test_decoupled_synthetic_protocol_guards.py`: 10 passed
- `python3 -m pytest -q tests/test_decoupled_synthetic_preregistration_freeze.py`: blocked, file missing
- `python3 -m valideval decoupled-synthetic-preflight --dry-run`: completed as dry-run only

## Preflight State

- Hidden-label guard: pass
- Fixed-readout guard: pass
- Flaw-type guard: pass
- Generation run: false
- Model inference run: false
- Metrics written: false
- AUC computed: false

Artifact:

- `results/preflight/decoupled_synthetic_preflight.json`

## Claims Allowed

- Decoupled synthetic scaffold guard surfaces exist.
- The available guard test passes.
- The protocol remains preregistered/scaffold-only.

## Claims Blocked

- Decoupled synthetic validation result.
- Any synthetic AUC as evidence.
- Any threshold-tuned or post-hoc synthetic claim.

## Final Verdict

`DECOUPLED_SYNTHETIC_EXECUTION_BLOCKED`
