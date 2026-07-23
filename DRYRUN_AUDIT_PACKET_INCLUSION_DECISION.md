# Dry-Run Audit Packet Inclusion Decision

## 1. Executive Summary

Recommendation: `INCLUDE_IN_NEXT_ZIP`.

The dry-run surface audit should be included in the next reviewer packet because it documents that
the newly added preflight surfaces were exercised without experiments, inference, downloads, metric
recomputation, threshold tuning, or evidence-state upgrades. The existing ZIP was built before this
audit and was not rebuilt during this pass.

## 2. Files Reviewed

- `REVIEWER_PACKET_MANIFEST.md`
- `REVIEWER_READING_GUIDE.md`
- `ARTIFACT_EXCLUSION_POLICY.md`
- `REVIEWER_PACKET_ZIP_AUDIT.md`
- `REVIEWER_PACKET_HANDOFF_NOTE.md`
- `scripts/make_reviewer_packet.py`
- `tests/test_make_reviewer_packet.py`
- `NO_RUN_DRYRUN_SURFACE_AUDIT.md`
- `results/no_run_dryrun_surface/*.manifest.json`

## 3. New Dry-Run Artifacts

The new reviewer-relevant artifact is:

- `NO_RUN_DRYRUN_SURFACE_AUDIT.md`

The small manifest files under `results/no_run_dryrun_surface/*.manifest.json` are also safe for the
next ZIP. They record dry-run status, planned inputs/outputs, and blocked/result-required claim
states. The stdout captures under `results/no_run_dryrun_surface/*.txt` are excluded.

## 4. Should They Be Included?

Yes, in the next explicitly approved ZIP rebuild only.

Include:

- `NO_RUN_DRYRUN_SURFACE_AUDIT.md`
- `DRYRUN_AUDIT_PACKET_INCLUSION_DECISION.md`
- `REVIEWER_PACKET_POST_DRYRUN_AUDIT.md`
- `results/no_run_dryrun_surface/*.manifest.json`

Exclude:

- `results/no_run_dryrun_surface/*.txt`
- all other generated `results/` content
- raw/cache artifacts
- JSONL prediction files
- large CSVs
- real MMLU/HELM prediction dumps

## 5. Why Include / Why Exclude

Include the audit and manifests because they are compact, reviewer-safe dry-run evidence for the
preflight surface. They help reviewers verify that the no-run scaffolds are operational without
mistaking them for empirical results.

Exclude stdout captures because they are logs, may be path-heavy, and add no claim-boundary value
beyond the manifest JSON files. Exclude all other results because the packet should remain a
documentation/source/config bundle, not a generated empirical artifact bundle.

## 6. Safety Checks

The manifest files are small: 9 files totaling about 48K. They contain `dry_run_only`,
`RESULT_REQUIRED`, blocked claim states, planned metrics/outputs, and execution flags such as
`metrics_computed=false`, `inference_run=false`, `download_run=false`, and `alignment_run=false`.

They do not contain raw MMLU question text, answer-choice text, prediction rows, real result tables,
or computed metric values.

## 7. Packaging Script Impact

`scripts/make_reviewer_packet.py` now treats the dry-run audit docs as optional safe files and
whitelists only `results/no_run_dryrun_surface/*.manifest.json`. It does not include stdout captures
or broader `results/` trees.

## 8. Reviewer Reading Guide Impact

`REVIEWER_READING_GUIDE.md` now points readers to `NO_RUN_DRYRUN_SURFACE_AUDIT.md` and clarifies
that dry-run manifests are packaging evidence only, not empirical results.

## 9. Recommendation

`INCLUDE_IN_NEXT_ZIP`

## 10. Next Action

When the user explicitly approves a future packet rebuild, rebuild and verify the ZIP with the
updated packaging policy. Do not rebuild it as part of this audit.
