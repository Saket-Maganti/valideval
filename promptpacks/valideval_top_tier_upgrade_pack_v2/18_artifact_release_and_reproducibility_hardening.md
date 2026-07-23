# Prompt 18 — Artifact Release and Reproducibility Hardening

## Objective

Make the reviewer artifact credible.

## Tasks

1. Create exact reproduction command list.
2. Add artifact hashes.
3. Add environment lock/report.
4. Add raw artifact exclusion policy.
5. Add small smoke test.
6. Add make targets if useful.
7. Rebuild reviewer ZIP.
8. Verify ZIP excludes raw/cache.

## Create

```text
REPRODUCIBILITY_HARDENING_REPORT.md
REVIEWER_PACKET_V2_ZIP_AUDIT.md
```

Final verdict:

```text
ARTIFACT_RELEASE_READY
ARTIFACT_RELEASE_NEEDS_FIXES
```
