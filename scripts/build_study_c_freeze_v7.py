from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import yaml

from valideval.execution.datasets import (
    PublicInferenceItem,
    build_item_identity,
    normalized_text_hash,
)
from valideval.execution.manifest import canonical_json_bytes, sha256_bytes, sha256_file

SEED = 20270809
EMPTY_SHA256 = hashlib.sha256(b"").hexdigest()
BENCHMARKS = ("mmlu", "gsm8k", "bbh")
PILOT_COUNTS = {"mmlu": 200, "gsm8k": 200, "bbh": 270}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Freeze exact Study C V7 benchmark/run inputs.")
    parser.add_argument("--repository-root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)
    root = args.repository_root.resolve()
    freeze_root = root / "results/freeze/study_c_v7"
    run_root = root / "configs/runs_v7"
    freeze_root.mkdir(parents=True, exist_ok=True)
    run_root.mkdir(parents=True, exist_ok=True)
    _write_quantization_panels(root)

    for benchmark in BENCHMARKS:
        source = _load_yaml(root / f"configs/benchmarks/{benchmark}_s1_v6.yaml")
        raw_scientific = _v7_contract(
            source, stage="scientific", count=source["expected_full_item_count"]
        )
        raw_entries = _load_entries(raw_scientific)
        if len(raw_entries) != int(source["expected_full_item_count"]):
            raise ValueError(
                f"{benchmark} item count drift: expected {source['expected_full_item_count']}, "
                f"resolved {len(raw_entries)}"
            )
        entries = _retire_exact_duplicates(raw_entries)
        scientific = _v7_contract(source, stage="scientific", count=len(entries))
        scientific["raw_full_item_count"] = len(raw_entries)
        scientific["exact_duplicate_items_retired"] = len(raw_entries) - len(entries)
        pilot = _v7_contract(source, stage="pilot", count=PILOT_COUNTS[benchmark])
        pilot["raw_full_item_count"] = len(raw_entries)
        pilot["exact_duplicate_items_retired_before_sampling"] = len(raw_entries) - len(entries)
        scientific_path = root / f"configs/benchmarks/{benchmark}_scientific_v7.yaml"
        pilot_path = root / f"configs/benchmarks/{benchmark}_s2_v7.yaml"
        _write_yaml(scientific_path, scientific)
        _write_yaml(pilot_path, pilot)
        full_manifest = _manifest(scientific, entries, "full_frozen_test_split_v7")
        pilot_entries = _select_pilot(benchmark, entries, PILOT_COUNTS[benchmark])
        pilot_manifest = _manifest(pilot, pilot_entries, "seeded_stratified_pilot_v7")
        full_path = freeze_root / f"{benchmark}_scientific_full_v7.json"
        pilot_manifest_path = freeze_root / f"{benchmark}_s2_pilot_v7.json"
        _write_json(full_path, full_manifest)
        _write_json(pilot_manifest_path, pilot_manifest)

        for stage, mode, evidence, panel, contract_path, subset_path in (
            (
                "S2",
                "pilot",
                "EXPLORATORY",
                "configs/panels/s2_pilot_v7.yaml",
                pilot_path,
                pilot_manifest_path,
            ),
            (
                "S3",
                "minimum_scientific",
                "CONFIRMATORY",
                "configs/panels/s3_scientific_v7.yaml",
                scientific_path,
                full_path,
            ),
            (
                "S4",
                "full_common_panel",
                "CONFIRMATORY",
                "configs/panels/s4_maximum_ceiling_v7.yaml",
                scientific_path,
                full_path,
            ),
        ):
            run = _run_config(
                root=root,
                benchmark=benchmark,
                stage=stage,
                mode=mode,
                evidence=evidence,
                panel=panel,
                contract_path=contract_path,
                subset_path=subset_path,
            )
            _write_yaml(run_root / f"{benchmark}_{stage.lower()}_v7.yaml", run)
        robustness_runs: list[tuple[str, str, str]] = []
        if benchmark == "mmlu":
            robustness_runs.extend(
                [
                    (
                        "controlled_generation",
                        "configs/robustness/mmlu_controlled_generation_v7.yaml",
                        "configs/panels/s3_scientific_v7.yaml",
                    ),
                    (
                        "option_loglikelihood",
                        "configs/robustness/mmlu_option_loglikelihood_v7.yaml",
                        "configs/panels/s3_scientific_v7.yaml",
                    ),
                ]
            )
        elif benchmark == "gsm8k":
            robustness_runs.append(
                (
                    "alternate_prompt_parser",
                    "configs/robustness/gsm8k_alternate_prompt_parser_v7.yaml",
                    "configs/panels/s3_scientific_v7.yaml",
                )
            )
        else:
            robustness_runs.append(
                (
                    "alternate_prompt",
                    "configs/robustness/bbh_alternate_prompt_v7.yaml",
                    "configs/panels/s3_scientific_v7.yaml",
                )
            )
        robustness_runs.extend(
            [
                (
                    "quantization_fp16",
                    "configs/robustness/quantization_sensitivity_v7.yaml",
                    "configs/panels/s5_quantization_fp16_v7.yaml",
                ),
                (
                    "quantization_nf4",
                    "configs/robustness/quantization_sensitivity_v7.yaml",
                    "configs/panels/s5_quantization_nf4_v7.yaml",
                ),
            ]
        )
        for suffix, robustness_path, robustness_panel in robustness_runs:
            run = _run_config(
                root=root,
                benchmark=benchmark,
                stage="S5",
                mode="robustness",
                evidence="ROBUSTNESS",
                panel=robustness_panel,
                contract_path=pilot_path,
                subset_path=pilot_manifest_path,
                robustness_config=robustness_path,
                run_suffix=suffix,
            )
            _write_yaml(run_root / f"{benchmark}_s5_{suffix}_v7.yaml", run)
    print("Study C V7 benchmark contracts, manifests, and run configs frozen.")
    return 0


def _v7_contract(source: dict[str, Any], *, stage: str, count: int) -> dict[str, Any]:
    payload = dict(source)
    benchmark = str(payload["benchmark_id"])
    payload.update(
        {
            "schema_version": "7.0",
            "benchmark_contract_id": f"{benchmark}_{stage}_v7",
            "benchmark_version": f"{payload['dataset_repository']}_{payload['dataset_revision'][:8]}_{stage}_v7",
            "expected_item_count": int(count),
            "subset_policy": (
                "full_frozen_test_split_v7"
                if stage == "scientific"
                else "seeded_stratified_pilot_v7"
            ),
            "subset_seed": SEED,
            "few_shot_policy": "zero_shot_v7",
            "few_shot_ids": [],
            "few_shot_examples_hash": EMPTY_SHA256,
        }
    )
    payload.pop("expected_s1_item_count", None)
    payload.pop("represented_subject_count", None)
    return payload


def _load_entries(contract: dict[str, Any]) -> list[dict[str, Any]]:
    try:
        from datasets import load_dataset
    except ImportError as exc:
        raise RuntimeError("install the datasets extra to freeze Study C") from exc
    repository = str(contract["dataset_repository"])
    revision = str(contract["dataset_revision"])
    split = str(contract["split"])
    benchmark = str(contract["benchmark_id"])
    entries: list[dict[str, Any]] = []
    if benchmark == "mmlu":
        data = load_dataset(repository, "all", split=split, revision=revision)
        for index, row in enumerate(data):
            entries.append(_entry(contract, str(row["subject"]), index, dict(row)))
    elif benchmark == "gsm8k":
        data = load_dataset(repository, "main", split=split, revision=revision)
        for index, row in enumerate(data):
            entries.append(_entry(contract, "main", index, dict(row)))
    else:
        for subtask in contract["subtasks"]:
            data = load_dataset(repository, subtask, split=split, revision=revision)
            for index, row in enumerate(data):
                entries.append(_entry(contract, str(subtask), index, dict(row)))
    return sorted(entries, key=lambda row: (row["subtask"], row["row_index"]))


def _entry(
    contract: dict[str, Any], subtask: str, row_index: int, row: dict[str, Any]
) -> dict[str, Any]:
    benchmark = str(contract["benchmark_id"])
    if benchmark == "mmlu":
        prompt_input = str(row["question"])
        choices = [str(value) for value in row["choices"]]
    elif benchmark == "gsm8k":
        prompt_input = str(row["question"])
        choices = []
    else:
        prompt_input = str(row["input"])
        choices = []
    item_id, item_hash = build_item_identity(
        benchmark,
        dataset_revision=str(contract["dataset_revision"]),
        split=str(contract["split"]),
        subtask=subtask,
        prompt_input=prompt_input,
        choices=choices,
    )
    return {
        "subtask": subtask,
        "row_index": row_index,
        "item_id": item_id,
        "item_hash": item_hash,
        "normalized_text_hash": normalized_text_hash(prompt_input, *choices),
        "_prompt_input": prompt_input,
        "_choices": choices,
    }


def _select_pilot(
    benchmark: str, entries: list[dict[str, Any]], count: int
) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in entries:
        grouped[str(row["subtask"])].append(row)
    chosen: list[dict[str, Any]] = []
    for subtask in sorted(grouped):
        chosen.append(
            min(grouped[subtask], key=lambda row: _seeded_hash(benchmark, row["item_id"]))
        )
    chosen_ids = {str(row["item_id"]) for row in chosen}
    remaining = sorted(
        (row for row in entries if str(row["item_id"]) not in chosen_ids),
        key=lambda row: _seeded_hash(benchmark, row["item_id"]),
    )
    chosen.extend(remaining[: count - len(chosen)])
    return sorted(chosen, key=lambda row: (row["subtask"], row["row_index"]))


def _retire_exact_duplicates(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    retained: dict[str, dict[str, Any]] = {}
    for row in entries:
        identifier = str(row["item_id"])
        previous = retained.setdefault(identifier, row)
        if previous["item_hash"] != row["item_hash"]:
            raise ValueError(f"item ID collision with different hash: {identifier}")
    return sorted(retained.values(), key=lambda row: (row["subtask"], row["row_index"]))


def _manifest(
    contract: dict[str, Any], entries: list[dict[str, Any]], policy: str
) -> dict[str, Any]:
    clean_entries: list[dict[str, Any]] = []
    public: list[dict[str, Any]] = []
    for row in entries:
        clean = {key: value for key, value in row.items() if not key.startswith("_")}
        clean_entries.append(clean)
        public.append(
            PublicInferenceItem(
                item_id=str(clean["item_id"]),
                item_hash=str(clean["item_hash"]),
                benchmark_id=str(contract["benchmark_id"]),
                subtask_id=str(clean["subtask"]),
                split=str(contract["split"]),
                prompt_input=str(row["_prompt_input"]),
                choices=tuple(map(str, row["_choices"])),
                public_metadata={
                    "dataset_repository": contract["dataset_repository"],
                    "dataset_revision": contract["dataset_revision"],
                    "row_index": int(clean["row_index"]),
                    "normalized_text_hash": clean["normalized_text_hash"],
                },
            ).to_dict()
        )
    return {
        "schema_version": "7.0",
        "benchmark_id": contract["benchmark_id"],
        "dataset_repository": contract["dataset_repository"],
        "dataset_revision": contract["dataset_revision"],
        "split": contract["split"],
        "subset_policy": policy,
        "subset_seed": SEED,
        "item_count": len(clean_entries),
        "few_shot_policy": "zero_shot_v7",
        "few_shot_ids": [],
        "few_shot_examples_hash": EMPTY_SHA256,
        "public_subset_sha256": sha256_bytes(canonical_json_bytes(public)),
        "items": clean_entries,
    }


def _run_config(
    *,
    root: Path,
    benchmark: str,
    stage: str,
    mode: str,
    evidence: str,
    panel: str,
    contract_path: Path,
    subset_path: Path,
    robustness_config: str | None = None,
    run_suffix: str | None = None,
) -> dict[str, Any]:
    stage_lower = stage.lower()
    payload = {
        "schema_version": "7.0",
        "run_id": f"study-c-{stage_lower}-{benchmark}{'-' + run_suffix if run_suffix else ''}-v7",
        "study_id": f"study-c-{stage_lower}-v7",
        "stage": stage,
        "evidence_class": evidence,
        "mode": mode,
        "benchmark_id": benchmark,
        "benchmark_contract": contract_path.relative_to(root).as_posix(),
        "benchmark_contract_sha256": sha256_file(contract_path),
        "panel_config": panel,
        "panel_config_sha256": sha256_file(root / panel),
        "subset_manifest": subset_path.relative_to(root).as_posix(),
        "subset_manifest_sha256": sha256_file(subset_path),
        "output_root": "kaggle_v7_outputs",
        "required_source_ref": "valideval-v7-icml2027-max-pre-execution",
        "expected_source_commit": None,
        "allow_source_commit_from_environment": True,
        "execution": {
            "backend": "transformers",
            "gpu_ids": ["0", "1"],
            "required_gpu_count": 2,
            "allow_single_gpu_fallback": False,
            "use_processes": True,
            "process_start_method": "spawn",
            "max_retries": 2,
            "shard_count": 8,
            "batch_size": 1,
            "max_sequence_length": 3072 if benchmark == "bbh" else 2048,
            "timeout_seconds": 1800,
            "minimum_free_disk_gb": 10,
            "model_download_margin_gb": 5,
        },
    }
    if robustness_config:
        payload["robustness_config"] = robustness_config
        payload["robustness_config_sha256"] = sha256_file(root / robustness_config)
    return payload


def _write_quantization_panels(root: Path) -> None:
    source = _load_yaml(root / "configs/panels/s3_scientific_v7.yaml")
    representatives = {
        "Qwen/Qwen2.5-3B-Instruct",
        "mistralai/Mistral-7B-Instruct-v0.3",
    }
    selected = [
        dict(model) for model in source["models"] if str(model["repository"]) in representatives
    ]
    if {str(model["repository"]) for model in selected} != representatives:
        raise ValueError("quantization representatives are absent from S3")
    for suffix, quantization in (("fp16", "none"), ("nf4", "nf4")):
        models = []
        for raw in selected:
            model = dict(raw)
            model["quantization"] = quantization
            model["quantization_fallback"] = None
            models.append(model)
        _write_yaml(
            root / f"configs/panels/s5_quantization_{suffix}_v7.yaml",
            {
                "schema_version": "7.0",
                "panel_id": f"s5_quantization_{suffix}_v7",
                "study_id": "study-c-s5-v7",
                "evidence_class": "ROBUSTNESS",
                "scientific_panel_adequacy": False,
                "model_count": 2,
                "family_count": 2,
                "models": models,
                "claim_boundary": "Representative precision sensitivity only.",
            },
        )


def _seeded_hash(namespace: str, value: str) -> str:
    return hashlib.sha256(f"{SEED}:{namespace}:{value}".encode()).hexdigest()


def _load_yaml(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected mapping: {path}")
    return payload


def _write_yaml(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
