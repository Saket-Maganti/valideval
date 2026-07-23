# Human Validation Protocol

Human review is required for claims about construct coverage, item ambiguity, and whether an ablation preserves or removes construct-critical information.

Recommended workflow:

1. Review the construct specification.
2. Annotate construct-critical fields per item.
3. Check flagged shortcut and low-discrimination items.
4. Resolve disagreements with a second reviewer when possible.
5. Record all changes before rerunning diagnostics.

## Offline Packet Workflow

```bash
python3 -m valideval matrices --benchmark toy_mcq --panel mock
python3 -m valideval human packet --benchmark toy_mcq --panel mock --sample-size 100
python3 -m valideval human import --benchmark toy_mcq --panel mock --path annotations.csv
python3 -m valideval human agreement --benchmark toy_mcq --panel mock
python3 -m valideval human judge --benchmark toy_mcq --panel mock
python3 -m valideval human ambiguity --benchmark toy_mcq --panel mock
python3 -m valideval human adjudication --benchmark toy_mcq --panel mock
python3 -m valideval human ui --benchmark toy_mcq --panel mock
```

Required annotation fields:

- `task_id`
- `item_id`
- `anonymized_annotator`
- `label`
- `confidence`

Recommended fields:

- `model_id`
- `rationale`
- `ambiguity_flag`
- `invalid_item_flag`

Labels are protocol evidence. They should be reported with agreement metrics, sampling strategy, limitations, and adjudication status. Do not describe imported labels as perfect truth.
