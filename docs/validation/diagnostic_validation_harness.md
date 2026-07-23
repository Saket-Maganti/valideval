# Diagnostic Validation Harness

ValidEval audits benchmark validity, but the diagnostics themselves need validation. A toy benchmark with obvious artifacts shows that code runs; it does not establish sensitivity, specificity, false-positive behavior, or materiality.

The validation harness creates controlled synthetic MCQ benchmarks with known ground-truth flaw metadata, runs existing ValidEval diagnostics through normal response matrices and cached predictions, and reports detector metrics.

What this validates:

- Whether a diagnostic score increases when a known synthetic flaw is injected.
- Whether clean synthetic benchmarks produce false flags.
- Whether thresholds can be estimated from null synthetic runs.
- Whether per-item flags survive multiplicity correction.

What this does not validate:

- Any claim about GSM8K, MMLU, TruthfulQA, or another real benchmark.
- Global benchmark invalidity.
- A universal threshold that transfers to every benchmark.
- Human construct validity.

Run the full suite:

```bash
python3 -m valideval validate-diagnostics --config configs/validation/all_sweeps.yaml
```

Main outputs:

- `validation_reports/diagnostic_validation_summary.md`
- `validation_reports/diagnostic_validation_summary.json`
- `validation_reports/{diagnostic}_{flaw}.md`
- `validation_reports/{diagnostic}_{flaw}.json`

Diagnostics are labeled as credible under the synthetic harness, prototype-only, uncalibrated, or quarantined. These labels are about synthetic detector validation only.
