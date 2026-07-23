# 10-Minute Demo

This path exercises the offline toy benchmark. It makes no empirical claim about real model ability.

```bash
python3 -m pip install -e ".[dev]"
python3 -m valideval toy
python3 -m valideval matrices --benchmark toy_mcq --panel mock
python3 -m valideval audit --benchmark toy_mcq --panel mock --diagnostics all-core
python3 -m valideval card render --benchmark toy_mcq --panel mock
```

Useful artifacts:

- `cache/toy_mcq/mock/matrix_full.csv`
- `results/toy_mcq/mock/data_forensics.json`
- `results/toy_mcq/mock/item_forensics.csv`
- `results/toy_mcq/mock/validity_card.md`
- `results/toy_mcq/manifest.json`

Interpretation rule: these are diagnostic signals under this protocol. They are not a proof that a benchmark is globally valid or invalid.
