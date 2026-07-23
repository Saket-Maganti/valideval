# Examples

The default example is fully offline:

```bash
python -m valideval toy
python -m valideval matrices --benchmark toy_mcq --panel mock
python -m valideval audit --benchmark toy_mcq --panel mock --diagnostics all-core
python -m valideval report --benchmark toy_mcq --panel mock
python -m valideval forensics overlap --benchmark toy_mcq --corpus examples/toy_corpus/
python -m valideval repair --benchmark toy_mcq --panel mock --policy conservative
python -m valideval card render --benchmark toy_mcq --panel mock
python -m valideval certificate issue --benchmark toy_mcq --panel mock
python -m valideval checklist --benchmark toy_mcq --panel mock
python -m valideval evidence-matrix --benchmark toy_mcq --panel mock
python -m valideval leaderboard --benchmark toy_mcq --panel mock
python -m valideval registry validate
python -m valideval atlas --benchmark toy_mcq --panel mock
python -m valideval dashboard export --benchmark toy_mcq --panel mock
python -m valideval site build
python -m valideval human packet --benchmark toy_mcq --panel mock --sample-size 288
python -m valideval human import --benchmark toy_mcq --panel mock --path examples/toy_human_annotations.csv
python -m valideval human agreement --benchmark toy_mcq --panel mock
python -m valideval human judge --benchmark toy_mcq --panel mock
python -m valideval human ambiguity --benchmark toy_mcq --panel mock
python -m valideval human adjudication --benchmark toy_mcq --panel mock
python -m valideval human ui --benchmark toy_mcq --panel mock
python -m valideval domain list
python -m valideval domain describe rag
python -m valideval audit --benchmark toy_mcq --panel mock --domain rag
```

The generated report card is written to `reportcards/toy_mcq_mock.md`, with a
reproducibility manifest beside it at `reportcards/toy_mcq_mock.manifest.json`.
The audit manifest is written to `results/toy_mcq/manifest.json`. The overlap
example searches only the tiny local corpus in `examples/toy_corpus/`; it is a
scanner demonstration, not a broad contamination claim.
Repair artifacts are advisory review aids written under `results/toy_mcq/mock/`.
Leaderboard and dashboard artifacts are profile views, not corrected rankings or
single benchmark-health scores.
The toy human annotation CSV is a fixture for exercising import, agreement,
judge-reliability, ambiguity, and adjudication code paths. It is not an
empirical human-validation result.
Domain-pack fixtures under `examples/domain_packs/` validate RAG, agent,
medical, graph/fraud, code, safety, multimodal, and abstention metadata schemas.
They are smoke fixtures, not domain benchmark evidence.

`examples/gpqa_diamond_tiny_fixture.jsonl` is a synthetic GPQA-like schema and
scoring fixture. It is not GPQA Diamond and must not be cited as scientific
evidence. See `examples/README_gpqa_fixture.md` for the expected local JSONL
schema.
