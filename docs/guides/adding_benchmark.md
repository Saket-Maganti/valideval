# Adding a Benchmark

Start from a local scaffold:

```bash
python3 -m valideval init-benchmark my_benchmark
python3 -m valideval validate-benchmark my_benchmark/
python3 -m valideval generate-card my_benchmark/
python3 -m valideval audit my_benchmark/
```

The scaffold creates:

- `items.jsonl`
- `construct_spec.yaml`
- `benchmark_card.md`
- `scoring.yaml`
- `audit_config.yaml`
- `README.md`

For real benchmark work, replace the sample item before making claims. Include stable item IDs, split metadata, source/provenance fields, scoring rules, and construct-critical fields.

Plain `audit my_benchmark/` runs an offline-safe first pass for local JSONL. Deeper diagnostics may require response matrices, prompt variants, human annotations, or domain-specific metadata.
