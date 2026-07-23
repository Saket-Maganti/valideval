# Domain Threat Library

The canonical machine-readable threat specs live in `src/valideval/domains/threats.json`.

Each threat spec records:

- name
- domain
- description
- diagnostic
- evidence
- repair
- limitations

Domains currently covered:

- `rag`
- `abstention`
- `agent`
- `medical`
- `graph_fraud`
- `code`
- `safety`
- `multimodal`

Use:

```bash
python3 -m valideval domain describe rag
```

Threat specs identify possible validity threats and recommended evidence. They are not empirical findings that a threat is present.
