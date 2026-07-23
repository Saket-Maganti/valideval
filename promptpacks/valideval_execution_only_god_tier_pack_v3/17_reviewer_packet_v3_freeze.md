# Prompt 17 — Reviewer Packet V3 Freeze

## Objective

Freeze all V3 artifacts and create reviewer-safe package.

## Tasks

1. Build artifact manifest.
2. Hash important outputs.
3. Exclude raw/restricted/cache-heavy data.
4. Include reports, code, tests, paper PDF, runbooks, manifests.
5. Verify ZIP integrity.
6. Run lint/tests.

## Outputs

```text
V3_ARTIFACT_MANIFEST.json
V3_ARTIFACT_HASHES.json
dist/valideval_reviewer_packet_v3.zip
REVIEWER_PACKET_V3_AUDIT.md
```

## Verification

```bash
ruff check .
python3 -m pytest -q
python3 - <<'ZIPCHECK'
import zipfile
z='dist/valideval_reviewer_packet_v3.zip'
with zipfile.ZipFile(z) as f:
    print('bad', f.testzip(), 'files', len(f.namelist()))
ZIPCHECK
```

## Final verdict

```text
REVIEWER_PACKET_V3_READY
REVIEWER_PACKET_V3_NEEDS_FIXES
REVIEWER_PACKET_V3_BLOCKED
```
