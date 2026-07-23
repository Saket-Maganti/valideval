# Importing Kaggle Outputs

1. Download `valideval_kaggle_outputs.zip` from the Kaggle notebook.
2. Place it under `kaggle_outputs/` in this repository.
3. Run Prompt 10. The import gate must create a manifest, extract into a new `data/external/kaggle_imported/<run_id>/` directory, validate `predictions.jsonl`, build `matrix.csv`, and run `panel-validity`.

Do not overwrite prior imports. Do not move raw Kaggle outputs into the reviewer packet.

Evidence remains `RESULT_REQUIRED` until the imported panel passes schema and panel-validity checks.
