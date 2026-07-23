from __future__ import annotations

import zipfile
from pathlib import Path

from scripts import make_reviewer_packet


def _write(path: Path, text: str = "safe\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _minimal_repo(tmp_path: Path) -> Path:
    for rel in make_reviewer_packet.REQUIRED_FILES:
        _write(tmp_path / rel)
    for rel in make_reviewer_packet.OPTIONAL_SAFE_FILES:
        _write(tmp_path / rel)
    for rel in make_reviewer_packet.INCLUDE_DIRS:
        _write(tmp_path / rel / "safe_file.md", f"# {rel}\n")

    _write(tmp_path / "paper" / "abstract.md", "# Abstract\n")
    _write(tmp_path / "paper" / "introduction.md", "# Introduction\n")
    _write(tmp_path / "configs" / "validation" / "synthetic_default.yaml", "seed: 0\n")
    _write(tmp_path / "src" / "valideval" / "__init__.py", "")
    _write(tmp_path / "scripts" / "make_reviewer_packet.py", "# script placeholder\n")
    _write(tmp_path / "tests" / "test_make_reviewer_packet.py", "# test placeholder\n")
    return tmp_path


def _zip_names(zip_path: Path) -> set[str]:
    with zipfile.ZipFile(zip_path) as archive:
        return set(archive.namelist())


def test_zip_is_created(tmp_path: Path) -> None:
    repo = _minimal_repo(tmp_path)

    packet = make_reviewer_packet.build_reviewer_packet(repo)

    assert packet.output_path == repo / make_reviewer_packet.DEFAULT_OUTPUT
    assert packet.output_path.exists()
    assert packet.file_count > 0


def test_required_files_are_included(tmp_path: Path) -> None:
    repo = _minimal_repo(tmp_path)

    packet = make_reviewer_packet.build_reviewer_packet(repo)
    names = _zip_names(packet.output_path)

    for rel in make_reviewer_packet.REQUIRED_FILES:
        assert rel in names
    assert "paper/abstract.md" in names
    assert "configs/validation/synthetic_default.yaml" in names
    assert "scripts/make_reviewer_packet.py" in names


def test_excluded_directories_are_not_included(tmp_path: Path) -> None:
    repo = _minimal_repo(tmp_path)
    excluded_files = (
        "cache/raw.txt",
        "data/external/helm/raw.txt",
        "results/mmlu/predictions.txt",
        "results/synthetic/preflight/output.txt",
    )
    for rel in excluded_files:
        _write(repo / rel)

    packet = make_reviewer_packet.build_reviewer_packet(repo)
    names = _zip_names(packet.output_path)

    for rel in excluded_files:
        assert rel not in names


def test_large_raw_and_cache_artifacts_are_excluded(tmp_path: Path) -> None:
    repo = _minimal_repo(tmp_path)
    large_csv = repo / "configs" / "large_artifact.csv"
    large_csv.parent.mkdir(parents=True, exist_ok=True)
    large_csv.write_bytes(b"x" * (make_reviewer_packet.MAX_CSV_BYTES + 1))
    _write(repo / "cache" / "large_cache.txt")

    packet = make_reviewer_packet.build_reviewer_packet(repo)
    names = _zip_names(packet.output_path)

    assert "configs/large_artifact.csv" not in names
    assert "configs/large_artifact.csv" in packet.skipped_files
    assert "cache/large_cache.txt" not in names


def test_no_jsonl_prediction_files_are_included(tmp_path: Path) -> None:
    repo = _minimal_repo(tmp_path)
    _write(repo / "paper" / "predictions.jsonl", '{"prediction": "A"}\n')
    _write(repo / "examples" / "model_predictions.jsonl", '{"prediction": "B"}\n')

    packet = make_reviewer_packet.build_reviewer_packet(repo)
    names = _zip_names(packet.output_path)

    assert all(not name.endswith(".jsonl") for name in names)
    assert "paper/predictions.jsonl" in packet.skipped_files
    assert "examples/model_predictions.jsonl" in packet.skipped_files


def test_dry_run_surface_includes_manifests_only(tmp_path: Path) -> None:
    repo = _minimal_repo(tmp_path)
    manifest = repo / "results" / "no_run_dryrun_surface" / "real_panel.manifest.json"
    capture = repo / "results" / "no_run_dryrun_surface" / "real_panel.txt"
    _write(manifest, '{"mode": "dry_run_only", "evidence_state": "RESULT_REQUIRED"}\n')
    _write(capture, "verbose stdout capture\n")

    packet = make_reviewer_packet.build_reviewer_packet(repo)
    names = _zip_names(packet.output_path)

    assert "results/no_run_dryrun_surface/real_panel.manifest.json" in names
    assert "results/no_run_dryrun_surface/real_panel.txt" not in names
