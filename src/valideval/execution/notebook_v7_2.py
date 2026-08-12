from __future__ import annotations

import json
import os
import subprocess
import tempfile
from importlib import import_module
from pathlib import Path
from typing import Any

import yaml

from valideval.execution.config import load_run_config, semantic_config_hash
from valideval.execution.datasets import FrozenBenchmarkItem, PublicInferenceItem
from valideval.execution.models import load_panel_config
from valideval.execution.runner import _load_contract, preflight_from_config, run_from_config
from valideval.importers.s1_v7_2 import accept_s1_v7_2

_CONFIGS = {
    benchmark: f"configs/runs_v7_2/{benchmark}_s1_v7_2.yaml"
    for benchmark in ("mmlu", "gsm8k", "bbh")
}


def run_notebook_stage_v7_2(
    stage: str,
    *,
    mode: str,
    output_root: str | Path,
    repository_root: str | Path,
) -> dict[str, Any]:
    root = Path(repository_root).resolve()
    destination = Path(output_root).resolve()
    if stage == "preflight":
        if mode == "fixture":
            return {
                "status": "V7_2_PRODUCTION_CONFIGS_VALIDATED_FIXTURE_BOUNDARY",
                "evidence_class": "NON_EVIDENCE_FIXTURE",
                "configs": [_config_identity(root, benchmark) for benchmark in _CONFIGS],
                "hardware_check": "DEFERRED_TO_REAL_PREFLIGHT",
            }
        environment = _v7_2_environment_access_preflight(root)
        results = [
            preflight_from_config(root / config, output_root=destination)
            for config in _CONFIGS.values()
        ]
        if any(result["status"] != "PREFLIGHT_COMPLETE" for result in results):
            raise RuntimeError(f"V7.2 production preflight failed: {results}")
        return {
            "status": "V7_2_T4X2_PREFLIGHT_PASS",
            "environment": environment,
            "results": results,
            "claim_boundary": "Preflight is engineering evidence only.",
        }
    if stage in _CONFIGS:
        config_path = root / _CONFIGS[stage]
        if mode == "fixture":
            return _run_fixture(config_path, root=root, output_root=destination)
        return run_from_config(
            config_path,
            mode_override=None if mode == "smoke" else mode,
            output_root=destination,
            repository_root=root,
        )
    if stage == "validate_package":
        source_commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=root, text=True
        ).strip()
        return accept_s1_v7_2(
            destination / "packages",
            repository_root=root,
            expected_source_commit=source_commit if mode == "fixture" else None,
            allow_non_evidence_fixture=mode == "fixture",
        )
    raise ValueError(f"unknown V7.2 notebook stage: {stage}")


def _run_fixture(config_path: Path, *, root: Path, output_root: Path) -> dict[str, Any]:
    payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    source_commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=root, text=True
    ).strip()
    payload.update(
        {
            "mode": "fixture",
            "evidence_class": "NON_EVIDENCE_FIXTURE",
            "expected_source_commit": source_commit,
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
    with tempfile.TemporaryDirectory(prefix="valideval-v7-2-notebook-fixture-") as temporary:
        fixture_path = Path(temporary) / config_path.name
        fixture_path.write_text(yaml.safe_dump(payload, sort_keys=True), encoding="utf-8")
        return run_from_config(
            fixture_path,
            output_root=output_root,
            repository_root=root,
            injected_items=_fixture_items(root, payload),
        )


def _fixture_items(root: Path, config_payload: dict[str, Any]) -> list[FrozenBenchmarkItem]:
    subset = json.loads((root / str(config_payload["subset_manifest"])).read_text(encoding="utf-8"))
    benchmark = str(config_payload["benchmark_id"])
    output = []
    for index, entry in enumerate(subset["items"]):
        choices = ("one", "two", "three", "four") if benchmark == "mmlu" else ()
        subtask = "causal_judgement" if benchmark == "bbh" else str(entry["subtask"])
        output.append(
            FrozenBenchmarkItem(
                public=PublicInferenceItem(
                    item_id=str(entry["item_id"]),
                    item_hash=str(entry["item_hash"]),
                    benchmark_id=benchmark,
                    subtask_id=subtask,
                    split="test",
                    prompt_input=f"NON_EVIDENCE_FIXTURE {benchmark} item {index}",
                    choices=choices,
                    public_metadata={"evidence_class": "NON_EVIDENCE_FIXTURE"},
                ),
                private_gold=("0" if benchmark in {"mmlu", "gsm8k"} else "(A)"),
            )
        )
    return output


def _config_identity(root: Path, benchmark: str) -> dict[str, Any]:
    config = load_run_config(root / _CONFIGS[benchmark], repository_root=root)
    panel = load_panel_config(root / config.panel_config)
    contract = _load_contract(root / config.benchmark_contract, benchmark)
    return {
        "benchmark_id": benchmark,
        "config_hash": semantic_config_hash(config),
        "model_revisions": {
            model["canonical_model_id"]: model["revision"] for model in panel["models"]
        },
        "dataset_revision": contract["dataset_revision"],
        "prompt_template_version": contract["prompt_template_version"],
        "required_source_ref": config.required_source_ref,
    }


def _validate_v7_2_hardware(gpu_names: list[str], total_ram_bytes: int) -> dict[str, Any]:
    if len(gpu_names) != 2 or any("T4" not in name.upper() for name in gpu_names):
        raise RuntimeError(f"V7.2 S1 requires exactly two T4 GPUs; observed={gpu_names}")
    minimum_ram = 12 * 1024**3
    if total_ram_bytes < minimum_ram:
        raise RuntimeError(
            f"V7.2 S1 requires at least 12 GiB RAM; observed={total_ram_bytes / 1024**3:.2f}"
        )
    return {
        "gpu_count": len(gpu_names),
        "gpu_names": gpu_names,
        "total_ram_bytes": total_ram_bytes,
        "minimum_ram_bytes": minimum_ram,
    }


def _verify_huggingface_access(root: Path, api: Any) -> dict[str, Any]:
    model_revisions: dict[str, str] = {}
    dataset_revisions: dict[str, str] = {}
    for benchmark, relative in _CONFIGS.items():
        config = load_run_config(root / relative, repository_root=root)
        panel = load_panel_config(root / config.panel_config)
        contract = _load_contract(root / config.benchmark_contract, benchmark)
        for model in panel["models"]:
            repository = str(model["repository"])
            revision = str(model["revision"])
            if repository not in model_revisions:
                api.model_info(repo_id=repository, revision=revision)
                model_revisions[repository] = revision
        repository = str(contract["dataset_repository"])
        revision = str(contract["dataset_revision"])
        api.dataset_info(repo_id=repository, revision=revision)
        dataset_revisions[repository] = revision
    return {
        "internet": "PASS",
        "model_revisions": model_revisions,
        "dataset_revisions": dataset_revisions,
    }


def _v7_2_environment_access_preflight(root: Path) -> dict[str, Any]:
    try:
        import torch

        huggingface_hub = import_module("huggingface_hub")
    except ImportError as exc:
        raise RuntimeError("T4 preflight requires torch and huggingface_hub") from exc
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is unavailable")
    names = [torch.cuda.get_device_name(index) for index in range(torch.cuda.device_count())]
    try:
        total_ram = int(os.sysconf("SC_PHYS_PAGES")) * int(os.sysconf("SC_PAGE_SIZE"))
    except (AttributeError, OSError, ValueError):
        total_ram = 0
    hardware = _validate_v7_2_hardware(names, total_ram)
    access = _verify_huggingface_access(
        root, huggingface_hub.HfApi(token=os.environ.get("HF_TOKEN"))
    )
    return {
        **hardware,
        **access,
        "cuda_available": True,
        "cuda_version": str(torch.version.cuda),
    }
