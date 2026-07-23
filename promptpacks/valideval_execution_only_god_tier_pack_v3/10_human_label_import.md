# Prompt 10 — Human Label Import

## Objective

Import actual human labels if supplied.

## Search

```bash
find human_labeling data/external -maxdepth 5 -type f \( -name "*label*.csv" -o -name "*human*.csv" -o -name "*completed*.csv" \) | sort
```

## If no labels

Create:

```text
HUMAN_LABEL_IMPORT_BLOCKED_NO_LABELS.md
```

## If present

Validate schema, item IDs, labels, reviewer IDs, and sanitization.

## Outputs

```text
results/mmlu/human_labels/validated_labels.csv
results/mmlu/human_labels/agreement_summary.json
results/mmlu/human_labels/diagnostic_label_alignment.csv
HUMAN_LABEL_IMPORT_AND_VALIDATION_REPORT_V3.md
```

## Final verdict

```text
HUMAN_LABEL_VALIDATION_COMPLETE
HUMAN_LABEL_VALIDATION_PARTIAL
HUMAN_LABEL_IMPORT_BLOCKED_NO_LABELS
HUMAN_LABEL_SCHEMA_FAILED
```
