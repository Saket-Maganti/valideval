# Design Assistant and Preregistration

Generate a noninteractive design scaffold:

```bash
python3 -m valideval design-assistant \
  --noninteractive \
  --benchmark-id rag_eval \
  --construct "RAG faithfulness under supplied evidence" \
  --domain rag \
  --output-dir design/rag_eval
```

Artifacts:

- `construct_spec.yaml`
- `audit_plan.md`
- `benchmark_card_draft.md`
- `human_validation_plan.md`
- `threat_model.md`

Generate a preregistration scaffold:

```bash
python3 -m valideval preregister \
  --benchmark rag_eval \
  --goal "evaluate RAG faithfulness" \
  --domain rag
```

Get benchmark-selection guidance:

```bash
python3 -m valideval advisor --goal "evaluate RAG faithfulness"
```

These commands produce planning artifacts. They do not produce empirical results and should be edited before use in a real study.
