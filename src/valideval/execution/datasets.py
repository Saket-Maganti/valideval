from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from valideval.execution.config import load_yaml_mapping
from valideval.execution.manifest import canonical_json_bytes, sha256_bytes

_GOLD_KEYS = frozenset(
    {
        "answer",
        "gold",
        "gold_answer",
        "gold_output",
        "correct_answer",
        "target",
        "is_correct",
        "label",
    }
)


@dataclass(frozen=True, slots=True)
class PublicInferenceItem:
    item_id: str
    item_hash: str
    benchmark_id: str
    subtask_id: str
    split: str
    prompt_input: str
    choices: tuple[str, ...]
    public_metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["choices"] = list(self.choices)
        return payload


@dataclass(frozen=True, slots=True)
class FrozenBenchmarkItem:
    public: PublicInferenceItem
    private_gold: str


class DatasetResolutionError(RuntimeError):
    """Raised when an immutable benchmark snapshot cannot be reconstructed."""


def normalize_text(value: Any) -> str:
    text = str(value).replace("\u00a0", " ")
    return re.sub(r"\s+", " ", text).strip()


def normalized_text_hash(*parts: Any) -> str:
    normalized = "\n".join(normalize_text(part) for part in parts)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def build_item_identity(
    benchmark_id: str,
    *,
    dataset_revision: str,
    split: str,
    subtask: str,
    prompt_input: str,
    choices: Sequence[str] = (),
) -> tuple[str, str]:
    if benchmark_id == "mmlu":
        identity = {
            "dataset_revision": dataset_revision,
            "subject": subtask,
            "split": split,
            "question": normalize_text(prompt_input),
            "ordered_choices": [normalize_text(choice) for choice in choices],
        }
    elif benchmark_id == "gsm8k":
        identity = {
            "dataset_revision": dataset_revision,
            "config": subtask,
            "split": split,
            "question": normalize_text(prompt_input),
        }
    elif benchmark_id == "bbh":
        identity = {
            "dataset_revision": dataset_revision,
            "subtask": subtask,
            "split": split,
            "input": normalize_text(prompt_input),
        }
    else:
        raise DatasetResolutionError(f"unsupported benchmark: {benchmark_id}")
    digest = sha256_bytes(canonical_json_bytes(identity))
    return f"{benchmark_id}-{subtask}-{digest[:24]}", digest


def load_frozen_benchmark_items(
    contract_path: str | Path,
    subset_manifest_path: str | Path,
) -> tuple[list[FrozenBenchmarkItem], dict[str, Any], dict[str, Any]]:
    contract = load_yaml_mapping(contract_path)
    subset = json.loads(Path(subset_manifest_path).read_text(encoding="utf-8"))
    if not isinstance(subset, dict):
        raise DatasetResolutionError("subset manifest must be a JSON object")
    benchmark_id = str(contract.get("benchmark_id", ""))
    if subset.get("benchmark_id") != benchmark_id:
        raise DatasetResolutionError(
            f"subset benchmark mismatch: {subset.get('benchmark_id')!r} != {benchmark_id!r}"
        )
    expected_count = int(contract.get("expected_s1_item_count", 0))
    entries = subset.get("items")
    if not isinstance(entries, list) or len(entries) != expected_count:
        raise DatasetResolutionError(
            f"subset item count mismatch: expected {expected_count}, got "
            f"{len(entries) if isinstance(entries, list) else 'invalid'}"
        )
    records = _load_huggingface_records(contract, entries)
    items = [
        _freeze_loaded_record(
            contract, entry, records[(str(entry["subtask"]), int(entry["row_index"]))]
        )
        for entry in entries
    ]
    _validate_frozen_items(items, subset)
    return items, contract, subset


def frozen_items_from_records(
    contract: Mapping[str, Any],
    records: Iterable[Mapping[str, Any]],
) -> list[FrozenBenchmarkItem]:
    """Build explicitly non-evidence items for mocked production-path tests."""

    benchmark_id = str(contract["benchmark_id"])
    revision = str(contract.get("dataset_revision", "NON_EVIDENCE_FIXTURE"))
    split = str(contract.get("split", "fixture"))
    items: list[FrozenBenchmarkItem] = []
    for index, raw in enumerate(records):
        record = dict(raw)
        subtask = str(record.pop("subtask", record.pop("subject", "fixture")))
        if benchmark_id == "mmlu":
            prompt_input = str(record["question"])
            choices = tuple(str(value) for value in record["choices"])
            gold = str(record["answer"])
        elif benchmark_id == "gsm8k":
            prompt_input = str(record["question"])
            choices = ()
            gold = str(record["answer"])
        else:
            prompt_input = str(record["input"])
            choices = ()
            gold = str(record["target"])
        item_id, item_hash = build_item_identity(
            benchmark_id,
            dataset_revision=revision,
            split=split,
            subtask=subtask,
            prompt_input=prompt_input,
            choices=choices,
        )
        public = PublicInferenceItem(
            item_id=item_id,
            item_hash=item_hash,
            benchmark_id=benchmark_id,
            subtask_id=subtask,
            split=split,
            prompt_input=prompt_input,
            choices=choices,
            public_metadata={"fixture_row_index": index, "evidence_class": "NON_EVIDENCE_FIXTURE"},
        )
        items.append(FrozenBenchmarkItem(public=public, private_gold=gold))
    return items


def reject_gold_fields(value: Any, *, location: str = "public inference input") -> None:
    if isinstance(value, Mapping):
        leaked = sorted(str(key) for key in value if str(key).lower() in _GOLD_KEYS)
        if leaked:
            raise ValueError(f"{location} contains forbidden gold-bearing fields: {leaked}")
        for key, child in value.items():
            reject_gold_fields(child, location=f"{location}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            reject_gold_fields(child, location=f"{location}[{index}]")


def _load_huggingface_records(
    contract: Mapping[str, Any],
    entries: Sequence[Mapping[str, Any]],
) -> dict[tuple[str, int], dict[str, Any]]:
    try:
        from datasets import load_dataset
    except ImportError as exc:
        raise DatasetResolutionError(
            "datasets is required for immutable benchmark resolution; install .[notebooks]"
        ) from exc
    repository = str(contract["dataset_repository"])
    revision = str(contract["dataset_revision"])
    split = str(contract["split"])
    benchmark_id = str(contract["benchmark_id"])
    by_subtask: dict[str, set[int]] = defaultdict(set)
    for entry in entries:
        by_subtask[str(entry["subtask"])].add(int(entry["row_index"]))
    resolved: dict[tuple[str, int], dict[str, Any]] = {}
    if benchmark_id == "mmlu":
        dataset = load_dataset(repository, "all", split=split, revision=revision)
        for subtask, row_indices in by_subtask.items():
            for row_index in row_indices:
                row = dict(dataset[row_index])
                if str(row.get("subject")) != subtask:
                    raise DatasetResolutionError(
                        f"MMLU row {row_index} subject drift: {row.get('subject')!r} != {subtask!r}"
                    )
                resolved[(subtask, row_index)] = row
    elif benchmark_id == "gsm8k":
        dataset = load_dataset(repository, "main", split=split, revision=revision)
        for row_index in by_subtask.get("main", set()):
            resolved[("main", row_index)] = dict(dataset[row_index])
    elif benchmark_id == "bbh":
        for subtask, row_indices in sorted(by_subtask.items()):
            dataset = load_dataset(repository, subtask, split=split, revision=revision)
            for row_index in row_indices:
                resolved[(subtask, row_index)] = dict(dataset[row_index])
    else:
        raise DatasetResolutionError(f"unsupported benchmark: {benchmark_id}")
    return resolved


def _freeze_loaded_record(
    contract: Mapping[str, Any],
    entry: Mapping[str, Any],
    record: Mapping[str, Any],
) -> FrozenBenchmarkItem:
    benchmark_id = str(contract["benchmark_id"])
    subtask = str(entry["subtask"])
    split = str(contract["split"])
    revision = str(contract["dataset_revision"])
    if benchmark_id == "mmlu":
        prompt_input = str(record["question"])
        choices = tuple(str(value) for value in record["choices"])
        private_gold = str(record["answer"])
    elif benchmark_id == "gsm8k":
        prompt_input = str(record["question"])
        choices = ()
        private_gold = _gsm8k_gold(str(record["answer"]))
    else:
        prompt_input = str(record["input"])
        choices = ()
        private_gold = str(record["target"])
    item_id, item_hash = build_item_identity(
        benchmark_id,
        dataset_revision=revision,
        split=split,
        subtask=subtask,
        prompt_input=prompt_input,
        choices=choices,
    )
    if item_id != entry.get("item_id") or item_hash != entry.get("item_hash"):
        raise DatasetResolutionError(
            f"frozen item identity drift at {subtask}/{entry.get('row_index')}: "
            f"expected {entry.get('item_id')}/{entry.get('item_hash')}, got {item_id}/{item_hash}"
        )
    text_hash = normalized_text_hash(prompt_input, *choices)
    if text_hash != entry.get("normalized_text_hash"):
        raise DatasetResolutionError(f"normalized text hash drift for {item_id}")
    public = PublicInferenceItem(
        item_id=item_id,
        item_hash=item_hash,
        benchmark_id=benchmark_id,
        subtask_id=subtask,
        split=split,
        prompt_input=prompt_input,
        choices=choices,
        public_metadata={
            "dataset_repository": contract["dataset_repository"],
            "dataset_revision": revision,
            "row_index": int(entry["row_index"]),
            "normalized_text_hash": text_hash,
        },
    )
    reject_gold_fields(public.to_dict())
    return FrozenBenchmarkItem(public=public, private_gold=private_gold)


def _validate_frozen_items(
    items: Sequence[FrozenBenchmarkItem],
    subset: Mapping[str, Any],
) -> None:
    item_ids = [item.public.item_id for item in items]
    item_hashes = [item.public.item_hash for item in items]
    if len(set(item_ids)) != len(item_ids):
        raise DatasetResolutionError("frozen subset contains duplicate item IDs")
    if len(set(item_hashes)) != len(item_hashes):
        raise DatasetResolutionError("frozen subset contains duplicate item hashes")
    digest = sha256_bytes(canonical_json_bytes([item.public.to_dict() for item in items]))
    if digest != subset.get("public_subset_sha256"):
        raise DatasetResolutionError(
            f"public subset hash mismatch: expected {subset.get('public_subset_sha256')}, got {digest}"
        )


def _gsm8k_gold(answer: str) -> str:
    marker = answer.rsplit("####", 1)
    if len(marker) != 2 or not marker[1].strip():
        raise DatasetResolutionError("GSM8K answer does not contain a final #### answer")
    return marker[1].strip()
