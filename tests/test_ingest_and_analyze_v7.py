import hashlib
import json
import zipfile
from pathlib import Path

import pytest

from valideval.importers.ingest_v7 import IngestV7Error, ingest_and_analyze_v7


def _package(root: Path) -> Path:
    package = root / "package"
    package.mkdir()
    predictions = package / "predictions.jsonl"
    rows = []
    for model in range(5):
        for item in range(2):
            rows.append(
                {
                    "item_id": f"i{item}",
                    "model_id": f"m{model}",
                    "model_revision": f"abcdef{model}",
                    "parsed_prediction": "A",
                    "correct": bool(item),
                }
            )
    predictions.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
    digest = hashlib.sha256(predictions.read_bytes()).hexdigest()
    manifest = {
        "schema_version": "v7",
        "study_id": "S2",
        "run_id": "fixture-run",
        "benchmark_id": "mmlu",
        "dataset_revision": "1234567",
        "prompt_hash": "a" * 64,
        "config_hash": "b" * 64,
        "expected_items": 2,
        "models": [
            {"model_id": f"m{model}", "revision": f"abcdef{model}", "family": f"f{model}"}
            for model in range(5)
        ],
        "files": [{"path": "predictions.jsonl", "sha256": digest}],
    }
    (package / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return package


def test_ingest_routes_all_fifteen_stages(tmp_path: Path) -> None:
    package = _package(tmp_path)
    result = ingest_and_analyze_v7(package, output_root=tmp_path / "imported")
    assert result["claim_eligible"]
    assert len(result["routes"]) == 15
    assert Path(result["receipt_path"]).is_file()


def test_ingest_fails_checksum_mismatch(tmp_path: Path) -> None:
    package = _package(tmp_path)
    (package / "predictions.jsonl").write_text("tampered\n", encoding="utf-8")
    with pytest.raises(IngestV7Error, match="checksum"):
        ingest_and_analyze_v7(package, output_root=tmp_path / "imported")


def test_ingest_rejects_zip_traversal(tmp_path: Path) -> None:
    archive = tmp_path / "bad.zip"
    with zipfile.ZipFile(archive, "w") as handle:
        handle.writestr("../escape", "bad")
    with pytest.raises(IngestV7Error, match="unsafe"):
        ingest_and_analyze_v7(archive, output_root=tmp_path / "imported")
