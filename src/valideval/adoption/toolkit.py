from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from valideval.io.jsonl import read_jsonl_as, write_jsonl
from valideval.schemas import BenchmarkItem, ConstructSpec

REQUIRED_BENCHMARK_FILES = [
    "items.jsonl",
    "construct_spec.yaml",
    "benchmark_card.md",
    "scoring.yaml",
    "audit_config.yaml",
    "README.md",
]


def init_benchmark(path: str | Path, *, overwrite: bool = False) -> dict[str, Any]:
    root = Path(path)
    root.mkdir(parents=True, exist_ok=True)
    files = {
        "items.jsonl": _sample_items,
        "construct_spec.yaml": _construct_spec_yaml,
        "benchmark_card.md": _benchmark_card_md,
        "scoring.yaml": _scoring_yaml,
        "audit_config.yaml": _audit_config_yaml,
        "README.md": _readme_md,
    }
    created: list[str] = []
    skipped: list[str] = []
    benchmark_id = root.name
    for relative, writer in files.items():
        path_out = root / relative
        if path_out.exists() and not overwrite:
            skipped.append(str(path_out))
            continue
        writer(path_out, benchmark_id)
        created.append(str(path_out))
    return {
        "benchmark_dir": str(root),
        "created": created,
        "skipped": skipped,
        "next_command": f"python -m valideval validate-benchmark {root}",
    }


def validate_benchmark(path: str | Path) -> dict[str, Any]:
    root = Path(path)
    errors: list[str] = []
    warnings: list[str] = []
    for required in REQUIRED_BENCHMARK_FILES:
        if not (root / required).exists():
            errors.append(f"Missing required file: {required}")
    items: list[BenchmarkItem] = []
    if (root / "items.jsonl").exists():
        try:
            items = read_jsonl_as(root / "items.jsonl", BenchmarkItem)
        except (ValidationError, json.JSONDecodeError, TypeError, ValueError) as exc:
            errors.append(f"items.jsonl is not BenchmarkItem-compatible: {exc}")
    if (root / "construct_spec.yaml").exists():
        try:
            payload = yaml.safe_load((root / "construct_spec.yaml").read_text(encoding="utf-8"))
            ConstructSpec.model_validate(payload)
        except (ValidationError, yaml.YAMLError, TypeError, ValueError) as exc:
            errors.append(f"construct_spec.yaml is not ConstructSpec-compatible: {exc}")
    item_ids = [item.item_id for item in items]
    duplicate_ids = sorted({item_id for item_id in item_ids if item_ids.count(item_id) > 1})
    if duplicate_ids:
        errors.append(f"Duplicate item IDs: {', '.join(duplicate_ids)}")
    missing_provenance = [
        item.item_id
        for item in items
        if not any([item.source_url, item.source_document, item.snapshot])
    ]
    if missing_provenance:
        warnings.append(
            "Some items lack source_url/source_document/snapshot provenance fields: "
            + ", ".join(missing_provenance[:10])
        )
    return {
        "benchmark_dir": str(root),
        "valid": not errors,
        "item_count": len(items),
        "errors": errors,
        "warnings": warnings,
    }


def generate_card(path: str | Path, *, overwrite: bool = True) -> dict[str, Any]:
    root = Path(path)
    validation = validate_benchmark(root)
    if not validation["valid"]:
        return {**validation, "generated": False}
    items = read_jsonl_as(root / "items.jsonl", BenchmarkItem)
    spec = ConstructSpec.model_validate(
        yaml.safe_load((root / "construct_spec.yaml").read_text(encoding="utf-8"))
    )
    output = root / "benchmark_card.md"
    if output.exists() and not overwrite:
        return {"generated": False, "path": str(output), "reason": "benchmark_card.md exists"}
    tags = sorted({tag for item in items for tag in item.construct_tags})
    output.write_text(
        "\n".join(
            [
                f"# Benchmark Card: {root.name}",
                "",
                "## Construct",
                "",
                f"- Claimed construct: {spec.claimed_construct}",
                f"- Description: {spec.description or 'Add a benchmark-specific description.'}",
                f"- Construct tags observed in items: {', '.join(tags) or 'none'}",
                "",
                "## Intended Decisions",
                "",
                "- Describe decisions this benchmark can inform under a documented audit protocol.",
                "",
                "## Non-Intended Uses",
                "",
                "- Do not treat a benchmark score as a scalar proof of model capability.",
                "",
                "## Validity Threats",
                "",
                *[f"- {threat}" for threat in spec.expected_threats],
                "",
                "## Required Evidence",
                "",
                "- Response matrices, scoring configuration, provenance fields, and human validation where relevant.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return {"generated": True, "path": str(output), "item_count": len(items)}


def _sample_items(path: Path, benchmark_id: str) -> None:
    write_jsonl(
        path,
        [
            BenchmarkItem(
                item_id=f"{benchmark_id}_001",
                prompt="Which option follows from the provided context?",
                answer="A",
                choices=[
                    "A. The supported answer",
                    "B. An unsupported distractor",
                    "C. A tempting shortcut answer",
                    "D. An unrelated option",
                ],
                context="The context states that the supported answer is the correct one.",
                source_document="author_fixture",
                license="TBD",
                created_by="benchmark_author",
                human_verified=False,
                construct_tags=["context_use"],
                construct_critical_fields=["prompt", "context", "choices"],
                metadata={"split": "dev"},
            )
        ],
    )


def _construct_spec_yaml(path: Path, benchmark_id: str) -> None:
    payload = ConstructSpec(
        claimed_construct=f"{benchmark_id} claimed construct",
        construct_tags=["context_use"],
        construct_critical_fields=["prompt", "context", "choices"],
        expected_threats=[
            "shortcut artifacts",
            "coverage gaps",
            "scoring ambiguity",
            "contamination or provenance gaps",
        ],
        description="Replace this scaffold with the construct and intended decisions.",
        limitations=["Initial scaffold; requires benchmark-author validation."],
    )
    path.write_text(
        yaml.safe_dump(payload.model_dump(mode="json"), sort_keys=False), encoding="utf-8"
    )


def _benchmark_card_md(path: Path, benchmark_id: str) -> None:
    path.write_text(
        "\n".join(
            [
                f"# Benchmark Card: {benchmark_id}",
                "",
                "## Claimed Construct",
                "",
                "Describe the construct the benchmark is intended to measure.",
                "",
                "## Intended Uses",
                "",
                "- Replace with decisions this benchmark can inform under a stated protocol.",
                "",
                "## Non-Intended Uses",
                "",
                "- Do not use as a global proof of model ability or benchmark validity.",
                "",
                "## Known Validity Threats",
                "",
                "- Shortcut artifacts",
                "- Scoring ambiguity",
                "- Provenance gaps",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _scoring_yaml(path: Path, benchmark_id: str) -> None:
    payload = {
        "schema_version": "0.1",
        "benchmark_id": benchmark_id,
        "scoring_method": "mcq_or_exact_match",
        "accepted_aliases": {},
        "limitations": [
            "Scoring configuration is a scaffold; validate aliases and ambiguous labels before use."
        ],
    }
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def _audit_config_yaml(path: Path, benchmark_id: str) -> None:
    payload = {
        "schema_version": "0.1",
        "benchmark_id": benchmark_id,
        "diagnostics": [
            "baselines",
            "answer_distribution",
            "shortcut",
            "irt",
            "reliability",
            "data_forensics",
        ],
        "limitations": [
            "This audit plan is a starting point and should be aligned with the claimed construct."
        ],
    }
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def _readme_md(path: Path, benchmark_id: str) -> None:
    path.write_text(
        "\n".join(
            [
                f"# {benchmark_id}",
                "",
                "This directory is a ValidEval benchmark scaffold.",
                "",
                "## First Commands",
                "",
                f"1. `python -m valideval validate-benchmark {path.parent}`",
                (
                    "2. `python -m valideval quickstart-audit "
                    f"--items {path.parent / 'items.jsonl'} "
                    f"--benchmark-card {path.parent / 'benchmark_card.md'}`"
                ),
                "",
            ]
        ),
        encoding="utf-8",
    )
