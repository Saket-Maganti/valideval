# One-Hour Audit Guide

Use quickstart audit when you have local benchmark items and optional local model outputs.

```bash
python3 -m valideval quickstart-audit \
  --items items.jsonl \
  --outputs model_outputs.jsonl \
  --benchmark-card benchmark_card.md \
  --output-dir quickstart_audit
```

Required item format is `BenchmarkItem` JSONL. Outputs may use generic local JSONL/CSV fields such as `model`, `item_id`, `output`, `prediction`, `score`, and `raw_output`. If outputs do not include scores, quickstart rescoring uses the local benchmark scorer.

Artifacts:

- `validity_card.md` and `validity_card.json`
- `certificate.json`
- `item_forensics.csv`
- `repair_recommendations.md`
- `audit_manifest.json`
- `README_NEXT_STEPS.md`

If `--outputs` is omitted, ValidEval runs shallow/static diagnostics and says that model performance evidence is unavailable. This is useful for author review, but it is not evidence of model ranking.

Quickstart is intentionally conservative: it reports possible validity threats and missing evidence areas without turning them into a single validity score.
