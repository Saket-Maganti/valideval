# ValidEval V3 Import And Validate

No GSM8K or third-benchmark output artifact was found during the V2 autorun.

Expected imports after external execution:

```bash
python3 scripts/v2_top_tier_local.py kaggle-import --help
python3 -m pytest -q tests/test_lm_eval_importer.py tests/test_wide_matrix_importer.py tests/test_second_benchmark_preflight.py
```

Do not promote GSM8K, BBH, TruthfulQA, three-benchmark transfer, human-label, or external-label claims until real outputs and labels are imported and validated.
