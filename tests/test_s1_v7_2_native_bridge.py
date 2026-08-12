from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import zipfile
from pathlib import Path
from typing import Any

import pytest
import yaml

from valideval.execution.config import load_run_config
from valideval.execution.datasets import FrozenBenchmarkItem, PublicInferenceItem
from valideval.execution.manifest import sha256_file
from valideval.execution.runner import run_from_config
from valideval.importers.s1_v7_2 import (
    S1_V7_2_ACCEPTED,
    S1_V7_2_REJECTED_CONFIG,
    S1_V7_2_REJECTED_COVERAGE,
    S1_V7_2_REJECTED_EXTRACTION,
    S1_V7_2_REJECTED_IDENTITY,
    S1_V7_2_REJECTED_PROVENANCE,
    S1_V7_2_REQUIRES_RERUN,
    accept_s1_v7_2,
)

ROOT = Path(__file__).resolve().parents[1]
BENCHMARKS = ("mmlu", "gsm8k", "bbh")


def test_all_native_s1_v7_2_configs_are_exact_and_resolvable() -> None:
    paths = sorted((ROOT / "configs/runs_v7_2").glob("*_s1_v7_2.yaml"))
    assert [path.name for path in paths] == [
        "bbh_s1_v7_2.yaml",
        "gsm8k_s1_v7_2.yaml",
        "mmlu_s1_v7_2.yaml",
    ]
    for path in paths:
        config = load_run_config(path, repository_root=ROOT)
        contract = yaml.safe_load((ROOT / config.benchmark_contract).read_text(encoding="utf-8"))
        panel = yaml.safe_load((ROOT / config.panel_config).read_text(encoding="utf-8"))
        subset = json.loads((ROOT / config.subset_manifest).read_text(encoding="utf-8"))
        assert config.schema_version == "7.2"
        assert config.study_id == "study-c-s1-v7-2"
        assert config.stage == "S1"
        assert config.evidence_class == "ENGINEERING_ONLY"
        assert config.execution.required_gpu_count == 2
        assert contract["generation_parameters"]["do_sample"] is False
        assert len(panel["models"]) == 5
        assert subset["item_count"] == 50


def test_s1_v7_2_acceptance_requires_all_three_archives(tmp_path: Path) -> None:
    result = accept_s1_v7_2(tmp_path, repository_root=ROOT, expected_source_commit="a" * 40)
    assert result["status"] == S1_V7_2_REQUIRES_RERUN
    assert len(result["problems"]) == 3


def test_s1_v7_2_acceptance_rejects_duplicate_archives(tmp_path: Path) -> None:
    for name in (
        "valideval_v7_2_s1_mmlu_one.zip",
        "valideval_v7_2_s1_mmlu_two.zip",
        "valideval_v7_2_s1_gsm8k_one.zip",
        "valideval_v7_2_s1_bbh_one.zip",
    ):
        with zipfile.ZipFile(tmp_path / name, "w"):
            pass
    result = accept_s1_v7_2(tmp_path, repository_root=ROOT, expected_source_commit="a" * 40)
    assert result["status"] == S1_V7_2_REJECTED_IDENTITY


@pytest.fixture(scope="module")
def native_s1_packages(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Any]:
    root = tmp_path_factory.mktemp("native-s1-v7-2")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    packages = root / "packages"
    packages.mkdir()
    results: dict[str, Any] = {}
    for benchmark in BENCHMARKS:
        config_path = _mock_config(root, benchmark, commit)
        result = run_from_config(
            config_path,
            output_root=root / "outputs" / benchmark,
            repository_root=ROOT,
            injected_items=_fixture_items(benchmark),
        )
        assert result["status"] == "RUN_COMPLETE"
        archive = Path(result["zip_path"])
        target = packages / archive.name
        target.write_bytes(archive.read_bytes())
        results[benchmark] = result
    return {"root": root, "packages": packages, "commit": commit, "results": results}


def test_runner_zip_import_acceptance_transaction_is_ready(
    native_s1_packages: dict[str, Any],
) -> None:
    imported = native_s1_packages["root"] / "accepted"
    result = accept_s1_v7_2(
        native_s1_packages["packages"],
        repository_root=ROOT,
        output_root=imported,
        expected_source_commit=native_s1_packages["commit"],
        allow_non_evidence_fixture=True,
    )
    assert result["status"] == S1_V7_2_ACCEPTED
    assert result["fixture_only"] is True
    assert result["authorization_updated"] is False
    assert {entry["benchmark_id"] for entry in result["benchmarks"]} == set(BENCHMARKS)
    assert all(entry["row_count"] == 250 for entry in result["benchmarks"])
    assert all(entry["expected_item_count"] == 50 for entry in result["benchmarks"])
    assert (imported / "s1_acceptance_receipt_v7_2.json").is_file()
    assert not (imported / "study_c_authorization_v7_2.json").exists()


def test_s1_v7_2_rejects_source_mismatch(native_s1_packages: dict[str, Any]) -> None:
    result = accept_s1_v7_2(
        native_s1_packages["packages"],
        repository_root=ROOT,
        expected_source_commit="f" * 40,
        allow_non_evidence_fixture=True,
    )
    assert result["status"] == S1_V7_2_REJECTED_PROVENANCE


def test_s1_v7_2_archives_have_canonical_members(native_s1_packages: dict[str, Any]) -> None:
    required = {
        "run_manifest.json",
        "environment.json",
        "models.json",
        "benchmark_contract.json",
        "config_snapshot.yaml",
        "file_checksums.json",
        "shard_status.json",
        "failure_summary.csv",
        "predictions.jsonl",
        "matrix.csv",
    }
    for archive in native_s1_packages["packages"].glob("*.zip"):
        with zipfile.ZipFile(archive) as handle:
            assert set(handle.namelist()) == required
        assert len(sha256_file(archive)) == 64


@pytest.mark.parametrize(
    ("mutation", "expected_status"),
    [
        ("checkpoint", S1_V7_2_REJECTED_IDENTITY),
        ("coverage", S1_V7_2_REJECTED_COVERAGE),
        ("extraction", S1_V7_2_REJECTED_EXTRACTION),
        ("config", S1_V7_2_REJECTED_CONFIG),
        ("prompt", S1_V7_2_REJECTED_CONFIG),
        ("duplicate", S1_V7_2_REJECTED_IDENTITY),
    ],
)
def test_s1_v7_2_native_acceptance_negative_matrix(
    native_s1_packages: dict[str, Any],
    tmp_path: Path,
    mutation: str,
    expected_status: str,
) -> None:
    packages = tmp_path / "packages"
    shutil.copytree(native_s1_packages["packages"], packages)
    archive = next(packages.glob("valideval_v7_2_s1_mmlu_*.zip"))
    run_dir = tmp_path / "run"
    with zipfile.ZipFile(archive) as handle:
        handle.extractall(run_dir)
    if mutation == "checkpoint":
        payload = json.loads((run_dir / "models.json").read_text())
        payload["models"][0]["family"] = "wrong-family"
        (run_dir / "models.json").write_text(json.dumps(payload), encoding="utf-8")
        _resign(run_dir, "models.json")
    elif mutation in {"coverage", "extraction", "duplicate"}:
        path = run_dir / "predictions.jsonl"
        lines = path.read_text(encoding="utf-8").splitlines()
        if mutation == "coverage":
            lines = lines[1:]
        elif mutation == "duplicate":
            lines.append(lines[0])
        else:
            for index in range(20):
                row = json.loads(lines[index])
                row.update(
                    {
                        "parsed_output": None,
                        "is_correct": None,
                        "extraction_status": "failed",
                        "failure_type": "EXTRACTION_FAILURE",
                    }
                )
                lines[index] = json.dumps(row)
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        _resign(run_dir, "predictions.jsonl")
    elif mutation == "config":
        payload = yaml.safe_load((run_dir / "config_snapshot.yaml").read_text())
        payload["output_root"] = "wrong-output-root"
        (run_dir / "config_snapshot.yaml").write_text(
            yaml.safe_dump(payload), encoding="utf-8"
        )
        _resign(run_dir, "config_snapshot.yaml")
    else:
        payload = json.loads((run_dir / "benchmark_contract.json").read_text())
        payload["prompt_hash"] = "0" * 64
        (run_dir / "benchmark_contract.json").write_text(
            json.dumps(payload), encoding="utf-8"
        )
        _resign(run_dir, "benchmark_contract.json")
    _write_sorted_zip(run_dir, archive)
    result = accept_s1_v7_2(
        packages,
        repository_root=ROOT,
        expected_source_commit=native_s1_packages["commit"],
        allow_non_evidence_fixture=True,
    )
    assert result["status"] == expected_status


def _mock_config(root: Path, benchmark: str, commit: str) -> Path:
    source = ROOT / f"configs/runs_v7_2/{benchmark}_s1_v7_2.yaml"
    payload = yaml.safe_load(source.read_text(encoding="utf-8"))
    payload.update(
        {
            "mode": "fixture",
            "evidence_class": "NON_EVIDENCE_FIXTURE",
            "expected_source_commit": commit,
        }
    )
    payload["execution"].update(
        {
            "backend": "mock",
            "use_processes": False,
            "minimum_free_disk_gb": 0,
            "model_download_margin_gb": 0,
        }
    )
    destination = root / f"{benchmark}_fixture_v7_2.yaml"
    destination.write_text(yaml.safe_dump(payload, sort_keys=True), encoding="utf-8")
    return destination


def _fixture_items(benchmark: str) -> list[FrozenBenchmarkItem]:
    config = load_run_config(
        ROOT / f"configs/runs_v7_2/{benchmark}_s1_v7_2.yaml", repository_root=ROOT
    )
    subset = json.loads((ROOT / config.subset_manifest).read_text(encoding="utf-8"))
    items: list[FrozenBenchmarkItem] = []
    for index, entry in enumerate(subset["items"]):
        choices = ("one", "two", "three", "four") if benchmark == "mmlu" else ()
        subtask = "causal_judgement" if benchmark == "bbh" else str(entry["subtask"])
        prompt_input = f"NON_EVIDENCE_FIXTURE {benchmark} prompt {index}"
        gold = "0" if benchmark in {"mmlu", "gsm8k"} else "(A)"
        public = PublicInferenceItem(
            item_id=str(entry["item_id"]),
            item_hash=str(entry["item_hash"]),
            benchmark_id=benchmark,
            subtask_id=subtask,
            split="test",
            prompt_input=prompt_input,
            choices=choices,
            public_metadata={"evidence_class": "NON_EVIDENCE_FIXTURE"},
        )
        items.append(FrozenBenchmarkItem(public=public, private_gold=gold))
    return items


def _resign(run_dir: Path, filename: str) -> None:
    digest = hashlib.sha256((run_dir / filename).read_bytes()).hexdigest()
    checksums = json.loads((run_dir / "file_checksums.json").read_text())
    manifest = json.loads((run_dir / "run_manifest.json").read_text())
    checksums["files"][filename] = digest
    manifest["file_checksums"][filename] = digest
    (run_dir / "file_checksums.json").write_text(
        json.dumps(checksums), encoding="utf-8"
    )
    (run_dir / "run_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")


def _write_sorted_zip(run_dir: Path, archive: Path) -> None:
    archive.unlink()
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as handle:
        for path in sorted(run_dir.iterdir()):
            handle.write(path, arcname=path.name)
