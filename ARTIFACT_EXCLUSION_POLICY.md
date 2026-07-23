# Artifact Exclusion Policy

## Purpose

This policy defines what the default `valideval` reviewer packet excludes. The goal is to keep the
packet reviewable, reproducible, and safe while avoiding accidental inclusion of large raw/cache
artifacts or restricted benchmark text.

## Large Raw And Cache Files

Large raw/cache files are not committed or packaged by default. They are operational inputs or
generated outputs, not source-controlled claim text.

Default exclusions include:

- `cache/`
- `data/external/`
- `results/mmlu/`
- `results/synthetic/`
- generated `results/` trees unless explicitly whitelisted
- all `*.jsonl` files
- `*.csv` files larger than 5 MB
- raw model outputs
- local temporary outputs
- generated result trees unless separately approved

## Dry-Run Surface Audit Artifacts

The next reviewer packet may include:

- `NO_RUN_DRYRUN_SURFACE_AUDIT.md`
- `results/no_run_dryrun_surface/*.manifest.json`

Those manifest files are small dry-run records only. They must contain no raw item text, no
prediction rows, no real result tables, and no computed metric values. The corresponding stdout
captures under `results/no_run_dryrun_surface/*.txt` stay excluded because they are command logs and
can be path-heavy.

## HELM MMLU Prediction Artifacts

HELM MMLU prediction artifacts are large and should be referenced by acquisition scripts and
sanitized reports rather than bundled into the default reviewer packet. The relevant routing surface
is the acquisition/import workflow, not raw prediction dumps.

Reviewer-facing MMLU-Redux evidence should use:

- `MMLU_EVIDENCE_GATE_REPORT.md`
- `paper/appendices/mmlu_redux_evidence_appendix.md`
- `paper/appendices/mmlu_redux_reviewer_summary.md`

## Reproducible Generated Outputs

Generated outputs should be reproducible from manifests, runbooks, configs, and scripts. The default
packet therefore includes the command surfaces and excludes bulky output directories.

For confirmatory synthetic validation, the future commands live in:

- `CONFIRMATORY_RUN_COMMAND_MANIFEST.md`
- `RUNBOOK_CONFIRMATORY_SYNTHETIC_VALIDATION.md`

Those commands remain deferred until explicit approval.

## Raw MMLU Text

No raw MMLU question text or answer-choice text should be exposed in the reviewer packet. The
MMLU-Redux stress test is reported through sanitized metadata and aggregate metrics only.

## Reviewer Inspection Path

Reviewers should inspect sanitized reports and claim ledgers before looking for raw artifacts:

- `paper/claims.md`
- `CLAIMS_LEDGER_NEURIPS.md`
- `SYNTHETIC_EVIDENCE_STATUS_TABLE.md`
- `MMLU_EVIDENCE_GATE_REPORT.md`
- `paper/appendices/mmlu_redux_reviewer_summary.md`
- `STATIC_CONFIRMATORY_PREFLIGHT_REPORT.md`

If a reviewer needs to reproduce generated outputs, use the documented acquisition/runbook commands
under the relevant protocol rather than relying on a bundled raw cache.
