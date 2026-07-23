# GPQA Extraction Compliance Decision Report

## 1. Executive Summary

A formal amended-v2 extraction-compliance decision was recorded. The 0.95 extraction threshold was kept. Two original models were flagged using extraction-compliance-only criteria, replacement models were selected from feasible local Ollama models, and a separate compliant preliminary panel was built before any diagnostic interpretation.

The compliant panel now has 8 models, 1584 amended-v2 predictions, complete alignment, `matrix_full_answer_only_v2.csv`, and amended go/no-go status `go`. Dry-run-real completed as a shell only; no diagnostics were interpreted.

## 2. Starting State

- Item file: `data/gpqa/gpqa_diamond.jsonl`
- Item count: 198
- Original amended-v2 panel: `gpqa_minimal_open_local`
- Original amended-v2 extraction success: 0.941 versus threshold 0.95
- Original amended-v2 status before this phase: `no_go`

## 3. Decision Memo

Decision memo: `docs/protocols/gpqa_diamond_amended_v2_extraction_compliance_decision.md`

The memo compares keeping the threshold, lowering it, regenerating the same models with a stricter prompt, exclusion/replacement under pre-specified criteria, and replacement with feasible local Ollama alternatives.

## 4. Compliance Rule

Machine-readable rule: `configs/audits/gpqa_diamond_amended_v2_compliance.yaml`

A model is eligible for the amended-v2 primary panel only if its `full_answer_only_v2` extraction success is at least 0.95 under the frozen extractor, with no item dropping and no answer-label modification. The aggregate panel must also meet 0.95.

Forbidden bases: accuracy, diagnostic findings, item quality flags, and model ranking.

## 5. Original 8-Model Extraction Compliance

Original compliance report: `results/gpqa_diamond/input_validation/amended_v2_model_compliance.json`

- Original models: 8
- Eligible under rule: 6
- Non-compliant under rule: `llama3.2:1b`, `mistral:latest`

## 6. Excluded / Non-Compliant Models

- `llama3.2:1b`: excluded from the compliant panel under extraction-compliance criteria only.
- `mistral:latest`: excluded from the compliant panel under extraction-compliance criteria only.

The original raw outputs, scored predictions, matrix, failure analysis, and threshold review remain preserved. Archive manifest: `results/gpqa_diamond/input_validation/amended_v2_original_8model_archive_manifest.json`.

## 7. Replacement Candidate Search

Candidate report: `results/gpqa_diamond/input_validation/replacement_model_candidates.json`

Selected replacements:

- `qwen2.5:latest`
- `mistral:7b-instruct-q5_K_M`

`phi3.5:3.8b` was attempted but not selected because the local pull was not completed in practical runtime. Larger candidates were not forced.

## 8. Compliant Panel

Panel config: `configs/panels/gpqa_minimal_open_local_amended_v2_compliant.yaml`

Panel label: amended-v2 extraction-compliant preliminary local panel. This is not paper-grade and is not a closed-model or paid-API panel.

## 9. Output Generation

Replacement outputs were generated with resume behavior under:

```text
local_outputs/gpqa/full_answer_only_v2/
```

The six retained compliant original model files were reused from raw local outputs. The two replacement model files were generated as new 198-row raw outputs.

## 10. Scoring

Compliant-panel scoring cache:

```text
cache/gpqa_diamond/gpqa_minimal_open_local_amended_v2_compliant/
```

- Prediction rows: 1584 / 1584
- Model count: 8
- Aggregate prediction file: `cache/gpqa_diamond/gpqa_minimal_open_local_amended_v2_compliant/predictions_full_answer_only_v2.jsonl`

## 11. Extraction Audit

Compliant-panel extraction summary: `results/gpqa_diamond/input_validation/compliant_panel_v2_extraction_audit_summary.json`

- Extraction success: 0.994
- Threshold: 0.950
- Invalid outputs: 10
- Ambiguous outputs: 5
- Threshold status: pass

## 12. Alignment

Compliant-panel alignment summary: `results/gpqa_diamond/input_validation/compliant_panel_v2_alignment_summary.json`

- Status: `pass`
- Models: 8
- Predictions: 1584
- Missing items: 0
- Extra items: 0
- Duplicate predictions: 0
- Invalid answer labels: 0

## 13. Matrix Status

Matrix built:

```text
cache/gpqa_diamond/gpqa_minimal_open_local_amended_v2_compliant/matrix_full_answer_only_v2.csv
```

The original panel's `matrix_full_answer_only_v2.csv` was not replaced.

## 14. Manifest

Manifest generated: `results/gpqa_diamond/input_validation/audit_manifest.json`

The manifest includes hashes for the item file, amended preregistration, compliance decision memo, compliance config, compliant panel config, prediction files, matrix, replacement reports, and archive manifest.

## 15. Go/No-Go Result

Amended compliant-panel go/no-go status: `go`

- Primary full variant: `full_answer_only_v2`
- Model count check: pass
- Extraction threshold check: pass at 0.994
- Matrix check: pass

## 16. Dry-Run-Real Result

Dry-run-real status: `ready`

Dry-run-real was only a scheduling/artifact shell. No diagnostics were interpreted.

## 17. Diagnostics Allowed Later

A later phase may run amended primary full-path diagnostics only after explicitly starting the real audit interpretation phase. This phase did not interpret any diagnostic result.

## 18. Diagnostics Blocked

- Shortcut and prompt-sensitivity diagnostics remain blocked until non-full variants have complete 8-model coverage under the active protocol.
- Original `full` prompt diagnostics remain archived as protocol-development artifacts.
- Paper-grade claims remain blocked for this preliminary local panel.

## 19. Deviations and Risks

- The threshold was not lowered.
- Model exclusion/replacement was based only on answer-extraction compliance.
- Accuracy, diagnostic outcomes, model ranking, and item-quality flags were not used.
- Original non-compliant outputs remain archived.
- Replacement-panel results are preliminary local workflow artifacts, not benchmark validity claims.

## 20. Do-Not-Claim List

- Do not claim GPQA has any validity issue.
- Do not claim shortcut, contamination, saturation, item-quality, or model-ranking evidence.
- Do not treat extraction-compliance exclusion as performance filtering.
- Do not mix excluded-model artifacts with the compliant panel cache.
- Do not interpret diagnostics from this phase.

## 21. Next Commands

Dry-run shell already passed. The next interpretation phase, if explicitly started later, should use:

```bash
python3 -m valideval audit \
  --benchmark gpqa_diamond \
  --panel gpqa_minimal_open_local_amended_v2_compliant \
  --config configs/audits/gpqa_diamond_amended_v2.yaml \
  --from-cache \
  --input-validated-only
```

Do not run that command until the next phase explicitly authorizes diagnostic interpretation.

## Phase 28 Update

The compliant replacement panel was used for the first preliminary amended-v2 audit after go/no-go was reconfirmed as `go`. The audit ran from cache and used only `full_answer_only_v2` artifacts from `gpqa_minimal_open_local_amended_v2_compliant`.

The model exclusion/replacement decision remains extraction-compliance-only. It was not based on accuracy, model ranking, item-level diagnostic results, or benchmark-validity conclusions.

Primary prompt-variant diagnostics that require complete non-full coverage remain blocked.
