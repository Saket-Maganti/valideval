# ValidEval V6 S1 Import and Acceptance

Gate: `S1_IMPORT_AND_ACCEPTANCE_READY`

The importer requires exactly one MMLU, one GSM8K, and one BBH V6 ZIP. It validates safe ZIP
members, required artifacts, file checksums, config hash, source tag commit, dataset revision,
prompt hash, exact model/tokenizer identities, declared failed models, unique model/item rows,
frozen item coverage, failure summaries, and extraction reliability.

It returns exactly one of:

- `S1_SMOKE_ACCEPTED`
- `S1_SMOKE_ACCEPTED_WITH_RECORDED_MODEL_FAILURES`
- `S1_SMOKE_REQUIRES_RERUN`
- `S1_SMOKE_REJECTED_CONFIGURATION_MISMATCH`
- `S1_SMOKE_REJECTED_DATA_INTEGRITY`
- `S1_SMOKE_REJECTED_EXTRACTION_FAILURE`
- `S1_SMOKE_REJECTED_INSUFFICIENT_COVERAGE`

Acceptance is fail-closed and remains `ENGINEERING_ONLY`. Missing/duplicate archive and
mock/non-evidence rejection paths are tested. No real S1 ZIP is present, so this report claims
acceptance readiness, not an accepted smoke result.

```bash
python -m valideval accept-s1 \
  --input-dir kaggle_outputs/v6 \
  --output-root imported/v6
```
