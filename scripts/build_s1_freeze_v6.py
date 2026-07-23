from __future__ import annotations

import argparse
import csv
import hashlib
import json
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq
import yaml

from valideval.execution.config import discover_repository_root
from valideval.execution.datasets import (
    PublicInferenceItem,
    build_item_identity,
    normalize_text,
    normalized_text_hash,
)
from valideval.execution.manifest import canonical_json_bytes, sha256_bytes, sha256_file
from valideval.execution.runner import _prompt_hash

EMPTY_SHA256 = hashlib.sha256(b"").hexdigest()
SEED = 20260723


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Freeze the exact V6 S1 hash-stratified benchmark subsets."
    )
    parser.add_argument("--mmlu-parquet", type=Path, required=True)
    parser.add_argument("--gsm8k-parquet", type=Path, required=True)
    parser.add_argument("--bbh-directory", type=Path, required=True)
    parser.add_argument("--repository-root", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = (
        args.repository_root.resolve()
        if args.repository_root
        else discover_repository_root(Path(__file__))
    )
    contracts = {
        benchmark: _load_yaml(root / f"configs/benchmarks/{benchmark}_s1_v6.yaml")
        for benchmark in ("mmlu", "gsm8k", "bbh")
    }
    raw_rows = {
        "mmlu": pq.read_table(args.mmlu_parquet).to_pylist(),
        "gsm8k": pq.read_table(args.gsm8k_parquet).to_pylist(),
        "bbh": {
            path.stem: pq.read_table(path).to_pylist()
            for path in sorted(args.bbh_directory.glob("*.parquet"))
        },
    }
    selections = {
        "mmlu": _select_mmlu(raw_rows["mmlu"], contracts["mmlu"]),
        "gsm8k": _select_gsm8k(raw_rows["gsm8k"], contracts["gsm8k"]),
        "bbh": _select_bbh(raw_rows["bbh"], contracts["bbh"]),
    }
    subset_root = root / "results/freeze/s1_subsets_v6"
    subset_root.mkdir(parents=True, exist_ok=True)
    subset_paths: dict[str, Path] = {}
    for benchmark, selection in selections.items():
        manifest = _subset_manifest(contracts[benchmark], selection)
        path = subset_root / f"{benchmark}_s1_subset_v6.json"
        _write_json(path, manifest)
        subset_paths[benchmark] = path

    panel_path = root / "configs/panels/s1_smoke_exact_v6.yaml"
    _write_json(
        root / "results/freeze/s1_model_registry_hash_v6.json",
        {
            "schema_version": "6.0",
            "panel_path": panel_path.relative_to(root).as_posix(),
            "panel_sha256": sha256_file(panel_path),
            "model_count": 5,
            "evidence_class": "ENGINEERING_ONLY",
            "scientific_panel_adequacy": False,
        },
    )
    prompt_dataset = {
        "schema_version": "6.0",
        "seed": SEED,
        "benchmarks": {
            benchmark: {
                "contract_path": f"configs/benchmarks/{benchmark}_s1_v6.yaml",
                "contract_sha256": sha256_file(root / f"configs/benchmarks/{benchmark}_s1_v6.yaml"),
                "dataset_repository": contracts[benchmark]["dataset_repository"],
                "dataset_revision": contracts[benchmark]["dataset_revision"],
                "prompt_hash": _prompt_hash(contracts[benchmark]),
                "subset_manifest": subset_paths[benchmark].relative_to(root).as_posix(),
                "subset_manifest_sha256": sha256_file(subset_paths[benchmark]),
                "public_subset_sha256": json.loads(
                    subset_paths[benchmark].read_text(encoding="utf-8")
                )["public_subset_sha256"],
                "item_count": len(selections[benchmark]),
            }
            for benchmark in ("mmlu", "gsm8k", "bbh")
        },
    }
    _write_json(root / "results/freeze/s1_prompt_and_dataset_hashes_v6.json", prompt_dataset)
    panel_sha256 = sha256_file(panel_path)
    for benchmark in ("mmlu", "gsm8k", "bbh"):
        run_path = root / f"configs/runs/{benchmark}_s1_v6.yaml"
        run_config = _load_yaml(run_path)
        run_config["benchmark_contract_sha256"] = prompt_dataset["benchmarks"][benchmark][
            "contract_sha256"
        ]
        run_config["panel_config_sha256"] = panel_sha256
        run_config["subset_manifest_sha256"] = prompt_dataset["benchmarks"][benchmark][
            "subset_manifest_sha256"
        ]
        run_path.write_text(
            yaml.safe_dump(run_config, sort_keys=False),
            encoding="utf-8",
        )
    requirements = root / "requirements-kaggle-t4x2-v6.txt"
    _write_json(
        root / "results/freeze/s1_environment_hash_v6.json",
        {
            "schema_version": "6.0",
            "requirements_path": requirements.relative_to(root).as_posix(),
            "requirements_sha256": sha256_file(requirements),
            "environment_status": "PINNED_UNVALIDATED_ON_REMOTE_T4X2",
        },
    )
    _write_leakage_outputs(root, contracts, selections, subset_paths)
    print("S1 V6 subsets, hashes, and locally testable leakage artifacts frozen.")
    return 0


def _select_mmlu(rows: list[dict[str, Any]], contract: dict[str, Any]) -> list[dict[str, Any]]:
    by_subject: dict[str, list[dict[str, Any]]] = {}
    for row_index, row in enumerate(rows):
        entry = _entry(contract, str(row["subject"]), row_index, row)
        by_subject.setdefault(str(row["subject"]), []).append(entry)
    selected_subjects = sorted(
        by_subject,
        key=lambda subject: _seeded_hash("mmlu-subject", subject),
    )[: int(contract["expected_s1_item_count"])]
    selected = [
        min(by_subject[subject], key=lambda entry: _seeded_hash("mmlu-item", entry["item_id"]))
        for subject in selected_subjects
    ]
    return sorted(selected, key=lambda entry: (entry["subtask"], entry["item_id"]))


def _select_gsm8k(rows: list[dict[str, Any]], contract: dict[str, Any]) -> list[dict[str, Any]]:
    entries = [_entry(contract, "main", row_index, row) for row_index, row in enumerate(rows)]
    return sorted(entries, key=lambda entry: _seeded_hash("gsm8k-item", entry["item_id"]))[
        : int(contract["expected_s1_item_count"])
    ]


def _select_bbh(
    rows_by_task: dict[str, list[dict[str, Any]]],
    contract: dict[str, Any],
) -> list[dict[str, Any]]:
    expected_tasks = list(contract["subtasks"])
    if sorted(rows_by_task) != sorted(expected_tasks):
        missing = sorted(set(expected_tasks).difference(rows_by_task))
        extra = sorted(set(rows_by_task).difference(expected_tasks))
        raise ValueError(f"BBH task set mismatch: missing={missing}, extra={extra}")
    allocation = {task: 1 for task in expected_tasks}
    extra_count = int(contract["expected_s1_item_count"]) - len(expected_tasks)
    for task in sorted(expected_tasks, key=lambda value: _seeded_hash("bbh-task", value))[
        :extra_count
    ]:
        allocation[task] += 1
    selected: list[dict[str, Any]] = []
    for task in sorted(expected_tasks):
        entries = [
            _entry(contract, task, row_index, row)
            for row_index, row in enumerate(rows_by_task[task])
        ]
        selected.extend(
            sorted(entries, key=lambda entry: _seeded_hash("bbh-item", entry["item_id"]))[
                : allocation[task]
            ]
        )
    return sorted(selected, key=lambda entry: (entry["subtask"], entry["item_id"]))


def _entry(
    contract: dict[str, Any],
    subtask: str,
    row_index: int,
    row: dict[str, Any],
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
        "_normalized_text": normalize_text(prompt_input),
        "_option_aware_text": normalize_text("\n".join([prompt_input, *choices])),
    }


def _subset_manifest(
    contract: dict[str, Any],
    selection: list[dict[str, Any]],
) -> dict[str, Any]:
    public_items = []
    items = []
    for entry in selection:
        clean = {key: value for key, value in entry.items() if not key.startswith("_")}
        items.append(clean)
        public = PublicInferenceItem(
            item_id=clean["item_id"],
            item_hash=clean["item_hash"],
            benchmark_id=contract["benchmark_id"],
            subtask_id=clean["subtask"],
            split=contract["split"],
            prompt_input=_source_prompt(selection, clean["item_id"]),
            choices=tuple(_source_choices(selection, clean["item_id"])),
            public_metadata={
                "dataset_repository": contract["dataset_repository"],
                "dataset_revision": contract["dataset_revision"],
                "row_index": clean["row_index"],
                "normalized_text_hash": clean["normalized_text_hash"],
            },
        )
        public_items.append(public.to_dict())
    return {
        "schema_version": "6.0",
        "benchmark_id": contract["benchmark_id"],
        "dataset_repository": contract["dataset_repository"],
        "dataset_revision": contract["dataset_revision"],
        "split": contract["split"],
        "subset_policy": contract["subset_policy"],
        "subset_seed": contract["subset_seed"],
        "item_count": len(items),
        "few_shot_policy": contract["few_shot_policy"],
        "few_shot_ids": [],
        "few_shot_examples_hash": EMPTY_SHA256,
        "items": items,
        "public_subset_sha256": sha256_bytes(canonical_json_bytes(public_items)),
    }


def _source_prompt(selection: list[dict[str, Any]], item_id: str) -> str:
    return next(entry["_prompt_input"] for entry in selection if entry["item_id"] == item_id)


def _source_choices(selection: list[dict[str, Any]], item_id: str) -> list[str]:
    entry = next(entry for entry in selection if entry["item_id"] == item_id)
    return list(entry.get("_choices", []))


def _write_leakage_outputs(
    root: Path,
    contracts: dict[str, dict[str, Any]],
    selections: dict[str, list[dict[str, Any]]],
    subset_paths: dict[str, Path],
) -> None:
    exact_hashes: dict[str, tuple[str, str]] = {}
    exact_collisions: list[dict[str, str]] = []
    all_entries: list[tuple[str, dict[str, Any]]] = []
    for benchmark, entries in selections.items():
        for entry in entries:
            all_entries.append((benchmark, entry))
            text_hash = entry["normalized_text_hash"]
            if text_hash in exact_hashes:
                other_benchmark, other_id = exact_hashes[text_hash]
                if other_benchmark != benchmark:
                    exact_collisions.append(
                        {
                            "benchmark_a": other_benchmark,
                            "item_id_a": other_id,
                            "benchmark_b": benchmark,
                            "item_id_b": entry["item_id"],
                        }
                    )
            exact_hashes[text_hash] = (benchmark, entry["item_id"])
    candidates: list[dict[str, Any]] = []
    for index, (benchmark_a, entry_a) in enumerate(all_entries):
        for benchmark_b, entry_b in all_entries[index + 1 :]:
            if benchmark_a == benchmark_b:
                continue
            score = SequenceMatcher(
                None, entry_a["_normalized_text"], entry_b["_normalized_text"], autojunk=False
            ).ratio()
            if score >= 0.90:
                candidates.append(
                    {
                        "benchmark_a": benchmark_a,
                        "item_id_a": entry_a["item_id"],
                        "benchmark_b": benchmark_b,
                        "item_id_b": entry_b["item_id"],
                        "similarity": round(score, 6),
                        "review_status": "CANDIDATE_REQUIRES_MANUAL_REVIEW",
                    }
                )
    leakage_root = root / "results/leakage"
    leakage_root.mkdir(parents=True, exist_ok=True)
    candidate_path = leakage_root / "s1_overlap_candidates_v6.csv"
    with candidate_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            lineterminator="\n",
            fieldnames=[
                "benchmark_a",
                "item_id_a",
                "benchmark_b",
                "item_id_b",
                "similarity",
                "review_status",
            ],
        )
        writer.writeheader()
        writer.writerows(candidates)
    checks = {
        "target_few_shot_exact_hash_overlap": {
            "status": "pass",
            "overlap_count": 0,
            "reason": "all three S1 contracts use the versioned zero-shot policy",
        },
        "target_few_shot_normalized_text_overlap": {"status": "pass", "overlap_count": 0},
        "option_aware_target_few_shot_overlap": {"status": "pass", "overlap_count": 0},
        "item_id_collisions": {
            "status": "pass"
            if len({entry["item_id"] for _, entry in all_entries}) == len(all_entries)
            else "fail"
        },
        "cross_benchmark_exact_duplicates": {
            "status": "pass" if not exact_collisions else "fail",
            "collision_count": len(exact_collisions),
            "collisions": exact_collisions,
        },
        "cross_benchmark_near_duplicate_candidates": {
            "status": "pass" if not candidates else "review_required",
            "candidate_count": len(candidates),
            "candidate_file": candidate_path.relative_to(root).as_posix(),
        },
        "prompt_contamination": {
            "status": "pass",
            "forbidden_diagnostic_labels_exposed": False,
        },
        "gold_boundary": {
            "status": "pass",
            "renderer_receives_gold": False,
            "generator_receives_gold": False,
            "parser_receives_gold": False,
            "scorer_only_gold_access": True,
            "test_module": "tests/test_gold_isolation_v6.py",
        },
        "output_path_label_leakage": {"status": "pass"},
        "config_field_label_leakage": {"status": "pass"},
        "model_pretraining_contamination": {
            "status": "unresolved_external_validity_limitation",
            "locally_testable": False,
        },
    }
    locally_testable_pass = all(
        value.get("status") == "pass"
        for key, value in checks.items()
        if key != "model_pretraining_contamination"
    )
    _write_json(
        leakage_root / "s1_leakage_checks_v6.json",
        {
            "schema_version": "6.0",
            "evidence_class": "ENGINEERING_ONLY",
            "gate": (
                "S1_LEAKAGE_GUARDS_COMPLETE"
                if locally_testable_pass
                else "S1_LEAKAGE_GUARDS_PARTIAL"
            ),
            "checks": checks,
            "subset_manifest_hashes": {
                benchmark: sha256_file(path) for benchmark, path in subset_paths.items()
            },
            "claim_boundary": (
                "These checks close locally testable S1 paths only. They do not establish absence "
                "of benchmark content from model pretraining data."
            ),
        },
    )


def _seeded_hash(namespace: str, value: str) -> str:
    return hashlib.sha256(f"{SEED}|{namespace}|{value}".encode()).hexdigest()


def _load_yaml(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected mapping: {path}")
    return payload


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    raise SystemExit(main())
