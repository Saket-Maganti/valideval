from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from typing import Any

from valideval.execution.manifest import canonical_json_bytes, sha256_bytes

FOLD_SCHEMA_VERSION = "valideval.transport-fold.v7.1"
_REQUIRED = {
    "schema_version",
    "fold_id",
    "training_benchmarks",
    "held_out_benchmark",
    "training_families",
    "held_out_families",
    "training_model_ids",
    "evaluation_model_ids",
    "discovery_item_ids",
    "evaluation_item_ids",
    "execution_status",
    "data_artifact_hashes",
    "fold_hash",
    "source_commit",
    "config_hash",
}


class FoldManifestError(ValueError):
    """Raised when a claimed held-out fold is not provenance-complete."""


def build_fold_manifest(
    *,
    fold_id: str,
    training_benchmarks: Sequence[str],
    held_out_benchmark: str | None,
    training_families: Sequence[str],
    held_out_families: Sequence[str],
    training_model_ids: Sequence[str],
    evaluation_model_ids: Sequence[str],
    discovery_item_ids: Sequence[str],
    evaluation_item_ids: Sequence[str],
    source_commit: str,
    config_hash: str,
    execution_status: str = "PLANNED",
    data_artifact_hashes: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema_version": FOLD_SCHEMA_VERSION,
        "fold_id": str(fold_id),
        "training_benchmarks": sorted(set(map(str, training_benchmarks))),
        "held_out_benchmark": None if held_out_benchmark is None else str(held_out_benchmark),
        "training_families": sorted(set(map(str, training_families))),
        "held_out_families": sorted(set(map(str, held_out_families))),
        "training_model_ids": sorted(set(map(str, training_model_ids))),
        "evaluation_model_ids": sorted(set(map(str, evaluation_model_ids))),
        "discovery_item_ids": sorted(set(map(str, discovery_item_ids))),
        "evaluation_item_ids": sorted(set(map(str, evaluation_item_ids))),
        "execution_status": str(execution_status).upper(),
        "data_artifact_hashes": dict(sorted((data_artifact_hashes or {}).items())),
        "source_commit": str(source_commit),
        "config_hash": str(config_hash),
    }
    payload["fold_hash"] = _fold_hash(payload)
    return validate_fold_manifest(payload)


def validate_fold_manifest(value: Mapping[str, Any] | str) -> dict[str, Any]:
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError as exc:
            raise FoldManifestError("fold manifest string must contain JSON") from exc
        if not isinstance(parsed, dict):
            raise FoldManifestError("fold manifest JSON must contain an object")
        payload = dict(parsed)
    else:
        payload = dict(value)
    missing = sorted(_REQUIRED - set(payload))
    if missing:
        raise FoldManifestError(f"fold manifest is missing {missing}")
    if payload["schema_version"] != FOLD_SCHEMA_VERSION:
        raise FoldManifestError("unsupported transport fold schema")
    for key in (
        "training_benchmarks",
        "training_families",
        "held_out_families",
        "training_model_ids",
        "evaluation_model_ids",
        "discovery_item_ids",
        "evaluation_item_ids",
    ):
        values = payload[key]
        if not isinstance(values, list) or len(values) != len(set(map(str, values))):
            raise FoldManifestError(f"{key} must be a duplicate-free list")
    held_out_benchmark = payload["held_out_benchmark"]
    if held_out_benchmark is not None and str(held_out_benchmark) in set(
        map(str, payload["training_benchmarks"])
    ):
        raise FoldManifestError("held-out benchmark appears in training benchmarks")
    if set(map(str, payload["training_families"])) & set(map(str, payload["held_out_families"])):
        raise FoldManifestError("held-out family appears in training families")
    if payload["held_out_families"] and set(map(str, payload["training_model_ids"])) & set(
        map(str, payload["evaluation_model_ids"])
    ):
        raise FoldManifestError("evaluation model appears in the training model set")
    if set(map(str, payload["discovery_item_ids"])) & set(map(str, payload["evaluation_item_ids"])):
        raise FoldManifestError("evaluation item appears in the discovery item set")
    for key, width in (("source_commit", 40), ("config_hash", 64), ("fold_hash", 64)):
        text = str(payload[key]).lower()
        if len(text) != width or any(character not in "0123456789abcdef" for character in text):
            raise FoldManifestError(f"{key} must be a {width}-character hexadecimal digest")
    execution_status = str(payload["execution_status"]).upper()
    if execution_status not in {"PLANNED", "EXECUTED"}:
        raise FoldManifestError("execution_status must be PLANNED or EXECUTED")
    artifact_hashes = payload["data_artifact_hashes"]
    if not isinstance(artifact_hashes, dict):
        raise FoldManifestError("data_artifact_hashes must be an object")
    for name, digest in artifact_hashes.items():
        if not str(name):
            raise FoldManifestError("data artifact names must not be empty")
        value = str(digest).lower()
        if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
            raise FoldManifestError("data artifact hashes must be SHA-256 digests")
    if execution_status == "EXECUTED" and not artifact_hashes:
        raise FoldManifestError("executed folds require at least one hashed data artifact")
    if str(payload["fold_hash"]) != _fold_hash(payload):
        raise FoldManifestError("fold_hash does not match the canonical fold payload")
    benchmark_holdout = held_out_benchmark is not None
    family_holdout = bool(payload["held_out_families"])
    if not benchmark_holdout and not family_holdout:
        raise FoldManifestError("fold must hold out a benchmark or at least one family")
    return payload


def leave_one_benchmark_out_folds(
    benchmarks: Sequence[str],
    **common: Any,
) -> list[dict[str, Any]]:
    names = sorted(set(map(str, benchmarks)))
    if len(names) < 2:
        raise FoldManifestError("leave-one-benchmark-out requires at least two benchmarks")
    return [
        build_fold_manifest(
            fold_id=f"lobo-{held_out}",
            training_benchmarks=[name for name in names if name != held_out],
            held_out_benchmark=held_out,
            **common,
        )
        for held_out in names
    ]


def leave_one_family_out_folds(
    family_to_models: Mapping[str, Sequence[str]],
    **common: Any,
) -> list[dict[str, Any]]:
    families = sorted(map(str, family_to_models))
    if len(families) < 2:
        raise FoldManifestError("leave-one-family-out requires at least two families")
    rows = []
    for held_out in families:
        training_families = [family for family in families if family != held_out]
        rows.append(
            build_fold_manifest(
                fold_id=f"lofo-{held_out}",
                training_families=training_families,
                held_out_families=[held_out],
                training_model_ids=[
                    model for family in training_families for model in family_to_models[family]
                ],
                evaluation_model_ids=list(family_to_models[held_out]),
                **common,
            )
        )
    return rows


def _fold_hash(payload: Mapping[str, Any]) -> str:
    return sha256_bytes(
        canonical_json_bytes({key: value for key, value in payload.items() if key != "fold_hash"})
    )
