# No-Run Dry-Run Surface Audit

## 1. Executive Summary

Verdict: `DRYRUN_SURFACE_READY`.

The dry-run/preflight surface was executed without experiments, model inference, downloads, metric
recomputation, threshold tuning, validation reruns, or evidence-state upgrades. All nine intended
surfaces wrote dry-run stdout captures and dry-run manifest JSON files under
`results/no_run_dryrun_surface/`.

Two no-run/dry-run fixes were applied during the audit:

- Real-panel wide-matrix schema checks now accept `model_id`, matching the existing MMLU wide-matrix
  layout.
- Schema manifests now cap `observed_fields` previews and record `observed_field_count` /
  `observed_fields_truncated`, avoiding oversized dry-run outputs while preserving schema evidence.

## 2. Commands Run

Implemented CLI names were checked with `python3 -m valideval --help`. The prompt names
`ollama-panel-preflight` and `second-benchmark-preflight` map to the implemented commands
`panel-preflight` and `benchmark-preflight`.

```bash
python3 -m valideval real-panel-baselines-preflight --dry-run --output results/no_run_dryrun_surface/real_panel_baselines_preflight.manifest.json
python3 -m valideval real-panel-ranking-audit --dry-run --matrix cache/mmlu/wide/matrix.csv --predictions cache/mmlu/wide/predictions.jsonl --mmlu-redux data/ground_truth/mmlu_redux_issues.helm_aligned.jsonl --results-dir results/mmlu --output results/no_run_dryrun_surface/real_panel_ranking_audit_dryrun.manifest.json
python3 -m valideval diagnostic-disagreement-audit --dry-run --matrix cache/mmlu/wide/matrix.csv --predictions cache/mmlu/wide/predictions.jsonl --mmlu-redux data/ground_truth/mmlu_redux_issues.helm_aligned.jsonl --results-dir results/mmlu --output results/no_run_dryrun_surface/diagnostic_disagreement_audit_dryrun.manifest.json
python3 -m valideval subject-instability-audit --dry-run --matrix cache/mmlu/wide/matrix.csv --predictions cache/mmlu/wide/predictions.jsonl --mmlu-redux data/ground_truth/mmlu_redux_issues.helm_aligned.jsonl --results-dir results/mmlu --output results/no_run_dryrun_surface/subject_instability_audit_dryrun.manifest.json
python3 -m valideval panel-preflight --dry-run --output results/no_run_dryrun_surface/ollama_panel_preflight.manifest.json
python3 -m valideval benchmark-preflight --dry-run --output results/no_run_dryrun_surface/second_benchmark_preflight.manifest.json
python3 -m valideval calibration-preflight --dry-run --output results/no_run_dryrun_surface/calibration_preflight.manifest.json
python3 -m valideval power-materiality-preflight --dry-run --output results/no_run_dryrun_surface/power_materiality_preflight.manifest.json
python3 -m valideval mmlu-redux-alignment-preflight --dry-run --predictions cache/mmlu/wide/predictions.jsonl --redux data/ground_truth/mmlu_redux_issues.helm_aligned.jsonl --output results/no_run_dryrun_surface/mmlu_redux_alignment_preflight.manifest.json
```

Each command also captured stdout to the matching `.txt` file in
`results/no_run_dryrun_surface/`.

## 3. Output Locations

| Surface | Stdout capture | Dry-run manifest |
|---|---|---|
| Real-panel baselines | `results/no_run_dryrun_surface/real_panel_baselines_preflight.txt` | `results/no_run_dryrun_surface/real_panel_baselines_preflight.manifest.json` |
| Real-panel ranking | `results/no_run_dryrun_surface/real_panel_ranking_audit_dryrun.txt` | `results/no_run_dryrun_surface/real_panel_ranking_audit_dryrun.manifest.json` |
| Diagnostic disagreement | `results/no_run_dryrun_surface/diagnostic_disagreement_audit_dryrun.txt` | `results/no_run_dryrun_surface/diagnostic_disagreement_audit_dryrun.manifest.json` |
| Subject instability | `results/no_run_dryrun_surface/subject_instability_audit_dryrun.txt` | `results/no_run_dryrun_surface/subject_instability_audit_dryrun.manifest.json` |
| Ollama panel preflight | `results/no_run_dryrun_surface/ollama_panel_preflight.txt` | `results/no_run_dryrun_surface/ollama_panel_preflight.manifest.json` |
| Second benchmark preflight | `results/no_run_dryrun_surface/second_benchmark_preflight.txt` | `results/no_run_dryrun_surface/second_benchmark_preflight.manifest.json` |
| Calibration preflight | `results/no_run_dryrun_surface/calibration_preflight.txt` | `results/no_run_dryrun_surface/calibration_preflight.manifest.json` |
| Power/materiality preflight | `results/no_run_dryrun_surface/power_materiality_preflight.txt` | `results/no_run_dryrun_surface/power_materiality_preflight.manifest.json` |
| MMLU-Redux alignment preflight | `results/no_run_dryrun_surface/mmlu_redux_alignment_preflight.txt` | `results/no_run_dryrun_surface/mmlu_redux_alignment_preflight.manifest.json` |

## 4. Dry-Run Compliance

| Surface | Status | Compliance |
|---|---|---|
| Real-panel baselines | `dry_run_ready` | `RESULT_REQUIRED`, dry-run manifest only |
| Real-panel ranking | `dry_run_ready` | `RESULT_REQUIRED`, planned metrics/outputs only |
| Diagnostic disagreement | `dry_run_ready` | `RESULT_REQUIRED`, planned metrics/outputs only |
| Subject instability | `dry_run_ready` | `RESULT_REQUIRED`, planned metrics/outputs only |
| Ollama panel preflight | `dry_run_ready` | `server_contacted=false`, `inference_run=false` |
| Second benchmark preflight | `dry_run_ready` | `download_run=false`, `evaluation_run=false` |
| Calibration preflight | `dry_run_ready` | `metrics_computed=false` |
| Power/materiality preflight | `dry_run_ready` | `metrics_computed=false`, `simulations_run=false` |
| MMLU-Redux alignment preflight | `direct_or_hash_fields_present` | `alignment_run=false`, claim remains blocked |

## 5. Accidental Execution Check

No output matched risky execution markers such as `metrics_computed: true`,
`inference_run: true`, `server_contacted: true`, `download_run: true`, `evaluation_run: true`,
`simulations_run: true`, `alignment_run: true`, validation-success claims, AUROC/AUPRC result text,
or evidence-state upgrade wording.

No real result tables were written. Only stdout `.txt` captures and dry-run manifest `.json` files
were created in the audit output directory.

## 6. Evidence States

Evidence states remain unchanged:

- Real-panel findings: `RESULT_REQUIRED`
- Calibration/logprob analysis: `BLOCKED` / `RESULT_REQUIRED`
- Power/materiality: `RESULT_REQUIRED`
- Confirmatory cross-flaw / held-out: `RESULT_REQUIRED`
- Second-benchmark evidence: `RESULT_REQUIRED`
- MMLU-Redux direct/hash validation: `BLOCKED` / `RESULT_REQUIRED`

## 7. Missing or Broken CLI Surfaces

No implemented dry-run surface is missing.

Name differences from the prompt were found and handled:

- `ollama-panel-preflight` is implemented as `panel-preflight`.
- `second-benchmark-preflight` is implemented as `benchmark-preflight`.

## 8. Fixes Applied

- Updated `src/valideval/real_panel/finding_engine.py` so real-panel dry-run checks accept the
  existing wide-matrix `model_id` layout.
- Updated `src/valideval/no_run_preflight.py` to truncate observed schema-field previews while
  recording total field counts.

No empirical code, metrics, thresholds, or claim states were changed.

## 9. Tests and Lint

Run after fixes:

```bash
ruff check .
python3 -m pytest -q tests/test_real_panel_dryrun_commands.py
python3 -m pytest -q tests/test_preflight_confirmatory_synthetic.py
python3 -m pytest -q
```

Results:

- `ruff check .`: passed
- `tests/test_real_panel_dryrun_commands.py`: 2 passed
- `tests/test_preflight_confirmatory_synthetic.py`: 7 passed
- Full suite: 182 passed

## 10. Final Verdict

`DRYRUN_SURFACE_READY`
