# Final V4 Pre-Execution Gate

> **SUPERSEDED_BY_V5 — historical snapshot only (2026-07-16).** The V4 verdict below did not
> survive the V5 audit unchanged. Its importer and cross-benchmark paths are legacy compatibility
> surfaces; controlled future runs must use the fail-closed V5 contracts. V5 also retired the
> `subject rank range >=10` severity rule, contradicted the legacy diagnostic-family ablation, and
> retired positive item-level MMLU-Redux validation. This banner does not rewrite the historical V4
> record.

Verdict: `READY_FOR_GSM8K_AND_BBH_KAGGLE_RUNS`

## Current Venue Level

Current level: strong workshop / evaluation-track scaffold with a real 39-model MMLU artifact spine.

Not claimed: NeurIPS, TMLR, or COLM readiness. The project still lacks actual GSM8K outputs, third-benchmark outputs, human labels, external labels beyond the weak/structural MMLU-Redux path, and validated cross-benchmark transfer evidence.

## What Is Still Not Evidence

- Hardened Kaggle notebooks are execution runbooks, not benchmark outputs.
- `kaggle_outputs/` currently has no returned ZIPs.
- `results/kaggle_import_v4/blocked_report.md` is a no-ZIP blocked report, not an import success.
- `results/cross_benchmark/blocked_report.md` is a second-matrix blocker, not cross-benchmark evidence.
- No human-review labels or external-label validation are present.

## Exact Kaggle Files To Run

Run first:

```text
kaggle_gsm8k/valideval_gsm8k_panel_runner.ipynb
```

Then run BBH third benchmark:

```text
kaggle_third_benchmark/valideval_third_benchmark_runner.ipynb
```

Use `kaggle_general/valideval_multi_model_matrix_runner.ipynb` only if you need a generic lm-eval-compatible fallback runner.

## Where To Place Output ZIPs

- GSM8K: `kaggle_outputs/gsm8k/valideval_outputs.zip`
- BBH: `kaggle_outputs/bbh/valideval_outputs.zip` or `kaggle_outputs/third_benchmark/valideval_outputs.zip`

## Exact Command After ZIP Download

```bash
bash scripts/run_after_kaggle_outputs_v4.sh
```

Manual first import command:

```bash
python3 -m valideval import-kaggle-outputs \
  --input-dir kaggle_outputs \
  --output-root data/external/kaggle_imported \
  --cache-root cache \
  --results-root results \
  --strict
```

## Expected Ceiling After Successful Import

- If GSM8K imports cleanly: stronger two-benchmark workshop/evaluation-track submission candidate with protocol-scoped cross-benchmark analysis against MMLU.
- If GSM8K and BBH both import cleanly: possible COLM/TMLR-ready candidate after claim-ledger review and paper update, still not automatic NeurIPS readiness.
- NeurIPS/TMLR/COLM readiness remains blocked unless evidence is real, imported, validated, and the claims ledger preserves the multidimensional profile rather than a single validity score.
