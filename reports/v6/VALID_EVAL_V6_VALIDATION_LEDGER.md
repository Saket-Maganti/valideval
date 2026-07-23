# ValidEval V6 Validation Ledger

Overall local status: `PASS`

Validation ran on 2026-07-23 in both the existing native environment and a newly created `.venv`
under Python 3.11.9 on macOS 26.5.2 arm64. The final recorded chain ran from
2026-07-23T15:37:01Z through 15:37:49Z.

| Check | Result | Duration |
|---|---|---:|
| Create clean `.venv` | passed | 0.90 s |
| Upgrade clean pip | passed | 0.26 s |
| Install editable `.[dev]` | passed | 1.27 s |
| Clean-environment full tests | 349 passed | 17.24 s |
| Native full tests | 349 passed | 17.53 s |
| `ruff check .` | passed | 0.04 s |
| `ruff format --check .` | passed | 0.02 s |
| mypy, 20 critical V6 modules | passed | 0.12 s |
| sdist and wheel build | passed (`valideval` 0.3.0) | 2.04 s |
| `valideval doctor` | passed | 0.70 s |
| CLI help | passed | 0.69 s |
| V5 MMLU evidence reproduction | `REPRODUCED` | 5.50 s |
| V5 paper assets | passed | 0.02 s |
| pdfLaTeX/BibTeX/pdfLaTeX×2 | passed | 1.19 s |
| Source release dry run | `RELEASE_DRY_RUN_SAFE` | 0.93 s |

Test accounting in each environment: 349 passed, 0 failed, 0 skipped, 0 xfailed. Both runs emitted
two pandas `ConstantInputWarning` instances from the deliberately constant tiny post-import router
fixture; no V6 production-path warning was emitted.

Additional closure executions:

- V6 scoring/config/gold/scheduler/runner/notebook/importer/environment adversarial tests are
  included in the 349-test suite.
- All six notebook JSON files validated and executed top-to-bottom in fixture mode.
- Mocked production run/resume/validate/package produced and revalidated a 250-row non-evidence
  artifact.
- MMLU rank materiality: 39 models, 14,042 items, 57 subjects, 500 bootstraps, 500 additive-null
  simulations, status `REPRODUCED`.
- Measurement model: held-out, baseline, calibration, uncertainty, regularization,
  family-deduplicated, and synthetic recovery checks, status
  `MEASUREMENT_MODEL_PLAN_DEFENSIBLE`.
- Immutable parquet-derived S1 freeze regenerated all 150 item identities and leakage checks;
  gate `S1_LEAKAGE_GUARDS_COMPLETE`.

Environment limitation: the pinned Kaggle requirements were hash-frozen locally, but the exact
CUDA/T4×2 binary stack is `PINNED_UNVALIDATED_ON_REMOTE_T4X2` until notebook 00 runs on Kaggle.

Machine command tails are retained locally in the ignored
`results/v6_validation/command_ledger_v6.json`.
