# ValidEval Kaggle Panel Runner

This package is for generating open-model prediction panels on Kaggle GPU notebooks. It does not use paid APIs or private credentials.

## What It Produces

- `predictions.jsonl`: normalized wide prediction records with item ids, model ids, gold labels, predictions, and correctness.
- `matrix.csv`: model-by-item correctness matrix.
- `manifest.json`: run metadata, model/task config, file hashes, and row counts.
- `valideval_kaggle_outputs.zip`: portable output archive for import into this repository.

## Intended Tasks

The default task config prioritizes:

- MMLU subset smoke/full lanes.
- GSM8K as the recommended second-benchmark path when enough open-model outputs can be produced.
- TruthfulQA as a fallback scaffold only, because deterministic scoring requires care.

## Local Import After Kaggle

Place the Kaggle output ZIP under `kaggle_outputs/`, then run the Prompt 10 import/validation gate. Do not claim second-benchmark evidence until schema import, matrix creation, and panel-validity all pass.

## Evidence Boundary

This notebook package is an execution path, not evidence. Until a ZIP is returned and validated, second-benchmark evidence remains `RESULT_REQUIRED`.
