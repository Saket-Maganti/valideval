# Paper Narrative Consistency Audit

## 1. Executive Summary

The main paper narrative now treats synthetic diagnostic validation as the positive evidence surface
and HELM MMLU / MMLU-Redux as a weak/negative external-validation stress test. The paper-facing
files no longer frame MMLU-Redux as a centerpiece or success case. The narrative emphasizes
evidence-gating discipline: broad/proxy diagnostics did not strongly recover structurally aligned
MMLU-Redux labels, subject-normalized evidence weakened the raw label-error signal, and the claims
ledger blocks detection-success claims.

No validation was rerun. No empirical values were changed. No raw MMLU question text or answer-choice
text was added.

## 2. Files Reviewed

Requested files reviewed:

- `paper/main.tex`
- `paper/abstract.md`
- `paper/introduction.md`
- `paper/experiments.md`
- `paper/limitations.md`
- `paper/claims.md`
- `paper/related_work.md`
- `paper/appendices/mmlu_redux_evidence_appendix.md`
- `paper/appendices/mmlu_redux_reviewer_summary.md`
- `CLAIMS_LEDGER_NEURIPS.md`
- `MMLU_EVIDENCE_GATE_REPORT.md`

Requested files missing:

- `paper/results.md`
- `paper/discussion.md`

Additional paper-structure files reviewed because `paper/main.tex` or the paper directory referenced
them:

- `paper/sections/01_introduction.tex`
- `paper/sections/02_related_work.tex`
- `paper/sections/03_validity_framework.tex`
- `paper/sections/04_toolkit.tex`
- `paper/sections/05_audit_protocol.tex`
- `paper/sections/06_results.tex`
- `paper/sections/07_analysis.tex`
- `paper/sections/08_limitations.tex`
- `paper/sections/09_ethics_broader_impact.tex`
- `paper/sections/10_conclusion.tex`
- `paper/CLAIMS_LEDGER.md`
- `paper/NEURIPS_SUBMISSION_PLAN.md`
- `paper/external_validation.md`
- `paper/diagnostic_validation.md`
- `paper/related_work_map.md`
- `paper/gpqa_protocol_demo.md`

## 3. Overclaim Search Results

The requested risky-phrase scan was run over `paper`, `CLAIMS_LEDGER_NEURIPS.md`, and
`MMLU_EVIDENCE_GATE_REPORT.md`.

Initial risky or quote-shaped language found:

- `paper/CLAIMS_LEDGER.md` and `paper/sections/07_analysis.tex` used proof-shaped wording in
  negative guardrail sentences.
- `paper/related_work_map.md` described the MMLU-Redux relation as ValidEval validating diagnostic
  flags against labels.
- `paper/external_validation.md` and `paper/NEURIPS_SUBMISSION_PLAN.md` repeated exact blocked
  MMLU detection/validation claims inside "not allowed" wording.
- Several planning surfaces placed MMLU-Redux too close to the positive evidence story.

After edits, the requested risky-phrase scan returns no matches.

## 4. Edits Made

- Filled `paper/main.tex` and `paper/abstract.md` with the cautious ValidEval framework story.
- Reframed `paper/introduction.md` and `paper/sections/01_introduction.tex` around diagnostic
  validation, evidence gates, claims ledgers, and a weak/negative MMLU-Redux stress test.
- Reorganized `paper/experiments.md` and `paper/sections/06_results.tex` into five blocks:
  synthetic diagnostic validation, cross-flaw specificity, held-out generator validation,
  HELM MMLU / MMLU-Redux external stress test, and GPQA protocol case study.
- Updated `paper/limitations.md` and `paper/sections/08_limitations.tex` to include structural
  MMLU-Redux alignment, weak/negative MMLU-Redux evidence, proxy-only IRT, synthetic circularity,
  preliminary real-benchmark findings, domain-pack limits, and GPQA protocol-only status.
- Tightened `paper/claims.md`, `paper/CLAIMS_LEDGER.md`, `paper/external_validation.md`,
  `paper/diagnostic_validation.md`, `paper/related_work_map.md`, and
  `paper/NEURIPS_SUBMISSION_PLAN.md`.
- Rephrased exact overclaim-shaped blocked claims into claim categories.

## 5. Main Narrative After Edits

ValidEval is presented as an offline-safe framework for validating benchmark-validity diagnostics
before using them to support benchmark claims. The positive evidence path is the
diagnostic-validation harness: controlled synthetic flaw injection, cross-flaw specificity, held-out
generator validation, false-positive/error-control checks, and materiality reporting.

MMLU-Redux is explicitly not the positive evidence centerpiece. It is a real external stress test
showing that broad/proxy diagnostics do not automatically validate against documented issue labels
and that the claims ledger blocks unsupported detection-success claims.

## 6. Claims Allowed

- ValidEval treats validity as multidimensional rather than a scalar benchmark-health score.
- ValidEval provides an offline-safe diagnostic-validation and audit-artifact workflow.
- The paper can present the legacy synthetic harness as wiring/sanity-check context only, with
  decoupled diagnostic-validation blocks marked as `[RESULT REQUIRED]`.
- MMLU-Redux can be described as a weak/negative external-validation stress test.
- Broad/proxy diagnostics did not strongly recover structurally aligned MMLU-Redux labels under the
  documented protocol.
- A narrow raw label-error review-queue signal appears at some top-k cutoffs, but remains
  preliminary.

## 7. Claims Blocked

- MMLU error-detection success by ValidEval.
- Global MMLU validity or invalidity conclusions.
- MMLU-Redux label-validation success.
- External-validation success for proxy IRT flags as MMLU-error detectors.
- A success-story interpretation of the MMLU-Redux stress test.
- GPQA local-panel findings support broad validity evidence.
- Domain packs are paper-validated without separate support.
- Synthetic validation establishes real-benchmark diagnostic performance without cross-flaw,
  held-out, and false-positive/error-control evidence.

## 8. Remaining [RESULT REQUIRED] Placeholders

- `paper/diagnostic_validation.md`: synthetic-harness power analysis.
- `paper/diagnostic_validation.md`: numeric calibration with confidence/logprob outputs.
- `paper/diagnostic_validation.md`: human-reviewed real-benchmark threshold calibration.
- `paper/gpqa_protocol_demo.md`: GPQA wide-panel readiness if used.

## 9. Remaining Reviewer Risks

- The paper is still structurally sparse in several LaTeX sections.
- `paper/results.md` and `paper/discussion.md` do not exist, so reviewers may need to rely on
  `paper/sections/06_results.tex` and `paper/sections/07_analysis.tex`.
- Synthetic evidence can still be read as circular unless mixed cross-flaw specificity and held-out
  generator results are reported with their off-target activations and transfer drops.
- MMLU-Redux alignment remains structural rather than direct-id or hash-confirmed.
- The narrow raw label-error review-queue signal may be overread unless kept next to the
  subject-normalized weakening and blocked-claim language.

## 10. Next Recommended Experiment Block

Complete the missing synthetic support blocks next: synthetic-harness power analysis, numeric
calibration with confidence/logprob outputs, and human-reviewed real-benchmark threshold calibration.
Keep MMLU-Redux framed as a weak/negative stress test.
