# Post-Import Analysis Router V4 Report

Implemented command:

```bash
python3 -m valideval post-import-analysis \
  --benchmark gsm8k \
  --matrix cache/gsm8k/wide/matrix.csv \
  --predictions cache/gsm8k/wide/predictions.jsonl \
  --output results/gsm8k \
  --execute
```

Implemented analyses:

- Panel validity.
- Ranking audit.
- Diagnostic disagreement.
- Baselines.
- Proxy/scalable IRT.
- Bootstrap/materiality via ranking-disagreement artifacts.
- Diagnostic-family ablation CSV.
- GSM8K-to-MMLU cross-benchmark preparation when MMLU exists.

Current repo state: no GSM8K imported matrix exists, so the router is ready but not evidence-bearing on GSM8K yet.

Tests: `tests/test_post_import_analysis_router_v4.py`.

Final verdict: `POST_IMPORT_ROUTER_READY`
