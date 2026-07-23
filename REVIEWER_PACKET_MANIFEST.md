# Reviewer Packet Manifest

## 1. Purpose

This manifest defines the safe reviewer packet for `valideval`. The packet is a documentation,
source, configuration, and claim-boundary bundle. It is not an empirical rerun and does not upgrade
any evidence state.

The packet is intended to help reviewers inspect the framework, paper-facing claims, preregistered
confirmatory plan, static preflight status, and weak/blocked evidence without bundling large raw
artifacts or restricted item text.

## 2. What This Packet Contains

- Paper scaffold and reviewer-facing paper notes.
- Claims ledgers and evidence-status summaries.
- Synthetic diagnostic-validation summaries and preregistration documents.
- MMLU-Redux weak/negative external-validation summaries.
- Static confirmatory preflight and build-only audit documents.
- No-run state lock and dry-run preflight build reports.
- Consolidated dry-run surface audit and small dry-run manifest JSON files, when the packet is
  rebuilt after the dry-run audit.
- Safe source code, tests, configs, schemas, templates, and scripts needed to inspect the toolkit.
- Release/readiness metadata that preserves blocked claims and `[RESULT REQUIRED]` placeholders.

## 3. What This Packet Does Not Claim

- It does not claim confirmatory synthetic validation has run.
- It does not claim cross-flaw specificity is solved.
- It does not claim held-out generator transfer is solved.
- It does not claim synthetic validation establishes real benchmark validity.
- It does not claim ValidEval detects real benchmark errors.
- It does not claim MMLU-Redux validates the diagnostics.
- It does not claim GPQA establishes broad validity evidence.
- It does not claim numeric calibration without confidence/logprob outputs.

## 4. Core Evidence Files

- `README.md`
- `CLAIMS_LEDGER_NEURIPS.md`
- `paper/CLAIMS_LEDGER.md`
- `paper/claims.md`
- `paper/diagnostic_validation.md`
- `paper/experiments.md`
- `paper/limitations.md`
- `SYNTHETIC_EVIDENCE_STATUS_TABLE.md`
- `SYNTHETIC_VALIDATION_ARTIFACT_INVENTORY.md`
- `SYNTHETIC_VALIDATION_NARRATIVE_AUDIT.md`
- `VALIDATOR_VALIDATION_STATUS.md`
- `NO_RUN_RULES_AND_EVIDENCE_STATE_LOCK.md`
- `CLAIMS_LEDGER_PAPER_SYNC_AUDIT.md`

## 5. MMLU-Redux Weak/Negative Stress Test Files

- `MMLU_EVIDENCE_GATE_REPORT.md`
- `MMLU_REDUX_WEAK_SIGNAL_DIAGNOSIS.md`
- `MMLU_REDUX_ISSUE_SPECIFIC_VALIDATION_REPORT.md`
- `MMLU_REDUX_SUBJECT_NORMALIZED_VALIDATION_REPORT.md`
- `MMLU_REDUX_LABEL_ERROR_NULL_CONFIRMATION_REPORT.md`
- `paper/appendices/mmlu_redux_evidence_appendix.md`
- `paper/appendices/mmlu_redux_reviewer_summary.md`

These files frame MMLU-Redux as weak/negative external validation. They are not detection-success
evidence and do not expose raw MMLU question text or answer choices.

## 6. Synthetic Validation Files

- `validation_reports/diagnostic_validation_summary.md`, if included separately by an approved
  artifact bundle.
- `validation_reports/diagnostic_validation_summary.json`, if included separately by an approved
  artifact bundle.
- `CROSS_FLAW_AND_HELDOUT_FAILURE_CASES.md`
- `SYNTHETIC_EVIDENCE_STATUS_TABLE.md`
- `SYNTHETIC_VALIDATION_ARTIFACT_INVENTORY.md`
- `SYNTHETIC_VALIDATION_NARRATIVE_AUDIT.md`

Generated result trees are excluded from the default reviewer packet. Reviewers should inspect the
sanitized summaries and, when needed, reproduce outputs from the documented commands.

## 7. Confirmatory Run Preregistration Files

- `PREREGISTERED_CROSS_FLAW_HELDOUT_INVESTIGATION_PLAN.md`
- `PREREGISTRATION_REVIEW_AUDIT.md`
- `CONFIRMATORY_RUN_COMMAND_MANIFEST.md`
- `RUNBOOK_CONFIRMATORY_SYNTHETIC_VALIDATION.md`
- `STATIC_CONFIRMATORY_PREFLIGHT_REPORT.md`
- `BUILD_ONLY_POLISH_AUDIT.md`
- `templates/reports/CROSS_FLAW_CONFIRMATORY_REPORT_TEMPLATE.md`
- `templates/reports/HELDOUT_CONFIRMATORY_REPORT_TEMPLATE.md`
- `templates/reports/SYNTHETIC_CONFIRMATORY_CLAIM_STATUS_REPORT_TEMPLATE.md`
- `templates/reports/SYNTHETIC_CONFIRMATORY_REVIEWER_APPENDIX_TEMPLATE.md`

The confirmatory run is preregistered and statically preflighted, but execution remains deferred.

## 8. Build/Preflight Files

- `scripts/preflight_confirmatory_synthetic.py`
- `tests/test_preflight_confirmatory_synthetic.py`
- `scripts/make_reviewer_packet.py`
- `tests/test_make_reviewer_packet.py`
- `NO_RUN_RELEASE_AUDIT.md`
- `NO_RUN_DRYRUN_SURFACE_AUDIT.md`
- `DRYRUN_AUDIT_PACKET_INCLUSION_DECISION.md`
- `REVIEWER_PACKET_POST_DRYRUN_AUDIT.md`
- `RELEASE_READINESS_CHECKLIST.md`
- `ARTIFACT_EXCLUSION_POLICY.md`
- `REAL_PANEL_FINDING_ENGINE_BUILD_AUDIT.md`
- `REAL_PANEL_BASELINES_PLAN.md`
- `CALIBRATION_INFRASTRUCTURE_BUILD_REPORT.md`
- `POWER_AND_MATERIALITY_ANALYSIS_PLAN.md`
- `MMLU_REDUX_DIRECT_HASH_ALIGNMENT_PLAN.md`
- `results/no_run_dryrun_surface/*.manifest.json`, if rebuilt after the dry-run audit

## 9. Paper Files

- `paper/abstract.md`
- `paper/introduction.md`
- `paper/method.md`
- `paper/related_work.md`
- `paper/diagnostic_validation.md`
- `paper/external_validation.md`
- `paper/gpqa_protocol_demo.md`
- `paper/claims.md`
- `paper/limitations.md`
- `paper/ethics_and_data.md`
- `paper/appendices/`
- `paper/sections/`
- `paper/tables/`
- `paper/figures/`

## 10. Large Artifacts Excluded

The default packet excludes:

- `cache/`
- `data/external/`
- `results/mmlu/`
- `results/synthetic/`
- all `*.jsonl` files
- `*.csv` files larger than 5 MB
- exploratory prompt-pack directories
- dry-run stdout captures such as `results/no_run_dryrun_surface/*.txt`
- all `results/` contents except the explicitly whitelisted
  `results/no_run_dryrun_surface/*.manifest.json`
- raw model outputs, raw HELM prediction dumps, large local caches, and generated result trees

These exclusions protect reviewer usability, avoid accidental raw-text exposure, and keep the packet
focused on reproducible source and sanitized reports.

## 11. Reviewer Reading Order

Recommended order:

1. `paper/abstract.md`
2. `paper/introduction.md`
3. `paper/claims.md`
4. `paper/diagnostic_validation.md`
5. `SYNTHETIC_EVIDENCE_STATUS_TABLE.md`
6. `MMLU_EVIDENCE_GATE_REPORT.md`
7. `paper/appendices/mmlu_redux_reviewer_summary.md`
8. `PREREGISTERED_CROSS_FLAW_HELDOUT_INVESTIGATION_PLAN.md`
9. `STATIC_CONFIRMATORY_PREFLIGHT_REPORT.md`
10. `RUNBOOK_CONFIRMATORY_SYNTHETIC_VALIDATION.md`

## 12. Reproduction Commands

Static/package checks only:

```bash
ruff check .
python3 -m pytest -q tests/test_preflight_confirmatory_synthetic.py
python3 -m pytest -q tests/test_make_reviewer_packet.py
python3 -m pytest -q tests/test_real_panel_dryrun_commands.py tests/test_real_panel_baselines_scaffold.py
```

Create the safe reviewer packet:

```bash
python3 scripts/make_reviewer_packet.py
```

Future confirmatory commands are documented in `CONFIRMATORY_RUN_COMMAND_MANIFEST.md`, but remain
deferred until explicit execution approval.
