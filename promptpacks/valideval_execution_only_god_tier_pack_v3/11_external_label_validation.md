# Prompt 11 — External Label Validation Execution

## Objective

Run any available external-label validation beyond the existing structural MMLU-Redux result.

## Search

```bash
find data results schemas -maxdepth 5 -type f \( -iname "*external*label*" -o -iname "*errata*" -o -iname "*redux*" \) | sort
```

## Tasks

1. Validate external-label schema.
2. Align labels if possible.
3. Run diagnostic-label association.
4. Preserve direct/hash requirements.
5. Report weak/null results honestly.

## Outputs

```text
results/external_label_validation_v3/
EXTERNAL_LABEL_VALIDATION_EXECUTION_REPORT_V3.md
```

## Final verdict

```text
EXTERNAL_LABEL_VALIDATION_COMPLETE
EXTERNAL_LABEL_VALIDATION_WEAK_OR_NEGATIVE
EXTERNAL_LABEL_VALIDATION_BLOCKED_NO_LABELS
```
