# Prompt 12 — External Label Validation Pack Beyond MMLU-Redux

## Objective

Find or prepare another external validation target, even if it becomes blocked.

## Candidate validation sources

- MMLU-Redux labels,
- dataset errata,
- benchmark issue trackers,
- paper-maintained correction lists,
- human-reviewed samples generated locally,
- external contamination/duplicate lists if available.

## Tasks

1. Search local repo for external labels/errata.
2. Create an external-label schema.
3. Build importers.
4. Attempt validation if labels exist.
5. Otherwise create a blocked-but-ready path.

## Outputs

```text
schemas/external_label.schema.json
src/valideval/external_labels/
EXTERNAL_LABEL_VALIDATION_PLAN.md
EXTERNAL_LABEL_VALIDATION_REPORT.md
```

Final verdict:

```text
EXTERNAL_LABEL_VALIDATION_COMPLETE
EXTERNAL_LABEL_PATH_READY_NO_LABELS
EXTERNAL_LABEL_VALIDATION_BLOCKED
```
