"""Blinded, randomized human-validation packet builder for V5."""

from __future__ import annotations

import csv
import hashlib
import json
import random
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from valideval.leakage.guards import normalize_text, option_aware_hash

HUMAN_LABEL_TAXONOMY = (
    "INCORRECT_GOLD_ANSWER",
    "AMBIGUOUS_QUESTION",
    "AMBIGUOUS_OPTIONS",
    "MULTIPLE_DEFENSIBLE_ANSWERS",
    "INSUFFICIENT_CONTEXT",
    "OUTDATED_FACT",
    "SCORING_OR_EXTRACTION_ISSUE",
    "DOMAIN_SPECIALIST_DISPUTE",
    "NO_DETECTED_ISSUE",
    "UNSURE",
)

FORBIDDEN_PUBLIC_FIELDS = frozenset(
    {
        "control_expectation",
        "control_type",
        "diagnostic_rank",
        "diagnostic_score",
        "external_issue_label",
        "human_label",
        "intended_hypothesis",
        "is_high_risk",
        "model_correctness_pattern",
        "model_id",
        "risk_rank",
        "selection_reason",
        "source_item_id",
        "source_queue_position",
    }
)
CONTROL_TYPES = frozenset({"positive", "negative"})


@dataclass(frozen=True)
class BlindedHumanTask:
    schema_version: str
    blinded_task_id: str
    prompt: str
    choices: tuple[str, ...]
    recorded_answer: str
    subject: str
    review_question: str
    allowed_labels: tuple[str, ...]


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_json(value: Any) -> str:
    return _sha256_bytes(_canonical_json(value).encode("utf-8"))


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def _require_separate_packet_and_audit_dirs(packet_dir: Path, audit_dir: Path) -> None:
    packet = packet_dir.resolve()
    audit = audit_dir.resolve()
    if packet == audit or _is_relative_to(audit, packet):
        raise ValueError("private audit_dir must not be inside the annotator-visible packet_dir")


def _source_id(row: Mapping[str, Any], index: int) -> str:
    for key in ("item_id", "source_item_id", "id"):
        if key in row and row[key] not in (None, ""):
            return str(row[key])
    return f"row_{index}"


def _prompt(row: Mapping[str, Any]) -> str:
    return str(row.get("prompt") or row.get("question") or row.get("input") or "").strip()


def _choices(row: Mapping[str, Any]) -> tuple[str, ...]:
    value = row.get("choices") or row.get("options") or []
    if isinstance(value, Mapping):
        value = list(value.values())
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise ValueError("choices/options must be a sequence")
    return tuple(str(choice) for choice in value)


def _recorded_answer(row: Mapping[str, Any]) -> str:
    for key in ("recorded_answer", "gold_answer", "answer", "correct_answer"):
        if key in row and row[key] not in (None, ""):
            return str(row[key]).strip()
    return ""


def _control(row: Mapping[str, Any]) -> tuple[str, str]:
    control_type = str(row.get("control_type") or "").strip().casefold()
    expectation = str(row.get("control_expectation") or "").strip().upper()
    if control_type and control_type not in CONTROL_TYPES:
        raise ValueError(f"control_type must be one of {sorted(CONTROL_TYPES)}")
    if control_type and expectation not in HUMAN_LABEL_TAXONOMY:
        raise ValueError("control rows require a control_expectation from the frozen taxonomy")
    if expectation and not control_type:
        raise ValueError("control_expectation requires control_type")
    return control_type, expectation


def _validate_source_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    validated: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    seen_content: set[str] = set()
    for index, row in enumerate(rows):
        source_id = _source_id(row, index)
        prompt = _prompt(row)
        choices = _choices(row)
        answer = _recorded_answer(row)
        if not source_id or not prompt or not answer:
            raise ValueError(
                f"row {index} requires an item id, prompt/question, and recorded answer"
            )
        if source_id in seen_ids:
            raise ValueError(f"duplicate source item id: {source_id}")
        content_hash = option_aware_hash(prompt, choices)
        if content_hash in seen_content:
            raise ValueError(
                f"duplicate normalized question/options content at source item {source_id}"
            )
        seen_ids.add(source_id)
        seen_content.add(content_hash)
        control_type, control_expectation = _control(row)
        validated.append(
            {
                "source_item_id": source_id,
                "prompt": prompt,
                "choices": choices,
                "recorded_answer": answer,
                "subject": str(row.get("subject") or row.get("subset") or "unspecified"),
                "content_hash": content_hash,
                "control_type": control_type,
                "control_expectation": control_expectation,
                "selection_audit": {
                    key: row.get(key)
                    for key in sorted(FORBIDDEN_PUBLIC_FIELDS)
                    if key in row
                    and key not in {"source_item_id", "control_type", "control_expectation"}
                },
            }
        )
    return validated


def _assert_public_task_blinded(task: Mapping[str, Any]) -> None:
    offenders = sorted(set(task) & FORBIDDEN_PUBLIC_FIELDS)
    if offenders:
        raise ValueError(f"public human task leaks blinded fields: {', '.join(offenders)}")


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(_canonical_json(row) + "\n")


def build_blinded_human_packet(
    candidate_rows: Sequence[Mapping[str, Any]],
    *,
    control_rows: Sequence[Mapping[str, Any]] = (),
    packet_dir: str | Path,
    audit_dir: str | Path,
    sample_size: int | None = None,
    seed: int = 20260715,
    minimum_annotators: int = 2,
    require_positive_and_negative_controls: bool = True,
) -> dict[str, Any]:
    """Build a public packet and a physically separate private randomization key.

    Candidate selection and task order are deterministic for the frozen seed.  Controls are
    appended before a second shuffle, but neither control membership nor expected labels appear
    in the public packet.  This function creates study infrastructure, not human evidence.
    """

    public_dir = Path(packet_dir)
    private_dir = Path(audit_dir)
    _require_separate_packet_and_audit_dirs(public_dir, private_dir)
    if minimum_annotators < 2:
        raise ValueError("minimum_annotators must be at least 2")
    candidates = _validate_source_rows(candidate_rows)
    controls = _validate_source_rows(control_rows)
    if any(not row["control_type"] for row in controls):
        raise ValueError("every row supplied through control_rows must declare control_type")
    present_control_types = {row["control_type"] for row in controls}
    if require_positive_and_negative_controls and present_control_types != CONTROL_TYPES:
        raise ValueError("a blinded packet requires at least one positive and one negative control")
    candidate_ids = {row["source_item_id"] for row in candidates}
    overlap = candidate_ids & {row["source_item_id"] for row in controls}
    if overlap:
        raise ValueError(f"candidate/control source ids overlap: {', '.join(sorted(overlap))}")
    candidate_content = {row["content_hash"] for row in candidates}
    content_overlap = candidate_content & {row["content_hash"] for row in controls}
    if content_overlap:
        raise ValueError("candidate/control normalized content overlaps")

    requested = len(candidates) if sample_size is None else sample_size
    if requested <= 0:
        raise ValueError("sample_size must be positive")
    if requested > len(candidates):
        raise ValueError("sample_size exceeds available unique candidate rows")

    rng = random.Random(seed)
    inclusion_probability = requested / len(candidates)
    selected = [
        {
            **row,
            "inclusion_probability": inclusion_probability,
            "estimand_role": "probability_sample",
        }
        for row in rng.sample(candidates, requested)
    ]
    prepared_controls = [
        {**row, "inclusion_probability": None, "estimand_role": "control"} for row in controls
    ]
    combined = [*selected, *prepared_controls]
    rng.shuffle(combined)
    source_digest = _sha256_json(
        [
            {"content_hash": row["content_hash"], "source_item_id": row["source_item_id"]}
            for row in combined
        ]
    )
    packet_id = "human_v5_" + _sha256_json({"seed": seed, "source_digest": source_digest})[:16]

    public_rows: list[dict[str, Any]] = []
    mapping: list[dict[str, Any]] = []
    for position, row in enumerate(combined):
        blind_id = (
            "task_"
            + _sha256_json(
                {"packet_id": packet_id, "position": position, "source": row["source_item_id"]}
            )[:20]
        )
        task = BlindedHumanTask(
            schema_version="5.0",
            blinded_task_id=blind_id,
            prompt=row["prompt"],
            choices=row["choices"],
            recorded_answer=row["recorded_answer"],
            subject=(
                "unspecified"
                if row["control_type"]
                and normalize_text(row["subject"]).replace(" ", "_")
                in {"control", "positive_control", "negative_control"}
                else row["subject"]
            ),
            review_question=(
                "Under the frozen rubric, identify the primary item or scoring issue, if any."
            ),
            allowed_labels=HUMAN_LABEL_TAXONOMY,
        )
        public = asdict(task)
        _assert_public_task_blinded(public)
        public_rows.append(public)
        mapping.append(
            {
                "blinded_task_id": blind_id,
                "source_item_id": row["source_item_id"],
                "source_content_hash": row["content_hash"],
                "source_queue_position": position,
                "source_subject": row["subject"],
                "control_type": row["control_type"],
                "control_expectation": row["control_expectation"],
                "estimand_role": row["estimand_role"],
                "inclusion_probability": row["inclusion_probability"],
                "selection_audit": row["selection_audit"],
            }
        )

    public_dir.mkdir(parents=True, exist_ok=True)
    private_dir.mkdir(parents=True, exist_ok=True)
    tasks_path = public_dir / "blinded_tasks_v5.jsonl"
    template_path = public_dir / "annotation_template_v5.csv"
    public_manifest_path = public_dir / "packet_manifest_v5.json"
    private_manifest_path = private_dir / "randomization_key_v5.json"
    _write_jsonl(tasks_path, public_rows)
    packet_sha256 = _sha256_bytes(tasks_path.read_bytes())
    with template_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "blinded_task_id",
                "anonymized_annotator",
                "label",
                "confidence",
                "rationale",
                "expertise_attestation",
                "exclusion_reason",
                "duration_seconds",
            ],
        )
        writer.writeheader()
        for public_task in public_rows:
            writer.writerow({"blinded_task_id": public_task["blinded_task_id"]})

    public_manifest = {
        "schema_version": "5.0",
        "packet_id": packet_id,
        "packet_sha256": packet_sha256,
        "task_count": len(public_rows),
        "candidate_task_count": len(selected),
        "control_task_count": len(controls),
        "sampling_design": "simple_random_probability_sample_from_frozen_candidate_frame",
        "minimum_annotators_per_task": minimum_annotators,
        "label_taxonomy": list(HUMAN_LABEL_TAXONOMY),
        "blinding": [
            "diagnostic scores and ranks",
            "model correctness patterns",
            "risk-selection reason",
            "external issue labels",
            "intended hypothesis",
            "control membership and expected labels",
        ],
        "estimands": ["enrichment", "precision", "calibration", "issue_type_distribution"],
        "blocked_estimands": [
            "recall from a high-score-only sample",
            "population prevalence without probability sampling weights",
        ],
        "claim_state": "RESULT_REQUIRED",
        "evidence_status": "PLANNED",
    }
    private_manifest = {
        "schema_version": "5.0",
        "packet_id": packet_id,
        "packet_sha256": packet_sha256,
        "randomization_seed": seed,
        "candidate_frame_size": len(candidates),
        "candidate_inclusion_probability": inclusion_probability,
        "source_digest": source_digest,
        "minimum_annotators_per_task": minimum_annotators,
        "mapping": mapping,
        "audit_boundary": "PRIVATE_NOT_FOR_ANNOTATORS",
        "claim_state": "RESULT_REQUIRED",
    }
    _write_json(public_manifest_path, public_manifest)
    _write_json(private_manifest_path, private_manifest)
    return {
        "packet_id": packet_id,
        "packet_sha256": packet_sha256,
        "task_count": len(public_rows),
        "candidate_task_count": len(selected),
        "control_task_count": len(controls),
        "blinded_tasks_jsonl": str(tasks_path),
        "annotation_template_csv": str(template_path),
        "public_manifest_json": str(public_manifest_path),
        "private_randomization_key_json": str(private_manifest_path),
        "claim_state": "RESULT_REQUIRED",
        "evidence_status": "PLANNED",
    }


def load_human_queue(path: str | Path) -> list[dict[str, Any]]:
    source = Path(path)
    if source.suffix.lower() == ".csv":
        with source.open("r", encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))
    if source.suffix.lower() in {".jsonl", ".ndjson"}:
        rows: list[dict[str, Any]] = []
        with source.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                value = json.loads(line)
                if not isinstance(value, dict):
                    raise ValueError(f"{source}:{line_number} is not a JSON object")
                rows.append(value)
        return rows
    value = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(value, list) or not all(isinstance(row, dict) for row in value):
        raise ValueError("human queue JSON must contain a list of objects")
    return value
