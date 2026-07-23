# Codex Prompt — 14 Reviewer Packet Slimming and Repo Hygiene

## Global hard rules

This is a **build/fix/polish only** prompt.

Do **not** run:
- validation experiments,
- synthetic generation,
- model inference,
- downloads,
- metric recomputation,
- threshold tuning,
- MMLU-Redux reruns,
- confirmatory cross-flaw / held-out runs,
- real-panel ranking analysis.

Allowed:
- static inspection,
- code scaffolding,
- dry-run or preflight commands,
- report/template creation,
- claim hygiene,
- `ruff check .`,
- targeted tests for newly added no-run code.

Do not upgrade evidence states. Do not remove caveats. Do not remove `[RESULT REQUIRED]` unless a matching local artifact already exists.


## Task

Keep reviewer packet lean and reduce process-theater risk.

Inspect:
`REVIEWER_PACKET_MANIFEST.md`, `REVIEWER_READING_GUIDE.md`, `ARTIFACT_EXCLUSION_POLICY.md`, `REVIEWER_PACKET_ZIP_AUDIT.md`, `REVIEWER_PACKET_HANDOFF_NOTE.md`, `scripts/make_reviewer_packet.py`, `tests/test_make_reviewer_packet.py`.

Create:
`REVIEWER_PACKET_SLIMMING_AUDIT.md`

Check packet includes only:
- paper,
- README,
- core claims ledger,
- synthetic evidence table,
- MMLU evidence gate,
- preregistration plan,
- preflight report,
- runbook/manifest,
- relevant configs,
- core source code,
- tests.

Exclude:
raw/cache artifacts, huge result dirs, duplicate audits, exploratory prompt packs, obsolete run logs, stale notes, `.jsonl`, large CSVs.

Verdict:
- `PACKET_SURFACE_CLEAN`
- `PACKET_NEEDS_REBUILD`
- `PACKET_TOO_BROAD`

Run:
`ruff check .`
`python3 -m pytest -q tests/test_make_reviewer_packet.py`

## Final response format

Return:

```markdown
## Summary
## What was built/changed
## What was not run
## Evidence states
## Files created/modified
## Commands run
## Remaining blockers
## Recommendation
## Next best prompt
```
