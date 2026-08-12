from __future__ import annotations

import json
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
