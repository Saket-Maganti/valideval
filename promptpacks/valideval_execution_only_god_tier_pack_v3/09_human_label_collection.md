# Prompt 09 — Human Label Collection Pack

## Objective

Turn the existing human-review queue into a real label collection workflow. Do not create fake labels.

## Inputs

```text
results/mmlu/human_review_queue/human_review_queue.csv
docs/annotation/MMLU_REVIEW_RUBRIC.md
```

## Tasks

1. Create 50-item quick-review CSV.
2. Create 200-item full-review CSV.
3. Create label schema.
4. Create reviewer instructions.
5. Create import instructions.

## Outputs

```text
human_labeling/mmlu_review_50.csv
human_labeling/mmlu_review_200.csv
human_labeling/README_LABELING_INSTRUCTIONS.md
human_labeling/label_schema.json
human_labeling/import_human_labels_expected_format.md
HUMAN_LABEL_COLLECTION_REPORT_V3.md
```

## Final verdict

```text
HUMAN_LABEL_COLLECTION_READY
HUMAN_LABELS_ALREADY_PRESENT_READY_TO_IMPORT
HUMAN_LABEL_COLLECTION_BLOCKED
```
