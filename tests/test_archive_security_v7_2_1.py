from __future__ import annotations

import stat
import zipfile
from pathlib import Path

import pytest

from valideval.execution.packaging import (
    PackageValidationError,
    validate_run_directory,
    validate_zip_archive,
)
from valideval.importers.ingest_v7 import IngestV7Error, ingest_and_analyze_v7


def _write_zip(path: Path, members: list[tuple[zipfile.ZipInfo | str, bytes]]) -> None:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, content in members:
            archive.writestr(name, content)


@pytest.mark.parametrize(
    "member",
    ["../escape", "/absolute", "folder\\windows", "C:/windows-absolute", "folder/./file"],
)
def test_archive_rejects_traversal_and_nonportable_paths(tmp_path: Path, member: str) -> None:
    archive = tmp_path / "unsafe.zip"
    _write_zip(archive, [(member, b"unsafe")])
    with pytest.raises(PackageValidationError, match="unsafe archive member"):
        validate_zip_archive(archive)
    with pytest.raises(IngestV7Error):
        ingest_and_analyze_v7(archive, output_root=tmp_path / "imported")


def test_archive_rejects_symlink(tmp_path: Path) -> None:
    archive = tmp_path / "symlink.zip"
    info = zipfile.ZipInfo("link")
    info.create_system = 3
    info.external_attr = stat.S_IFLNK << 16
    _write_zip(archive, [(info, b"target")])
    with pytest.raises(PackageValidationError, match="symbolic links"):
        validate_zip_archive(archive)


def test_run_directory_rejects_symlink_before_packaging(tmp_path: Path) -> None:
    run = tmp_path / "run"
    run.mkdir()
    target = tmp_path / "outside.json"
    target.write_text("{}", encoding="utf-8")
    (run / "run_manifest.json").symlink_to(target)
    with pytest.raises(PackageValidationError, match="symbolic links"):
        validate_run_directory(run)


def test_archive_rejects_duplicate_member(tmp_path: Path) -> None:
    archive = tmp_path / "duplicate.zip"
    with zipfile.ZipFile(archive, "w") as handle:
        handle.writestr("same", b"one")
        with pytest.warns(UserWarning):
            handle.writestr("same", b"two")
    with pytest.raises(PackageValidationError, match="unique and sorted"):
        validate_zip_archive(archive)


def test_archive_rejects_case_colliding_members(tmp_path: Path) -> None:
    archive = tmp_path / "case-collision.zip"
    _write_zip(archive, [("File.json", b"one"), ("file.json", b"two")])
    with pytest.raises(PackageValidationError, match="case-insensitive"):
        validate_zip_archive(archive)


def test_archive_rejects_member_count_and_compression_ratio(tmp_path: Path) -> None:
    archive = tmp_path / "many.zip"
    _write_zip(archive, [(f"{index:03d}", b"x") for index in range(5)])
    with pytest.raises(PackageValidationError, match="member count"):
        validate_zip_archive(archive, maximum_members=4)

    bomb = tmp_path / "ratio.zip"
    _write_zip(bomb, [("zeros", b"0" * 100_000)])
    with pytest.raises(PackageValidationError, match="compression ratio"):
        validate_zip_archive(bomb, maximum_compression_ratio=2.0)


def test_archive_accepts_portable_space_unicode_and_long_names(tmp_path: Path) -> None:
    archive = tmp_path / "portable.zip"
    names = sorted(["folder with space/file.json", "unicode/δ.json", f"long/{'a' * 180}.json"])
    _write_zip(archive, [(name, b"{}") for name in names])
    result = validate_zip_archive(archive)
    assert result["members"] == names
