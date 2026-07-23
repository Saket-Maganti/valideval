# Claims

Canonical claims live in `CLAIMS_LEDGER_NEURIPS.md`. Unsupported claims should not appear in the
paper except as future work or explicitly blocked placeholders.

MMLU-Redux claim status:

- Allowed: MMLU-Redux is a negative/weak external-validation stress test documented in `paper/appendices/mmlu_redux_evidence_appendix.md`.
- Allowed: ValidEval can run sanitized broad, issue-specific, subject-normalized, and subject-matched-null validation surfaces over local HELM MMLU artifacts.
- Allowed: Broad/proxy diagnostics did not strongly recover structurally aligned MMLU-Redux labels, and the claims ledger blocks detection-success claims.
- Not allowed: MMLU error-detection success, validation claims for MMLU-Redux labels, direct/hash alignment claims, or global MMLU validity/invalidity claims.

Main paper claim status:

- Allowed: ValidEval is an offline-safe framework for validating benchmark-validity diagnostics before using them to support benchmark claims.
- Allowed: The active public HELM MMLU wide panel has 39 models and 14,042 items, and the panel-size blocker is cleared under the current panel-validity artifact.
- Allowed: Proxy IRT artifacts exist for the active MMLU panel; full 2PL has not run.
- Allowed: Real-panel ranking/disagreement artifacts exist for the active MMLU panel.
- Allowed: Subject-level rank sensitivity is artifact-backed under the current panel and protocol.
- Allowed: Proxy diagnostic-weighted ranking remains close to accuracy ranking in the current run.
- Allowed: Historical 3-model MMLU files are provenance only, not the active panel.
- Allowed: ValidEval has a legacy controlled synthetic harness that is useful as a wiring/sanity-check surface.
- Allowed: Current synthetic AUCs are historical artifacts and are not treated as independent diagnostic-validation evidence.
- Allowed: Cross-flaw and held-out artifacts exist, but their mixed results and legacy coupling require diagnostic-specific claim-gating language.
- Allowed: False-positive/null controls and materiality labels can be reported only as legacy synthetic-generator sanity checks.
- Allowed: Decoupled synthetic validation is a scaffolded future requirement, not a completed result.
- Required state: diagnostic-validation evidence remains `RESULT_REQUIRED` until a decoupled flaw-agnostic harness or stronger real external-validation artifact exists.
- Allowed: A preregistered no-run plan exists for investigating cross-flaw off-target activations and held-out transfer drops.
- Not allowed: claiming current synthetic AUCs as independent diagnostic-validation evidence; claiming incomplete synthetic experiments as completed; claiming proxy IRT is full 2PL; treating MMLU-Redux as a success case.
- Not allowed: treating the preregistered plan as executed evidence; all-diagnostic generalization; real-benchmark validity conclusions from synthetic evidence alone; real benchmark error-detection claims; second-benchmark evidence; or NeurIPS readiness.

No-run build scaffold status:

- Allowed: The repo contains dry-run preflights for real-panel ranking/disagreement/subject-instability, real-panel baselines, Ollama panel metadata, second-benchmark schemas, calibration/logprob schemas, power/materiality planning, and MMLU-Redux direct/hash alignment.
- Allowed: These preflights can be cited as build readiness only.
- Not allowed: treating dry-run manifests as real-panel findings, calibration evidence, power evidence, second-benchmark transfer, or MMLU-Redux detection success.
- Required placeholders: `[RESULT REQUIRED: real-panel ranking audit]`, `[RESULT REQUIRED: diagnostic-disagreement audit]`, `[RESULT REQUIRED: subject-instability audit]`, `[RESULT REQUIRED: accuracy-only baseline]`, `[RESULT REQUIRED: random subset baseline]`, `[RESULT REQUIRED: subject-stratified baseline]`, `[RESULT REQUIRED: naive disagreement baseline]`, `[RESULT REQUIRED: diagnostic-vs-diagnostic baseline]`, `[RESULT REQUIRED: second benchmark real-panel audit]`, `[RESULT REQUIRED: synthetic-harness power analysis]`, and `[RESULT REQUIRED: materiality threshold validation]`.

Do not claim:

- All diagnostics generalize across flaw families.
- Synthetic validation proves real benchmark validity.
- Current synthetic AUCs provide independent diagnostic-validation evidence.
- Cross-flaw specificity is solved.
- Held-out transfer is solved.
- ValidEval detects real benchmark errors.
- MMLU-Redux validates the diagnostics.
- GPQA establishes broad validity evidence.
- The active MMLU panel has only 3 models.
- Second-benchmark evidence, full 2PL, direct/hash MMLU-Redux alignment, or NeurIPS readiness is established.
