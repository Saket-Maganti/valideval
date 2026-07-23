# ValidEval Docs

`valideval` turns psychometric validity threats into auditable diagnostics for AI benchmarks. The first release focuses on an offline toy audit that exercises the full pipeline without paid APIs or external data.

Key documents:

- `docs/theory/validity_framework.md`
- `docs/theory/psychometrics_for_ai_eval.md`
- `docs/theory/advanced_psychometrics.md`
- `docs/theory/benchmark_repair.md`
- `docs/theory/core_diagnostics.md`
- `docs/theory/data_forensics.md`
- `docs/theory/threat_taxonomy.md`
- `docs/theory/validity_adjusted_leaderboards.md`
- `docs/theory/human_validation.md`
- `docs/theory/domain_packs.md`
- `docs/validation/diagnostic_validation_harness.md`
- `docs/validation/synthetic_flaw_generator.md`
- `docs/validation/interpreting_detector_metrics.md`
- `docs/validation/multiplicity_and_materiality.md`
- `docs/validation/validated_vs_experimental_diagnostics.md`
- `docs/protocols/gpqa_diamond_preregistration.md`
- `GPQA_OUTPUT_GENERATION_PLAN.md`
- `docs/guides/10_minute_demo.md`
- `docs/guides/one_hour_audit.md`
- `docs/guides/adding_benchmark.md`
- `docs/guides/adding_diagnostic.md`
- `docs/guides/adding_domain_pack.md`
- `docs/guides/plugin_package_creation.md`
- `docs/guides/design_assistant_and_preregistration.md`
- `docs/guides/publishing_validity_card.md`
- `docs/guides/interpreting_certificates.md`
- `docs/guides/common_overclaims.md`
- `docs/protocols/audit_protocol.md`
- `docs/protocols/human_validation_protocol.md`
- `docs/protocols/preregistered_benchmark_set.md`
- `docs/protocols/statistical_reporting_protocol.md`
- `GPQA_DIAMOND_AUDIT_READINESS.md`
- `LITERATURE_AND_BENCHMARK_SELECTION_REPORT.md`
- `docs/reference/domain_threats.md`
- `docs/engineering/RELEASE_CHECKLIST.md`
- `docs/engineering/GOD_TIER_ROADMAP.md`
- `docs/schemas/audit_manifest.schema.json`
- `docs/schemas/benchmark.schema.json`
- `docs/schemas/certificate.schema.json`
- `docs/schemas/diagnostic_result.schema.json`
- `docs/schemas/model_output.schema.json`
- `docs/schemas/prediction.schema.json`
- `docs/schemas/response_matrix.schema.json`
- `docs/schemas/validity_card.schema.json`
- `docs/schemas/gpqa_diamond_item_schema.md`
- `docs/schemas/gpqa_model_output_schema.md`
- `docs/engineering/REPRODUCIBILITY.md`

## GPQA local export and output generation

The repository does not ship GPQA items. Users must obtain GPQA Diamond through appropriate local means, avoid publishing raw question text in reports, and use open/local models or cached outputs only. Smoke runs with `gpqa_smoke_local` validate the workflow but are not scientific results.

Start with:

```bash
python3 -m valideval export-gpqa-diamond --source-file data/raw/gpqa_source.csv --output data/gpqa/gpqa_diamond.jsonl
python3 -m valideval check-panel --panel gpqa_open_local
python3 -m valideval generate-outputs --benchmark gpqa_diamond --items data/gpqa/gpqa_diamond.jsonl --panel gpqa_open_local --prompt-variant full --output-dir local_outputs/gpqa/full
```

No GPQA audit claims should be made until go/no-go passes and diagnostics are run under `docs/protocols/gpqa_diamond_preregistration.md`. See `GPQA_OUTPUT_GENERATION_PLAN.md` for the full local-only command sequence.
