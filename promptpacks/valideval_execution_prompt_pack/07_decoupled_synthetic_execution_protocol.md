# Prompt 07 — Execute Decoupled Synthetic Validation Protocol

## Objective

Run the new decoupled synthetic validation only if preregistration and guard tests pass.

## Preconditions

Required:

```text
DECOUPLED_SYNTHETIC_SCHEMA_CONTRACTS.md
DECOUPLED_SYNTHETIC_PREREGISTERED_EXECUTION_MANIFEST.md
DECOUPLED_SYNTHETIC_BASELINES_PLAN.md
DECOUPLED_SYNTHETIC_REVIEWER_AUDIT_CHECKLIST.md
src/valideval/validation/decoupled_synthetic.py
tests/test_decoupled_synthetic_protocol_guards.py
tests/test_decoupled_synthetic_preregistration_freeze.py
```

Run:

```bash
ruff check .
python3 -m pytest -q tests/test_decoupled_synthetic_protocol_guards.py
python3 -m pytest -q tests/test_decoupled_synthetic_preregistration_freeze.py
python3 -m valideval decoupled-synthetic-preflight --dry-run
```

Block if any fail.

## Execution

If actual commands exist:

```bash
python3 -m valideval decoupled-synthetic-run   --config configs/validation/decoupled_synthetic_preregistered.yaml   --output results/decoupled_synthetic/run_001   --execute

python3 -m valideval decoupled-synthetic-analyze   --run results/decoupled_synthetic/run_001   --output results/decoupled_synthetic/analysis_001   --execute

python3 -m valideval decoupled-synthetic-reviewer-audit   --run results/decoupled_synthetic/run_001   --analysis results/decoupled_synthetic/analysis_001   --output results/decoupled_synthetic/reviewer_audit_001   --execute
```

If commands do not exist, implement from the preregistered schema only.

## Constraints

- model must not receive hidden labels,
- readout fixed before seeing flaw family,
- baselines run,
- null/random controls run,
- held-out transfer runs if preregistered,
- thresholds preregistered or sensitivity-reported,
- no threshold tuning after seeing results.

## Report

Create:

```text
DECOUPLED_SYNTHETIC_EXECUTION_REPORT.md
```

Final verdict:

```text
DECOUPLED_SYNTHETIC_VALIDATION_POSITIVE_LIMITED
DECOUPLED_SYNTHETIC_VALIDATION_WEAK_NEGATIVE
DECOUPLED_SYNTHETIC_EXECUTION_BLOCKED
```

Even if positive, only claim limited decoupled synthetic validation under preregistered assumptions.
