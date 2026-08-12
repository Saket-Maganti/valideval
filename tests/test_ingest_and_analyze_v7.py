import zipfile
from pathlib import Path

import pytest

from valideval.importers.ingest_v7 import IngestV7Error, ingest_and_analyze_v7


def test_ingest_rejects_zip_traversal(tmp_path: Path) -> None:
    archive = tmp_path / "bad.zip"
    with zipfile.ZipFile(archive, "w") as handle:
        handle.writestr("../escape", "bad")
    with pytest.raises(IngestV7Error, match="unsafe"):
        ingest_and_analyze_v7(archive, output_root=tmp_path / "imported")


def test_ingest_rejects_legacy_competing_manifest_name(tmp_path: Path) -> None:
    package = tmp_path / "legacy"
    package.mkdir()
    (package / "manifest.json").write_text("{}", encoding="utf-8")
    with pytest.raises(IngestV7Error, match="run_manifest"):
        ingest_and_analyze_v7(package, output_root=tmp_path / "imported")
