# Preregistered Investigation Plan: Cross-Flaw Specificity and Held-Out Transfer

## 1. Motivation

The current synthetic diagnostic-validation evidence is intentionally mixed. Controlled synthetic
flaw detection is supported for specific diagnostic/flaw pairs, but cross-flaw specificity and
held-out transfer remain weak because existing artifacts show 7 strong off-target activations and 3
non-paper-eligible held-out transfer families. This plan preregisters how to investigate those
failures before any confirmatory rerun.

This is a planning artifact only. It does not execute experiments, recompute metrics, tune
thresholds, or change evidence states.

## 2. Current Evidence State

- `SUPPORTED`: controlled synthetic flaw detection; synthetic FPR/null controls.
- `WEAK`: cross-flaw specificity, held-out generator transfer, materiality, toy-only power.
- `BLOCKED`: numeric calibration without confidence/logprob outputs.
- `NOT_RUN`: synthetic-to-real threshold validation.
- MMLU-Redux remains a weak/negative external-validation stress test.
- GPQA remains protocol/demo evidence unless wide-panel readiness exists.

## 3. Failure Cases Under Investigation

Cross-flaw off-target cases:

- CF-01: `shortcut` on off-target `too_easy_saturation`, AUC 1.0.
- CF-02: `distractor_quality` on off-target `prompt_format_fragility`, AUC 0.9928385416666666.
- CF-03: `distractor_quality` on off-target `too_easy_saturation`, AUC 0.9694010416666666.
- CF-04: `redundancy` on off-target `shortcut_signal`, AUC 0.9791666666666666.
- CF-05: `saturation` on off-target `shortcut_signal`, AUC 0.875.
- CF-06: `saturation` on off-target `prompt_format_fragility`, AUC 0.875.
- CF-07: `saturation` on off-target `extraction_ambiguity`, AUC 0.875.

Held-out transfer cases:

- HO-01: `shortcut`, `shortcut_signal` to `keyword_artifact`, AUC drop 0.4281684027777778.
- HO-02: `distractor_quality`, `dead_distractors` to `answer_length_artifact`, AUC drop 0.1410590277777778.
- HO-03: `redundancy`, `redundancy` to `context_leakage`, AUC drop 0.48958333333333337.

## 4. Hypotheses

Primary claim-status hypotheses:

- H3: Held-out transfer drops indicate generator-detector coupling, meaning controlled synthetic sensitivity does not automatically imply generalization.
- H4: Diagnostics should be marked `SUPPORTED` only when they pass within-family sensitivity, cross-flaw specificity, and held-out transfer gates.

Secondary explanatory hypotheses:

- H1: Some off-target activations represent real shared latent flaw structure rather than detector failure.
- H2: Some off-target activations are false positives caused by detector threshold leakage or generator artifacts.
- H5: Diagnostics that fail specificity or transfer gates may still be useful as exploratory review-queue heuristics, but not as claim-supporting evidence.

## 5. Planned Analyses

1. Freeze the current failure-case list before any rerun.
2. Re-run the cross-flaw matrix only in a future approved phase using the same preregistered config,
   output directory, and decision rules.
3. Re-run held-out transfer only in a future approved phase using the same preregistered config,
   output directory, and decision rules.
4. Compare each failure case against the existing artifact row by ID, diagnostic, flaw family, and
   metric name.
5. Classify each off-target activation as one of:
   - shared latent flaw structure,
   - detector overbreadth,
   - generator artifact,
   - threshold/null-control issue,
   - undetermined.
6. Classify each held-out drop as one of:
   - passes transfer,
   - weak transfer,
   - transfer failure,
   - undetermined due to missing artifact.
7. Preserve all failures in the report even if later runs improve.

## 6. Primary Metrics

- Intended-flaw ROC AUC.
- Off-target ROC AUC.
- Held-out ROC AUC.
- Transfer drop: original AUC minus held-out AUC.
- Clean false-positive rate.
- Paper-eligibility flag under preregistered rules.

## 7. Secondary Metrics

- PR AUC where emitted by the diagnostic-validation runner.
- Specificity where emitted by the cross-flaw matrix.
- Materiality status where emitted by the synthetic validation summary.
- Null/FPR-control status.
- Diagnostic downgrade reason.
- Review-queue-only eligibility.

## 8. Decision Rules

`SUPPORTED`:

- passes intended-flaw sensitivity gate,
- does not show material off-target activation,
- passes held-out transfer gate,
- satisfies null/FPR control.

`WEAK`:

- detects intended flaw,
- but has off-target activation or transfer instability.

`BLOCKED`:

- fails intended sensitivity,
- or has severe off-target activation,
- or fails held-out transfer,
- or lacks required artifact.

`NOT_RUN`:

- no matching artifact exists.

`RESULT_REQUIRED`:

- planned but missing metric/artifact.

Preregistered numeric gates for future runs:

- Intended-flaw sensitivity gate: AUC >= 0.80.
- Material off-target activation: off-target AUC >= 0.80.
- Held-out transfer gate: held-out AUC >= 0.75 and transfer drop <= 0.25.
- Null/FPR gate: clean FPR <= 0.10 unless a stricter diagnostic-specific gate is preregistered.

These gates match the current cross-flaw and held-out eligibility logic exposed by the existing
artifacts and source inspection. They must not be changed after seeing future results.

Minimum passing and failure thresholds:

| Gate | Minimum passing threshold | Failure/blocking threshold | Claim consequence |
|---|---|---|---|
| Intended-flaw sensitivity | Intended-flaw AUC >= 0.80 | Intended-flaw AUC < 0.80 or missing artifact | Cannot support the intended diagnostic/flaw claim |
| Cross-flaw specificity | No material off-target activation: off-target AUC < 0.80 for non-intended flaw cells | Any unaccounted off-target AUC >= 0.80 | Cannot claim diagnostic specificity; keep `WEAK` or block broad claim |
| Held-out transfer | Held-out AUC >= 0.75 and transfer drop <= 0.25 | Held-out AUC < 0.75, transfer drop > 0.25, or missing held-out artifact | Cannot claim generator transfer |
| Null/FPR control | Clean FPR <= 0.10 unless a stricter preregistered gate applies | Clean FPR > 0.10 or missing clean/null artifact | Cannot claim controlled false-positive behavior |
| Materiality | Use the materiality status emitted by the frozen validation summary | Missing or non-preregistered materiality threshold | Materiality remains `RESULT_REQUIRED` or `WEAK`; AUC alone cannot establish practical importance |

Multiple-comparison and family-level claim rule:

Because multiple diagnostics and flaw families are evaluated, a diagnostic cannot be upgraded to
`SUPPORTED` solely from one favorable cell. A `SUPPORTED` label requires consistency across the
intended-flaw sensitivity gate, cross-flaw specificity gate, held-out transfer gate, and null/FPR
gate. Isolated favorable cells are reported as exploratory unless they satisfy the preregistered
family-level decision rule.

## 9. What Would Change the Evidence State?

| Current state | Upgrade condition | Downgrade/block condition | Claim consequence |
|---|---|---|---|
| `WEAK` cross-flaw specificity | Off-target activations fall below the materiality threshold under the confirmatory run | Off-target activations remain material or lack a preregistered shared-family interpretation | Cannot claim diagnostic specificity |
| `WEAK` held-out transfer | Held-out AUC/sensitivity remains above the preregistered threshold and transfer drop stays within gate | Held-out drops remain near chance or exceed the preregistered drop threshold | Cannot claim generator transfer |
| `SUPPORTED` controlled sensitivity | Reconfirmed on intended flaw with null/FPR control | Fails intended sensitivity or null control | Downgrade to `WEAK` or `BLOCKED` |
| `WEAK` materiality | Materiality is emitted under a frozen threshold and aligns with a passing diagnostic gate | Materiality is missing, non-preregistered, or contradicted by failed gates | Cannot use separability as an importance claim |
| `BLOCKED` calibration | Confidence/logprob outputs exist and calibration metrics are emitted under a preregistered protocol | Confidence/logprob outputs remain unavailable | Numeric calibration claims remain blocked |

## 10. Stopping Rules

- Stop after the preregistered config completes once for cross-flaw and once for held-out transfer.
- Do not add generators, remove failure cases, or change thresholds within the confirmatory run.
- If a required artifact is missing or malformed, mark the affected case `RESULT_REQUIRED` or
  `BLOCKED`; do not repair the metric silently.
- If runtime or environment issues occur, report the partial artifact state and stop.

## 11. Claim Rules

- A diagnostic can support a claim only for the exact flaw family and protocol that passes all gates.
- Off-target activation keeps the diagnostic at `WEAK` unless a preregistered latent-structure
  analysis justifies a narrower shared-family claim.
- Held-out transfer failure keeps the diagnostic at `WEAK` or `BLOCKED` for generalization claims.
- Review-queue heuristic language is allowed for diagnostics that are sensitive but fail specificity
  or transfer gates.
- Real-benchmark validity conclusions remain blocked without separate real-benchmark validation.
- MMLU-Redux remains weak/negative external-validation evidence.
- GPQA remains protocol/demo evidence unless wide-panel readiness exists.

Do not claim:

- All diagnostics generalize across flaw families.
- Synthetic validation proves real benchmark validity.
- Cross-flaw specificity is solved.
- Held-out transfer is solved.
- ValidEval detects real benchmark errors.
- MMLU-Redux validates the diagnostics.
- GPQA establishes broad validity evidence.

## 12. Anti-Tuning Guardrails

- Freeze this plan before running confirmatory commands.
- Use fixed configs and output directories.
- Do not change AUC, transfer-drop, or FPR gates after inspecting results.
- Do not remove off-target failures from the denominator.
- Do not rename diagnostics or flaw families to make failures disappear.
- Report all previous failure cases side by side with confirmatory outcomes.
- Treat improvements as confirmatory only if they occur under the frozen plan.

## 13. Expected Outputs

- `results/synthetic/cross_flaw_confirmatory/cross_flaw_matrix.json`
- `results/synthetic/cross_flaw_confirmatory/cross_flaw_matrix.csv`
- `results/synthetic/cross_flaw_confirmatory/summary.md`
- `results/synthetic/heldout_confirmatory/heldout_transfer.json`
- `results/synthetic/heldout_confirmatory/heldout_transfer.csv`
- `results/synthetic/heldout_confirmatory/summary.md`
- A follow-up claim-status report that keeps failures visible.

## 14. Commands To Run Later

```bash
# Future only - do not run in this phase.
python3 -m valideval validate-diagnostics-cross-flaw \
  --config configs/validation/synthetic_default.yaml \
  --output results/synthetic/cross_flaw_confirmatory
```

```bash
# Future only - do not run in this phase.
python3 -m valideval validate-diagnostics-heldout \
  --config configs/validation/heldout_default.yaml \
  --output results/synthetic/heldout_confirmatory
```

## 15. Compute Estimate

The static source and config inspection imply:

- Cross-flaw confirmatory run: 8 diagnostics x 8 flaw families = 64 validation cells.
- Held-out confirmatory run: 6 families x 2 generator variants = 12 validation cells.
- Configured local scale: strength grid `[0.0, 1.0]`, seed `[0]`, and 48 items for the small-run
  configs.

These are local synthetic runs and should not require network access, paid APIs, or model inference.
Actual runtime should be reported after an approved run rather than estimated here as evidence.

## 16. Risks and Mitigations

| Risk | Mitigation |
|---|---|
| Off-target activation is actually shared latent flaw structure | Report as shared-family evidence only if preregistered analysis supports that interpretation |
| Off-target activation is generator artifact | Downgrade or mark non-paper-eligible until a less coupled generator passes |
| Held-out transfer drops persist | Keep diagnostic at `WEAK` or `BLOCKED` for generalization claims |
| Future run changes because thresholds are tuned | Freeze gates and configs before running |
| Missing or malformed artifacts | Mark `RESULT_REQUIRED` or `BLOCKED`; do not infer metrics |
| Reviewer overreads synthetic success | Keep synthetic-to-real caveat next to all supported synthetic claims |
