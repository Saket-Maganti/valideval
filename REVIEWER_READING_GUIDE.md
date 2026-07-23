# Reviewer Reading Guide

This guide gives a compact path through the `valideval` reviewer packet. It prioritizes claim
boundaries, evidence states, and preregistration before implementation details.

## 1. `paper/abstract.md`

Start here for the intended paper-level thesis and contribution shape. Treat it as a claim summary,
not as a substitute for the evidence ledgers.

## 2. `paper/introduction.md`

Read this for the framing: ValidEval argues that benchmark validity is multidimensional and should
not be collapsed into accuracy or a single scalar validity score.

## 3. `paper/claims.md`

Use this as the first claim boundary check. It lists what is allowed, what is blocked, and how
MMLU-Redux and synthetic validation should be interpreted.

Also check `NO_RUN_RULES_AND_EVIDENCE_STATE_LOCK.md` before reading dry-run manifests. It freezes
which surfaces are supported, weak, blocked, not run, or result-required.

## 4. `paper/diagnostic_validation.md`

Read this for the synthetic diagnostic-validation evidence surface. It documents controlled
synthetic sensitivity, cross-flaw specificity risks, held-out generator-transfer risks, null/FPR
controls, materiality caveats, and remaining `[RESULT REQUIRED]` placeholders.

## 5. `SYNTHETIC_EVIDENCE_STATUS_TABLE.md`

Use this table to map each synthetic evidence block to its current state. The important statuses are
unchanged: cross-flaw specificity is `WEAK`, held-out generator transfer is `WEAK`, calibration is
`BLOCKED`, synthetic-to-real threshold validation is `NOT_RUN`, and confirmatory follow-up is
`RESULT_REQUIRED`.

## 6. `MMLU_EVIDENCE_GATE_REPORT.md`

Read this for the external-validation gate. The MMLU-Redux result remains weak/negative and
protocol-scoped; it is not evidence that the diagnostics detect MMLU errors.

## 7. `paper/appendices/mmlu_redux_reviewer_summary.md`

Use this as the short reviewer-safe summary of the MMLU-Redux stress test. It is sanitized and does
not include raw MMLU question text or answer-choice text.

## 8. `PREREGISTERED_CROSS_FLAW_HELDOUT_INVESTIGATION_PLAN.md`

Read this before interpreting any future confirmatory synthetic result. It freezes the failure-case
list, metrics, gates, stopping rules, and anti-tuning rules for later execution.

## 9. `STATIC_CONFIRMATORY_PREFLIGHT_REPORT.md`

Use this to verify that the confirmatory run surface passed static preflight. It confirms file and
path readiness only; it does not mean validation ran.

## 10. `RUNBOOK_CONFIRMATORY_SYNTHETIC_VALIDATION.md`

Read this only after the preregistration and preflight reports. It explains how a future approved
confirmatory run should be launched, interpreted, and kept reviewer-safe.

## After The Core Reading Path

For implementation details, inspect:

- `src/valideval/`
- `configs/validation/`
- `scripts/preflight_confirmatory_synthetic.py`
- `scripts/make_reviewer_packet.py`
- `tests/test_preflight_confirmatory_synthetic.py`
- `tests/test_make_reviewer_packet.py`

For release boundaries, inspect:

- `REVIEWER_PACKET_MANIFEST.md`
- `ARTIFACT_EXCLUSION_POLICY.md`
- `RELEASE_READINESS_CHECKLIST.md`
- `NO_RUN_RELEASE_AUDIT.md`

For build-only preflight scaffolds, inspect:

- `NO_RUN_DRYRUN_SURFACE_AUDIT.md`
- `REAL_PANEL_FINDING_ENGINE_BUILD_AUDIT.md`
- `REAL_PANEL_BASELINES_PLAN.md`
- `CALIBRATION_INFRASTRUCTURE_BUILD_REPORT.md`
- `POWER_AND_MATERIALITY_ANALYSIS_PLAN.md`
- `MMLU_REDUX_DIRECT_HASH_ALIGNMENT_PLAN.md`
- `MASTER_LATER_RUN_PLAN.md`

If the reviewer packet is rebuilt after the dry-run audit, the small
`results/no_run_dryrun_surface/*.manifest.json` files are packaging evidence for dry-run execution
only. They are not empirical results.
