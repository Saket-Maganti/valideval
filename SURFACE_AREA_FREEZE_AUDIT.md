# Surface-Area Freeze Audit

## Verdict

`CORE_REVIEWER_PATH_FROZEN`

## Core paper contribution

The reviewer-facing contribution is diagnostic validation and claim authorization for
benchmark-validity diagnostics.

## Reviewer-facing files

- `paper/abstract.md`
- `paper/introduction.md`
- `paper/claims.md`
- `paper/diagnostic_validation.md`
- `paper/limitations.md`
- `CLAIMS_LEDGER_NEURIPS.md`
- `SYNTHETIC_EVIDENCE_STATUS_TABLE.md`
- `MMLU_EVIDENCE_GATE_REPORT.md`
- `PREREGISTERED_CROSS_FLAW_HELDOUT_INVESTIGATION_PLAN.md`
- `NO_RUN_RULES_AND_EVIDENCE_STATE_LOCK.md`

## Support files

Static preflight commands, no-run manifests, report templates, configs, and tests are support
surfaces. They do not create evidence.

## Deferred / non-paper features

Domain packs, certificates/badges, repair engine, leaderboard/site surfaces, design assistant,
plugin surfaces, predictive/Goodhart claims, and any unvalidated diagnostic are deferred unless a
separate validation artifact exists.

## Reviewer path

1. Paper thesis
2. Diagnostic validation
3. Synthetic evidence state
4. MMLU weak/negative stress test
5. Preregistered confirmatory plan
6. Real-panel finding `[RESULT REQUIRED]`

## Files not in main reviewer path

Exploratory prompt packs, raw/cache artifacts, generated result trees, large CSVs, JSONL prediction
files, and obsolete run logs should remain outside the default reviewer packet.
