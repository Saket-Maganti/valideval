"""Fail-closed V5 linkage between MMLU-Redux labels and benchmark items.

Structural subject/index alignment is useful for generating a manual-review queue, but it is
never promoted to confirmed item identity.  Output records contain identifiers and hashes only;
raw benchmark text is not written by this module.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from valideval.leakage.guards import normalize_text, normalized_text_hash, option_set_hash


class LinkageTier(str, Enum):
    CONFIRMED_EXACT = "CONFIRMED_EXACT"
    CONFIRMED_CANONICAL = "CONFIRMED_CANONICAL"
    HIGH_CONFIDENCE_MANUAL_REVIEW = "HIGH_CONFIDENCE_MANUAL_REVIEW"
    AMBIGUOUS = "AMBIGUOUS"
    UNMATCHED = "UNMATCHED"


CONFIRMED_TIERS = frozenset({LinkageTier.CONFIRMED_EXACT, LinkageTier.CONFIRMED_CANONICAL})
STRUCTURAL_METHODS = frozenset({"original_source_row_index", "canonical_subject_source_index"})
STABLE_ID_FIELDS = (
    "upstream_item_id",
    "source_item_id",
    "original_item_id",
    "helm_instance_id",
    "question_id",
)
SOURCE_INDEX_FIELDS = ("source_row_index", "source_index", "original_row_index", "row_index")


@dataclass(frozen=True)
class LinkageResult:
    redux_id: str
    benchmark_item_id: str
    tier: str
    method: str
    confidence: float
    candidate_count: int
    question_hash: str
    option_set_hash: str
    combined_content_hash: str
    structural_only: bool
    manual_review_required: bool
    collision_detected: bool

    @property
    def confirmed(self) -> bool:
        return LinkageTier(self.tier) in CONFIRMED_TIERS and not self.structural_only


@dataclass(frozen=True)
class LinkageSummary:
    status: str
    total_redux_rows: int
    confirmed_count: int
    manual_review_count: int
    ambiguous_count: int
    unmatched_count: int
    structural_only_count: int
    collision_count: int
    tier_counts: dict[str, int]
    method_counts: dict[str, int]
    claim_boundary: str


@dataclass(frozen=True)
class _Candidate:
    item_id: str
    subject: str
    source_index: int | None
    stable_keys: frozenset[str]
    question: str
    question_hash: str
    options: tuple[str, ...]
    option_hash: str
    answer: str
    combined_hash: str


def _metadata(row: Mapping[str, Any]) -> Mapping[str, Any]:
    value = row.get("metadata")
    return value if isinstance(value, Mapping) else {}


def _value(row: Mapping[str, Any], key: str) -> Any:
    value = row.get(key)
    return value if value not in (None, "") else _metadata(row).get(key)


def _item_id(row: Mapping[str, Any], fallback: str) -> str:
    for key in ("item_id", "source_issue_id", "id"):
        if key in row and row[key] not in (None, ""):
            return str(row[key])
    return fallback


def _subject(row: Mapping[str, Any]) -> str:
    return normalize_text(
        row.get("subject") or row.get("subset") or _metadata(row).get("subject") or ""
    ).replace(" ", "_")


def _source_index(row: Mapping[str, Any]) -> int | None:
    for key in SOURCE_INDEX_FIELDS:
        value = _value(row, key)
        if isinstance(value, int) and value >= 0:
            return value
        if isinstance(value, str) and value.strip().isdigit():
            return int(value.strip())
    match = re.search(r"(?:_|-)(\d+)$", str(row.get("item_id") or ""))
    return int(match.group(1)) if match else None


def _question(row: Mapping[str, Any]) -> str:
    return normalize_text(row.get("question") or row.get("prompt") or row.get("input") or "")


def _options(row: Mapping[str, Any]) -> tuple[str, ...]:
    raw = row.get("choices") or row.get("options") or []
    if isinstance(raw, Mapping):
        raw = list(raw.values())
    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
        return ()
    return tuple(normalize_text(value, strip_option_label=True) for value in raw)


def _answer(row: Mapping[str, Any]) -> str:
    for key in ("answer", "gold", "gold_answer", "correct_answer"):
        if key in row and row[key] not in (None, ""):
            return normalize_text(row[key])
    return ""


def _stable_keys(row: Mapping[str, Any]) -> frozenset[str]:
    keys: set[str] = set()
    for field in STABLE_ID_FIELDS:
        value = _value(row, field)
        if value not in (None, ""):
            keys.add(f"{field}:{normalize_text(value)}")
    return frozenset(keys)


def _combined_hash(question: str, options: Sequence[str], answer: str) -> str:
    if not question or not options or not answer:
        return ""
    payload = json.dumps(
        {"answer": answer, "options": sorted(options), "question": question},
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _candidate(row: Mapping[str, Any], index: int) -> _Candidate:
    question = _question(row)
    options = _options(row)
    answer = _answer(row)
    return _Candidate(
        item_id=_item_id(row, f"benchmark_row_{index:08d}"),
        subject=_subject(row),
        source_index=_source_index(row),
        stable_keys=_stable_keys(row),
        question=question,
        question_hash=normalized_text_hash(question) if question else "",
        options=options,
        option_hash=option_set_hash("", options) if options else "",
        answer=answer,
        combined_hash=_combined_hash(question, options, answer),
    )


class _CandidateIndex:
    def __init__(self, rows: Iterable[Mapping[str, Any]]) -> None:
        self.candidates = [_candidate(row, index) for index, row in enumerate(rows)]
        self.stable: dict[str, list[_Candidate]] = defaultdict(list)
        self.source_position: dict[tuple[str, int], list[_Candidate]] = defaultdict(list)
        self.question: dict[str, list[_Candidate]] = defaultdict(list)
        self.options: dict[str, list[_Candidate]] = defaultdict(list)
        self.combined: dict[str, list[_Candidate]] = defaultdict(list)
        for candidate in self.candidates:
            for key in candidate.stable_keys:
                self.stable[key].append(candidate)
            if candidate.subject and candidate.source_index is not None:
                self.source_position[(candidate.subject, candidate.source_index)].append(candidate)
            if candidate.question_hash:
                self.question[candidate.question_hash].append(candidate)
            if candidate.option_hash:
                self.options[candidate.option_hash].append(candidate)
            if candidate.combined_hash:
                self.combined[candidate.combined_hash].append(candidate)

    def resolve(
        self,
        redux_row: Mapping[str, Any],
        *,
        row_index: int,
        fuzzy_threshold: float,
    ) -> LinkageResult:
        redux_id = _item_id(redux_row, f"redux_row_{row_index:08d}")
        probe = _candidate(redux_row, row_index)

        stable_matches = _unique_candidates(
            candidate for key in probe.stable_keys for candidate in self.stable.get(key, [])
        )
        if stable_matches:
            return _resolved(
                redux_id,
                probe,
                stable_matches,
                LinkageTier.CONFIRMED_EXACT,
                "stable_upstream_id",
                1.0,
            )

        # Exact content is stronger than positional coincidence.  Options are required to agree
        # when both sides provide them; a question collision is therefore not silently confirmed.
        question_matches = self.question.get(probe.question_hash, []) if probe.question_hash else []
        compatible_question_matches = [
            candidate
            for candidate in question_matches
            if not probe.options
            or not candidate.options
            or probe.option_hash == candidate.option_hash
        ]
        if compatible_question_matches:
            unique_question_matches = _unique_candidates(compatible_question_matches)
            if len(unique_question_matches) > 1 and probe.combined_hash:
                combined_matches = [
                    candidate
                    for candidate in unique_question_matches
                    if candidate.combined_hash == probe.combined_hash
                ]
                if len(combined_matches) == 1:
                    return _resolved(
                        redux_id,
                        probe,
                        combined_matches,
                        LinkageTier.CONFIRMED_CANONICAL,
                        "question_options_answer_hash",
                        1.0,
                    )
            return _resolved(
                redux_id,
                probe,
                unique_question_matches,
                LinkageTier.CONFIRMED_CANONICAL,
                "exact_normalized_question",
                0.99,
            )

        if probe.option_hash:
            option_matches = self.options.get(probe.option_hash, [])
            if option_matches:
                return _resolved(
                    redux_id,
                    probe,
                    option_matches,
                    LinkageTier.HIGH_CONFIDENCE_MANUAL_REVIEW,
                    "exact_normalized_options",
                    0.8,
                    require_unique=True,
                )

        if probe.combined_hash:
            combined_matches = self.combined.get(probe.combined_hash, [])
            if combined_matches:
                return _resolved(
                    redux_id,
                    probe,
                    combined_matches,
                    LinkageTier.CONFIRMED_CANONICAL,
                    "question_options_answer_hash",
                    1.0,
                )

        if probe.subject and probe.source_index is not None:
            positional = self.source_position.get((probe.subject, probe.source_index), [])
            if positional:
                return _resolved(
                    redux_id,
                    probe,
                    positional,
                    LinkageTier.HIGH_CONFIDENCE_MANUAL_REVIEW,
                    "canonical_subject_source_index",
                    0.75,
                    structural_only=True,
                )

        fuzzy = _fuzzy_matches(probe, self.candidates, threshold=fuzzy_threshold)
        if fuzzy:
            top_score = fuzzy[0][0]
            tied = [candidate for score, candidate in fuzzy if abs(score - top_score) < 1e-12]
            tier = (
                LinkageTier.HIGH_CONFIDENCE_MANUAL_REVIEW
                if len(tied) == 1
                else LinkageTier.AMBIGUOUS
            )
            return _resolved(
                redux_id,
                probe,
                tied,
                tier,
                "reproducible_token_fuzzy_candidate",
                top_score,
            )

        return LinkageResult(
            redux_id=redux_id,
            benchmark_item_id="",
            tier=LinkageTier.UNMATCHED.value,
            method="no_candidate",
            confidence=0.0,
            candidate_count=0,
            question_hash=probe.question_hash,
            option_set_hash=probe.option_hash,
            combined_content_hash=probe.combined_hash,
            structural_only=False,
            manual_review_required=False,
            collision_detected=False,
        )


def _unique_candidates(candidates: Iterable[_Candidate]) -> list[_Candidate]:
    return list({candidate.item_id: candidate for candidate in candidates}.values())


def _resolved(
    redux_id: str,
    probe: _Candidate,
    candidates: Sequence[_Candidate],
    proposed_tier: LinkageTier,
    method: str,
    confidence: float,
    *,
    structural_only: bool = False,
    require_unique: bool = True,
) -> LinkageResult:
    unique = sorted(_unique_candidates(candidates), key=lambda candidate: candidate.item_id)
    collision = len(unique) != 1
    tier = LinkageTier.AMBIGUOUS if require_unique and collision else proposed_tier
    if method in STRUCTURAL_METHODS:
        structural_only = True
        if tier in CONFIRMED_TIERS:
            tier = LinkageTier.HIGH_CONFIDENCE_MANUAL_REVIEW
    selected = unique[0] if unique else None
    return LinkageResult(
        redux_id=redux_id,
        benchmark_item_id=selected.item_id if selected else "",
        tier=tier.value,
        method=method,
        confidence=round(confidence if not collision else min(confidence, 0.5), 8),
        candidate_count=len(unique),
        question_hash=probe.question_hash,
        option_set_hash=probe.option_hash,
        combined_content_hash=probe.combined_hash,
        structural_only=structural_only,
        manual_review_required=tier
        in {LinkageTier.HIGH_CONFIDENCE_MANUAL_REVIEW, LinkageTier.AMBIGUOUS},
        collision_detected=collision,
    )


def _token_set(value: str) -> set[str]:
    return set(re.findall(r"\w+", value, flags=re.UNICODE))


def _fuzzy_matches(
    probe: _Candidate,
    candidates: Sequence[_Candidate],
    *,
    threshold: float,
) -> list[tuple[float, _Candidate]]:
    if not probe.question:
        return []
    probe_tokens = _token_set(probe.question)
    scored: list[tuple[float, _Candidate]] = []
    for candidate in candidates:
        if probe.subject and candidate.subject and probe.subject != candidate.subject:
            continue
        candidate_tokens = _token_set(candidate.question)
        union = probe_tokens | candidate_tokens
        score = len(probe_tokens & candidate_tokens) / len(union) if union else 0.0
        if score >= threshold:
            scored.append((score, candidate))
    return sorted(scored, key=lambda pair: (-pair[0], pair[1].item_id))


def link_mmlu_redux_rows(
    redux_rows: Iterable[Mapping[str, Any]],
    benchmark_rows: Iterable[Mapping[str, Any]],
    *,
    fuzzy_threshold: float = 0.9,
) -> tuple[list[LinkageResult], LinkageSummary]:
    """Link rows using the preregistered order and return a fail-closed summary."""

    if not 0.0 <= fuzzy_threshold <= 1.0:
        raise ValueError("fuzzy_threshold must be between 0 and 1")
    index = _CandidateIndex(benchmark_rows)
    results = [
        index.resolve(row, row_index=row_index, fuzzy_threshold=fuzzy_threshold)
        for row_index, row in enumerate(redux_rows)
    ]
    tier_counts = Counter(result.tier for result in results)
    method_counts = Counter(result.method for result in results)
    confirmed = sum(result.confirmed for result in results)
    structural = sum(result.structural_only for result in results)
    all_confirmed = bool(results) and confirmed == len(results) and structural == 0
    summary = LinkageSummary(
        status="REDUX_ITEM_IDENTITY_CONFIRMED" if all_confirmed else "REDUX_EXPLORATORY_ONLY",
        total_redux_rows=len(results),
        confirmed_count=confirmed,
        manual_review_count=sum(result.manual_review_required for result in results),
        ambiguous_count=tier_counts[LinkageTier.AMBIGUOUS.value],
        unmatched_count=tier_counts[LinkageTier.UNMATCHED.value],
        structural_only_count=structural,
        collision_count=sum(result.collision_detected for result in results),
        tier_counts=dict(sorted(tier_counts.items())),
        method_counts=dict(sorted(method_counts.items())),
        claim_boundary=(
            "Only CONFIRMED_EXACT and CONFIRMED_CANONICAL rows may enter confirmatory external "
            "validation. Structural, fuzzy, ambiguous, and unmatched rows are exploratory only."
        ),
    )
    return results, summary


def _load_rows(path: str | Path) -> list[dict[str, Any]]:
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
        raise ValueError("JSON linkage inputs must be a list of objects")
    return value


def resolve_mmlu_redux_linkage(
    *,
    redux_path: str | Path,
    benchmark_path: str | Path,
    output_csv: str | Path,
    summary_json: str | Path | None = None,
    fuzzy_threshold: float = 0.9,
) -> LinkageSummary:
    """Resolve linkage files and write sanitized linkage/audit artifacts."""

    results, summary = link_mmlu_redux_rows(
        _load_rows(redux_path),
        _load_rows(benchmark_path),
        fuzzy_threshold=fuzzy_threshold,
    )
    output = Path(output_csv)
    output.parent.mkdir(parents=True, exist_ok=True)
    fields = list(LinkageResult.__dataclass_fields__)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for result in results:
            writer.writerow(asdict(result))
    if summary_json is not None:
        summary_output = Path(summary_json)
        summary_output.parent.mkdir(parents=True, exist_ok=True)
        summary_output.write_text(
            json.dumps(asdict(summary), indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    return summary
