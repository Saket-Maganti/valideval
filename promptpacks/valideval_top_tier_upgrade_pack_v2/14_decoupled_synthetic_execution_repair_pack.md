# Prompt 14 — Decoupled Synthetic Execution Repair Pack

## Objective

Fix the missing guard artifacts that blocked decoupled synthetic execution, then optionally execute only if guards pass.

## First repair missing artifacts

Create/verify:

```text
DECOUPLED_SYNTHETIC_SCHEMA_CONTRACTS.md
DECOUPLED_SYNTHETIC_REVIEWER_AUDIT_CHECKLIST.md
tests/test_decoupled_synthetic_preregistration_freeze.py
templates/reports/DECOUPLED_SYNTHETIC_FUTURE_RUN_MANIFEST_TEMPLATE.json
DECOUPLED_SYNTHETIC_FUTURE_COMMANDS.md
```

## Run guards

```bash
ruff check .
python3 -m pytest -q tests/test_decoupled_synthetic_protocol_guards.py
python3 -m pytest -q tests/test_decoupled_synthetic_preregistration_freeze.py
python3 -m valideval decoupled-synthetic-preflight --dry-run
```

## Execute only if all pass

```bash
python3 -m valideval decoupled-synthetic-run   --config configs/validation/decoupled_synthetic_preregistered.yaml   --output results/decoupled_synthetic/run_001   --execute
```

If execution command does not exist, implement minimal honest runner.

## Report

```text
DECOUPLED_SYNTHETIC_REPAIR_AND_EXECUTION_REPORT.md
```

Final verdict:

```text
DECOUPLED_SYNTHETIC_EXECUTED_LIMITED
DECOUPLED_SYNTHETIC_REPAIRED_NOT_EXECUTED
DECOUPLED_SYNTHETIC_STILL_BLOCKED
```
