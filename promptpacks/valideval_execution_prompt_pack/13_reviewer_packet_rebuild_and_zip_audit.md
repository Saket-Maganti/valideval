# Prompt 13 — Reviewer Packet Rebuild and ZIP Audit

## Objective

Create a clean reviewer packet after real runs and paper compilation.

## Include

- source code,
- configs,
- paper draft/PDF,
- artifact manifest,
- claim ledger,
- result reports,
- small tables/figures,
- dry-run/preflight manifests,
- no-run/evidence lock docs,
- reviewer guide.

## Exclude

- raw benchmark text,
- large cache files,
- raw HELM/MMLU JSONL dumps,
- `data/external/` unless explicitly small/safe,
- huge CSVs,
- Kaggle raw outputs,
- model weights,
- API keys/secrets.

## Run tests

```bash
ruff check .
python3 -m pytest -q tests/test_make_reviewer_packet.py
```

## Rebuild ZIP

```bash
python3 scripts/make_reviewer_packet.py
```

## Record

- ZIP path,
- size,
- file count,
- SHA-256,
- included reports,
- excluded raw artifacts.

## Create/update

```text
REVIEWER_PACKET_ZIP_AUDIT.md
REVIEWER_PACKET_HANDOFF_NOTE.md
```

Final verdict:

```text
REVIEWER_ZIP_READY
REVIEWER_ZIP_NEEDS_FIXES
REVIEWER_ZIP_BLOCKED
```

## Verification

```bash
ruff check .
python3 -m pytest -q
```
