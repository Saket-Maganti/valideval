# ValidEval V5 Cross-Benchmark Analysis Build

Audit date: 2026-07-16  
Protocol state: `PLANNED`  
Empirical conclusion: `BLOCKED`

## Verdict

`CROSS_BENCHMARK_CODE_FIXTURE_VALIDATED_RESULTS_BLOCKED`

The fail-closed V5 overlap gate, analysis runner, preregistered configuration, artifact writers, and paper template exist. No controlled MMLU, GSM8K, or BBH matrix is configured, so no transfer conclusion is available.

Running the default command without `--execute` correctly produced:

```text
status: blocked
transfer_conclusion: BLOCKED
missing_benchmarks: [bbh, gsm8k, mmlu]
evidence_state: RESULT_REQUIRED
```

## Predeclared estimands

The configuration separates:

1. exact-model rank transfer across identical checkpoint identities;
2. ability transfer;
3. diagnostic-family transfer;
4. construct specialization/model-by-benchmark interaction;
5. top-k and pairwise ranking-decision stability;
6. exploratory family-level transfer when exact overlap is insufficient.

No universal transfer estimand or conclusion is allowed.

## Implemented analysis components

- Exact checkpoint intersection and pairwise benchmark overlap audit.
- Spearman and Kendall rank association.
- Model-bootstrap Spearman interval and permutation null p-value.
- Benjamini-Hochberg multiple-testing correction.
- Optional attenuation correction when benchmark score reliabilities are supplied.
- Pairwise ordering agreement and top-k Jaccard overlap.
- Family-deduplicated and leave-one-family-out sensitivity analyses.
- Pairwise benchmark similarity/distance table.
- Diagnostic-family transfer table when diagnostic scores are supplied.
- Prompt/scoring-condition sensitivity table when condition scores are supplied.
- Exploratory family-level path that is distinct from exact-checkpoint inference.
- Deterministic CSV/JSON/Markdown artifacts and artifact hashes.

The current `model_benchmark_interaction_v5.json` computation is a descriptive two-way variance decomposition. It is not a fitted hierarchical model and must not be described as one.

## Gate thresholds

The frozen planning configuration currently requires:

| Gate | Threshold |
|---|---:|
| Exact common models | 8 |
| Independent common families | 3 |
| Common families for exploratory-only path | 3 |
| Usable items per benchmark | 100 |
| Extraction reliability | 0.95 |
| Common configuration class | required |

The confirmatory runner also predeclares 2,000 bootstrap iterations, 2,000 permutations, seed `20260715`, alpha 0.05, BH correction, and a minimum of 8 models for inference. These are protocol parameters, not results.

## Allowed result vocabulary

Only `TRANSFER_SUPPORTED`, `TRANSFER_PARTIAL`, `TRANSFER_BENCHMARK_SPECIFIC`, `TRANSFER_NOT_SUPPORTED`, `UNDERPOWERED`, or `BLOCKED` may be emitted. Fixture evidence forces `UNDERPOWERED`; missing or failed gates force `BLOCKED`.

## Verification

Cross-benchmark analysis and gate tests passed within this command:

```text
python3 -m pytest -q tests/test_kaggle_importer_adversarial_v5.py tests/test_cross_benchmark_gates_v5.py tests/test_cross_benchmark_analysis_v5.py
9 passed in 0.99s
```

The successful analysis test uses four deterministic `NON_EVIDENCE_FIXTURE` models and deliberately returns `UNDERPOWERED`. A separate test verifies that failed exact and family gates do not create rank-transfer artifacts.

## Remaining scientific blockers

- All three controlled matrices and validated V5 importer receipts are absent.
- Five exact repository revisions are frozen, but the 5-model/3-family roster is below the planned S3 target and no common execution identity has been reproduced.
- Reliability inputs for attenuation-aware estimates are absent.
- Diagnostic-transfer and condition-sensitivity inputs are absent.
- The requested hierarchical model-by-benchmark interaction is not implemented.
- No power claim can be made before the observed overlap and family structure are known.

## Exact next action

After S1/S2 validation, import MMLU, GSM8K, and BBH packages through V5; pass their receipts and exact matrices to `scripts/run_cross_benchmark_v5.py`; require `CROSS_BENCHMARK_READY_EXACT_COMMON_PANEL`; then run the frozen analysis with `--execute`. If the exact gate does not pass, report only the explicit blocked or exploratory-family state.
