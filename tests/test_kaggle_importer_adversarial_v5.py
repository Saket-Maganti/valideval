from __future__ import annotations

import json
import stat
import zipfile
from pathlib import Path

import pytest

from valideval.execution.notebook import package_fixture_runs
from valideval.importers.kaggle_v5 import (
    ArchiveSecurityError,
    ImportConflictError,
    ImportManifestError,
    import_kaggle_archive_v5,
    validate_kaggle_zip,
)


def _fixture_zip(tmp_path: Path) -> Path:
    payload = package_fixture_runs(tmp_path / "notebook")
    return Path(payload["packages"][0]["zip_path"])


def _rewrite_zip(source: Path, destination: Path, mutate) -> None:
    with zipfile.ZipFile(source) as archive:
        entries = {
            name: archive.read(name) for name in archive.namelist() if not name.endswith("/")
        }
    mutate(entries)
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, content in sorted(entries.items()):
            archive.writestr(name, content)


def test_valid_fixture_import_is_idempotent_and_conflicts_fail_closed(tmp_path: Path) -> None:
    source = _fixture_zip(tmp_path)
    output = tmp_path / "imports"
    first = import_kaggle_archive_v5(source, output_root=output)
    second = import_kaggle_archive_v5(source, output_root=output)

    assert first["status"] == "imported"
    assert second["status"] == "already_imported"
    assert second["idempotent"] is True
    assert first["prediction_summary"]["evidence_state"] == "NON_EVIDENCE_FIXTURE"

    changed = tmp_path / "changed.zip"

    def mutate(entries: dict[str, bytes]) -> None:
        manifest = json.loads(entries["run_manifest.json"])
        manifest["producer_note"] = "different valid package bytes"
        entries["run_manifest.json"] = json.dumps(manifest, sort_keys=True).encode()

    _rewrite_zip(source, changed, mutate)
    validate_kaggle_zip(changed)
    with pytest.raises(ImportConflictError, match="different hash"):
        import_kaggle_archive_v5(changed, output_root=output)


def test_zip_path_traversal_is_rejected_before_extraction(tmp_path: Path) -> None:
    source = _fixture_zip(tmp_path)
    malicious = tmp_path / "traversal.zip"

    def mutate(entries: dict[str, bytes]) -> None:
        entries["../escape.txt"] = b"escape"

    _rewrite_zip(source, malicious, mutate)
    with pytest.raises(ArchiveSecurityError, match="unsafe relative path"):
        validate_kaggle_zip(malicious)
    assert not (tmp_path / "escape.txt").exists()


def test_symlink_nested_archive_and_zip_bomb_are_rejected(tmp_path: Path) -> None:
    source = _fixture_zip(tmp_path)
    symlink_zip = tmp_path / "symlink.zip"
    with zipfile.ZipFile(source) as original, zipfile.ZipFile(symlink_zip, "w") as output:
        for info in original.infolist():
            if not info.is_dir():
                output.writestr(info.filename, original.read(info.filename))
        link = zipfile.ZipInfo("unsafe-link")
        link.create_system = 3
        link.external_attr = (stat.S_IFLNK | 0o777) << 16
        output.writestr(link, "target")
    with pytest.raises(ArchiveSecurityError, match="Symlink"):
        validate_kaggle_zip(symlink_zip)

    nested = tmp_path / "nested.zip"
    _rewrite_zip(source, nested, lambda entries: entries.__setitem__("payload.zip", b"PK"))
    with pytest.raises(ArchiveSecurityError, match="Nested archive"):
        validate_kaggle_zip(nested)

    bomb = tmp_path / "bomb.zip"
    _rewrite_zip(source, bomb, lambda entries: entries.__setitem__("bomb.txt", b"A" * 2_000_000))
    with pytest.raises(ArchiveSecurityError, match="compression ratio"):
        validate_kaggle_zip(bomb)


def test_missing_manifest_and_checksum_tampering_are_rejected(tmp_path: Path) -> None:
    source = _fixture_zip(tmp_path)
    missing = tmp_path / "missing.zip"
    _rewrite_zip(source, missing, lambda entries: entries.pop("run_manifest.json"))
    with pytest.raises(ImportManifestError, match="missing required"):
        validate_kaggle_zip(missing)

    tampered = tmp_path / "tampered.zip"

    def mutate(entries: dict[str, bytes]) -> None:
        entries["predictions.jsonl"] += b"\n"

    _rewrite_zip(source, tampered, mutate)
    with pytest.raises(ImportManifestError, match="Checksum mismatch"):
        validate_kaggle_zip(tampered)
