# Prompt 01 — V3 State Lock and Artifact Inventory

## Objective

Freeze the current state before execution so V3 changes are traceable.

## Read first

```text
FINAL_TOP_TIER_GATE_V2.md
Project report / latest autorun report if present
MMLU_DEEP_DIAGNOSTIC_VALUE_REPORT.md
BOOTSTRAP_MATERIALITY_REPORT.md
DIAGNOSTIC_FAMILY_ABLATION_REPORT.md
REPRODUCIBILITY_HARDENING_REPORT.md
REVIEWER_PACKET_V2_ZIP_AUDIT.md
```

## Commands

```bash
pwd
git status --short || true
find . -maxdepth 4 -type f \( -name "*REPORT.md" -o -name "*GATE*.md" -o -name "*AUDIT*.md" \) | sort > /tmp/valideval_v3_report_inventory.txt
find kaggle_outputs data/external cache results paper dist -maxdepth 5 -type f 2>/dev/null | sort > /tmp/valideval_v3_artifact_inventory.txt
ruff check .
python3 -m pytest -q
```

## Create

```text
V3_PRE_EXECUTION_STATE_LOCK.md
V3_PRE_EXECUTION_ARTIFACT_MANIFEST.json
```

## Final verdict

```text
V3_STATE_LOCK_READY
V3_STATE_LOCK_BLOCKED
```

Do not run new analyses in this prompt.
