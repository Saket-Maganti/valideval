# Confirmatory Run Command Manifest

## 1. Purpose

This manifest records the exact future commands for the preregistered synthetic cross-flaw and
held-out confirmatory validation phase. It is a build-only artifact. It does not execute
experiments, generate synthetic items, recompute metrics, tune thresholds, run inference, download
artifacts, or upgrade any evidence state.

The goal is to make a later user-approved execution phase reproducible and reviewer-safe while
preserving the current `WEAK`, `BLOCKED`, and `RESULT_REQUIRED` statuses until confirmatory
artifacts actually exist.

## 2. Frozen Source Documents

The future run must be governed by these documents as they exist before execution:

- `PREREGISTERED_CROSS_FLAW_HELDOUT_INVESTIGATION_PLAN.md`
- `PREREGISTRATION_REVIEW_AUDIT.md`
- `CROSS_FLAW_AND_HELDOUT_FAILURE_CASES.md`
- `SYNTHETIC_EVIDENCE_STATUS_TABLE.md`
- `SYNTHETIC_VALIDATION_ARTIFACT_INVENTORY.md`
- `SYNTHETIC_VALIDATION_NARRATIVE_AUDIT.md`
- `CLAIMS_LEDGER_NEURIPS.md`
- `paper/CLAIMS_LEDGER.md`
- `paper/diagnostic_validation.md`
- `paper/experiments.md`
- `paper/limitations.md`
- `paper/claims.md`
- `paper/appendices/cross_flaw_heldout_preregistration_note.md`

The MMLU-Redux appendix and reviewer summary remain weak/negative external-validation surfaces, not
success evidence:

- `paper/appendices/mmlu_redux_evidence_appendix.md`
- `paper/appendices/mmlu_redux_reviewer_summary.md`

## 3. Commands To Run Later

Do not run these commands in the build-only phase. They are future commands for a later explicit
execution approval.

```bash
# Future only - do not run during build-only polish.
python3 -m valideval validate-diagnostics-cross-flaw \
  --config configs/validation/synthetic_default.yaml \
  --output results/synthetic/cross_flaw_confirmatory
```

```bash
# Future only - do not run during build-only polish.
python3 -m valideval validate-diagnostics-heldout \
  --config configs/validation/heldout_default.yaml \
  --output results/synthetic/heldout_confirmatory
```

After those future commands complete, a separate build step should fill the claim-status report from
actual artifacts only. Until then, the report template must keep `[RESULT REQUIRED]` markers.

## 4. Expected Inputs

- `configs/validation/synthetic_default.yaml`
- `configs/validation/heldout_default.yaml`
- Frozen failure-case inventory in `CROSS_FLAW_AND_HELDOUT_FAILURE_CASES.md`
- Frozen decision rules in `PREREGISTERED_CROSS_FLAW_HELDOUT_INVESTIGATION_PLAN.md`
- Existing claims ledgers that preserve blocked-claim language
- Local repository checkout with the `valideval` package installed in dev mode

No paid APIs, downloads, model inference, or external data acquisition are required by the future
synthetic confirmatory commands.

## 5. Expected Outputs

Future cross-flaw outputs:

- `results/synthetic/cross_flaw_confirmatory/cross_flaw_matrix.json`
- `results/synthetic/cross_flaw_confirmatory/cross_flaw_matrix.csv`
- `results/synthetic/cross_flaw_confirmatory/summary.md`

Future held-out outputs:

- `results/synthetic/heldout_confirmatory/heldout_transfer.json`
- `results/synthetic/heldout_confirmatory/heldout_transfer.csv`
- `results/synthetic/heldout_confirmatory/summary.md`

Future report surfaces to fill from those outputs:

- `templates/reports/CROSS_FLAW_CONFIRMATORY_REPORT_TEMPLATE.md`
- `templates/reports/HELDOUT_CONFIRMATORY_REPORT_TEMPLATE.md`
- `templates/reports/SYNTHETIC_CONFIRMATORY_CLAIM_STATUS_REPORT_TEMPLATE.md`
- `templates/reports/SYNTHETIC_CONFIRMATORY_REVIEWER_APPENDIX_TEMPLATE.md`

## 6. Runtime Estimate

Reviewer-facing estimate only:

- Cross-flaw confirmatory run: 30-90 minutes CPU time.
- Held-out confirmatory run: 10-60 minutes CPU time.
- GPU: not expected.
- Network: not expected.
- Paid API calls: not expected.

Actual runtime must be recorded only after an approved run. Runtime is operational metadata, not
evidence of diagnostic validity.

## 7. Failure Handling

- Stop after one frozen cross-flaw run and one frozen held-out run.
- If a required config is missing, stop and report `RESULT_REQUIRED`.
- If an output is missing or malformed, mark the affected gate `RESULT_REQUIRED` or `BLOCKED`.
- If runtime fails partway through, preserve partial artifacts and report what completed.
- Do not repair metrics silently.
- Do not remove failure cases.
- Do not rerun with tuned thresholds.
- Do not add or remove generators after seeing results.

## 8. Evidence-State Rules

Current states remain unchanged until future artifacts exist:

- Controlled synthetic flaw detection: `SUPPORTED` only for generator-scoped sensitivity already
  documented in existing artifacts.
- Cross-flaw specificity: `WEAK`.
- Held-out generator transfer: `WEAK`.
- Materiality thresholding: `WEAK`.
- Numeric calibration: `BLOCKED` without confidence/logprob outputs.
- Synthetic-to-real threshold validation: `NOT_RUN`.
- Cross-flaw / held-out follow-up plan: `RESULT_REQUIRED` until future confirmatory outputs exist.
- MMLU-Redux: weak/negative external validation.
- GPQA: protocol/demo unless wide-panel evidence exists.

## 9. Claims Allowed After Run

Only if the future run produces passing artifacts under the frozen gates:

- A diagnostic-specific synthetic claim for the exact flaw family and protocol that passes intended
  sensitivity, cross-flaw specificity, held-out transfer, and null/FPR gates.
- A narrower shared-family interpretation for off-target activation only if preregistered analysis
  supports that interpretation.
- A review-queue heuristic claim for diagnostics that are sensitive but fail specificity or transfer
  gates.
- A statement that the confirmatory run was executed under the preregistered protocol, with all
  failures preserved.

## 10. Claims Blocked Unless Gates Pass

These claims remain blocked unless all relevant preregistered gates pass:

- All diagnostics generalize across flaw families.
- Synthetic validation proves real benchmark validity.
- Cross-flaw specificity is solved.
- Held-out transfer is solved.
- ValidEval detects real benchmark errors.
- MMLU-Redux validates the diagnostics.
- GPQA establishes broad validity evidence.
- A favorable single cell upgrades an entire diagnostic family.
- AUC alone establishes practical materiality.
- Synthetic thresholds transfer to real benchmarks.

## 11. Exact No-Tuning Rules

- Use only `configs/validation/synthetic_default.yaml` for the cross-flaw confirmatory run.
- Use only `configs/validation/heldout_default.yaml` for the held-out confirmatory run.
- Keep intended-flaw sensitivity gate at AUC >= 0.80.
- Keep material off-target activation gate at off-target AUC >= 0.80.
- Keep held-out transfer gate at held-out AUC >= 0.75 and transfer drop <= 0.25.
- Keep null/FPR gate at clean FPR <= 0.10 unless a stricter diagnostic-specific gate was already
  preregistered.
- Keep all seven cross-flaw failure cases and all three held-out transfer failure cases visible.
- Do not tune thresholds, generators, diagnostics, output paths, or denominators after seeing future
  results.
- Do not convert `[RESULT REQUIRED]` placeholders to evidence without corresponding artifacts.
