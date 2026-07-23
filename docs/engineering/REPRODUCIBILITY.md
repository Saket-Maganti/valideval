# Reproducibility

## Generate Once, Cache Forever

Predictions are written to `cache/{benchmark_id}/{panel_id}/predictions_{variant}.jsonl`. Response matrices are written beside them as CSV files. Diagnostics read from cached matrices where possible.

Each audit also writes `results/{benchmark_id}/manifest.json` with deterministic
hashes for item IDs, item text, benchmark config, scorer identity, prompt
templates, and diagnostic config.

## Fixed Seeds

The offline mock panel is deterministic. The default seed is `0`.

## No Paid APIs

The toy demo and tests do not require paid APIs, internet access, Hugging Face downloads, or Ollama. The Ollama runner is optional and local-only.
Public-artifact acquisition scripts are separate from the offline path; install them with
`python3 -m pip install -e ".[acquisition]"` only for an approved network acquisition pass.

## Offline Commands

```bash
python3 -m pip install -e ".[dev]"
python3 -m pytest
python3 -m valideval matrices --benchmark toy_mcq --panel mock
python3 -m valideval audit --benchmark toy_mcq --panel mock --diagnostics all-core
python3 -m valideval report --benchmark toy_mcq --panel mock
python3 -m valideval forensics overlap --benchmark toy_mcq --corpus examples/toy_corpus/
python3 -m valideval repair --benchmark toy_mcq --panel mock --policy conservative
python3 -m valideval card render --benchmark toy_mcq --panel mock
python3 -m valideval certificate issue --benchmark toy_mcq --panel mock
python3 -m valideval checklist --benchmark toy_mcq --panel mock
python3 -m valideval evidence-matrix --benchmark toy_mcq --panel mock
python3 -m valideval leaderboard --benchmark toy_mcq --panel mock
python3 -m valideval registry validate
python3 -m valideval atlas --benchmark toy_mcq --panel mock
python3 -m valideval dashboard export --benchmark toy_mcq --panel mock
python3 -m valideval site build
python3 -m valideval human packet --benchmark toy_mcq --panel mock --sample-size 288
python3 -m valideval human import --benchmark toy_mcq --panel mock --path examples/toy_human_annotations.csv
python3 -m valideval human agreement --benchmark toy_mcq --panel mock
python3 -m valideval human judge --benchmark toy_mcq --panel mock
python3 -m valideval human ambiguity --benchmark toy_mcq --panel mock
python3 -m valideval human adjudication --benchmark toy_mcq --panel mock
python3 -m valideval human ui --benchmark toy_mcq --panel mock
python3 -m valideval domain list
python3 -m valideval domain describe rag
python3 -m valideval audit --benchmark toy_mcq --panel mock --domain rag
python3 -m valideval audit --benchmark toy_mcq --panel mock --domain abstention
```

The bundled `examples/toy_human_annotations.csv` is a deterministic toy fixture for validating the import and agreement pipeline. It is not an empirical human study.
Domain-pack fixtures under `examples/domain_packs/` are metadata smoke fixtures. They are not real benchmark results.

## Regenerating Report Cards

Delete `cache/toy_mcq/mock`, `results/toy_mcq`, `reportcards/toy_mcq_mock.md`, and `reportcards/toy_mcq_mock.manifest.json`, then rerun the offline audit commands.
