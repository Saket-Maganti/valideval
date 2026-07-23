# ValidEval V5 Decoupled Synthetic Protocol

Audit date: 2026-07-16  
Confirmatory evidence state: `PLANNED`  
Fixture evidence state: `NON_EVIDENCE_FIXTURE`

## Verdict

`SYNTHETIC_PROTOCOL_PREFLIGHT_PASS_CONFIRMATORY_EXECUTION_BLOCKED`

The preregistration config is complete enough for a pre-execution protocol check, and the fixture proves that hidden synthetic truth is excluded recursively from public diagnostic inputs. The real generator/sweep executor is not implemented; confirmatory mode is deliberately rejected. No AUROC, AUPRC, calibration, recovery, or threshold result was produced.

## Generator-detector boundary

Public items expose only neutral item IDs, prompts, choices, and public metadata. Public response records expose neutral item IDs, model responses, and public covariates. Hidden condition, flaw family/type, severity, generator family, held-out status, labels, and private seed are stored separately.

`assert_public_synthetic_isolation` recursively rejects hidden keys at any depth. The fixed readout accepts only observable response records; its method signature has no truth argument. Public and private directories cannot be identical or nested with private truth under the public directory.

## Preregistered experiments

The V5 YAML declares all required lanes:

- no flaw, one flaw, multiple flaws, and unseen flaw;
- severity, prevalence, panel-size, and item-count sweeps;
- model-family dependence and leave-one-family-out analysis;
- missingness and correlated flaws;
- label permutation, diagnostic ablation, and negative controls.

## Frozen confirmatory choices

| Element | Frozen planning value |
|---|---|
| Development generator families | ambiguity, option-defect, and scoring-artifact template families V5 |
| Held-out family | context-omission templates V5 |
| Primary diagnostic | fixed response instability V5 |
| Primary metric | macro AUROC across preregistered flaw families |
| Secondary metrics | macro AUPRC, calibration error, fixed-threshold false-positive rate |
| Threshold policy | frozen on development generators before held-out execution |
| Primary sample size | 1,000 items/condition, 16-model panel, 5 independent generator replicates |
| Seeds | 1729, 2718, 31415, 65537, 104729 |
| Success rule | macro AUROC at least 0.70, lower 95% interval above chance, negative-control FPR at most 0.05, held-out result always reported |

These are preregistered criteria, not observed values.

## Fixture behavior

The deterministic fixture creates 12 items across four wiring conditions and four mock panel responses per item. It writes public items/responses and readout scores separately from private truth, hashes the artifacts, and labels every output `NON_EVIDENCE_FIXTURE`. The fixture never computes the confirmatory primary metric.

## Verification

```text
python3 -m pytest -q tests/test_confirmatory_synthetic_v5.py tests/test_synthetic_decoupling_v5.py tests/test_gold_answer_isolation_v5.py
13 passed in 0.09s
```

Tests verify required config fields, dry-run behavior, public/private isolation, recursive hidden-key rejection, neutral public APIs, deterministic fixture output, forbidden directory nesting, and refusal of real confirmatory mode.

## Remaining blockers

- The named generator families are config identifiers; their real generators are not implemented.
- The severity/prevalence/panel/item/family/missingness/correlation/permutation/ablation execution grid is not implemented.
- The real diagnostic pipeline, fixed threshold artifact, model-family simulator, metric/interval engine, exclusion ledger, and multiplicity report are absent.
- Confirmatory execution mode is intentionally unavailable in the pre-execution runner.

Consequently, `SYNTHETIC_PROTOCOL_READY` means the YAML passes preflight only. It does not mean the confirmatory experiment can run or that detector validity has been established.

## Exact next action

Implement the frozen generators and full execution grid without exposing private truth to the detector; freeze and hash the development threshold before held-out execution; then run the five preregistered seeds and report all null, negative, and held-out outcomes. Until then the primary claim remains `RESULT_REQUIRED`.
