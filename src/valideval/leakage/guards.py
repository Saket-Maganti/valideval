"""Deterministic V5 guards for leakage, overlap, and exact model identity.

The functions in this module are intentionally independent of model runners.  A runner
may receive only the mapping returned by :func:`build_generation_payload`; forensic
code that has access to gold answers must remain outside that boundary.
"""

from __future__ import annotations

import csv
import hashlib
import html
import json
import re
import unicodedata
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


class GoldAnswerLeakageError(ValueError):
    """Raised when generation or extraction context contains gold-derived state."""


class DiagnosticLabelLeakageError(ValueError):
    """Raised when a diagnostic input contains evaluation labels or label hints."""


_GOLD_KEYS = frozenset(
    {
        "answer",
        "answer_key",
        "correct_answer",
        "correct_choice",
        "correct_index",
        "correctness",
        "expected_answer",
        "expected_output",
        "gold",
        "gold_answer",
        "gold_label",
        "is_correct",
        "matched_answer",
        "reference_answer",
        "reward",
        "grader_score",
        "scored_correct",
        "score",
        "target",
        "target_answer",
        "target_label",
    }
)
_DIAGNOSTIC_LABEL_KEYS = _GOLD_KEYS | frozenset(
    {
        "anomaly_class",
        "diagnostic_label",
        "external_issue_label",
        "flaw_family",
        "flaw_label",
        "flaw_type",
        "ground_truth_flaw",
        "human_label",
        "injected_flaw",
        "intended_hypothesis",
        "is_flawed",
        "issue_label",
        "label",
        "repair_label",
        "risk_rank",
        "selection_reason",
        "synthetic_label",
    }
)
_PATH_LABEL_HINTS = frozenset(
    {
        "ambiguous",
        "clean",
        "control_negative",
        "control_positive",
        "flawed",
        "high_risk",
        "negative_class",
        "positive_class",
    }
)
_OPTION_LABEL_RE = re.compile(r"^\s*(?:\(?[A-Za-z0-9]{1,3}\)?[.)\]:-])\s+")
_HTML_TAG_RE = re.compile(r"<[^>]+>")
_LATEX_SPACING_RE = re.compile(r"\\(?:,|;|:|!|quad\b|qquad\b)")
_TOKEN_RE = re.compile(r"\w+", flags=re.UNICODE)
_KEY_NORMALIZER_RE = re.compile(r"[^a-z0-9]+")
_QUOTE_TRANSLATION = str.maketrans(
    {
        "\u2018": "'",
        "\u2019": "'",
        "\u201a": "'",
        "\u201b": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u201e": '"',
        "\u201f": '"',
        "\u2010": "-",
        "\u2011": "-",
        "\u2012": "-",
        "\u2013": "-",
        "\u2014": "-",
        "\u2212": "-",
        "\u00a0": " ",
    }
)


def _canonical_key(value: object) -> str:
    return _KEY_NORMALIZER_RE.sub("_", str(value).strip().casefold()).strip("_")


def normalize_text(value: object, *, strip_option_label: bool = False) -> str:
    """Return the V5 canonical text form used only for forensic comparison.

    Unicode compatibility normalization, HTML entity decoding, quote/dash normalization,
    HTML tag removal, LaTeX spacing normalization, case folding, and whitespace collapse are
    explicit.  Punctuation and mathematical content otherwise remain significant.
    """

    text = unicodedata.normalize("NFKC", html.unescape(str(value or "")))
    text = text.translate(_QUOTE_TRANSLATION)
    text = _HTML_TAG_RE.sub(" ", text)
    text = _LATEX_SPACING_RE.sub(" ", text)
    if strip_option_label:
        text = _OPTION_LABEL_RE.sub("", text)
    return " ".join(text.casefold().split())


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def normalized_text_hash(value: object) -> str:
    """Hash normalized text without exposing it in overlap artifacts."""

    return _sha256_text(normalize_text(value))


def _normalized_options(options: Sequence[object] | None) -> list[str]:
    return [normalize_text(option, strip_option_label=True) for option in (options or [])]


def option_aware_hash(question: object, options: Sequence[object] | None) -> str:
    """Hash a question and its options while preserving option order."""

    payload = {
        "normalization": "valideval_v5_nfkc_casefold_ordered_options",
        "question": normalize_text(question),
        "options": _normalized_options(options),
    }
    return _sha256_text(json.dumps(payload, sort_keys=True, separators=(",", ":")))


def option_set_hash(question: object, options: Sequence[object] | None) -> str:
    """Hash a question and option multiset to detect answer-option permutations."""

    payload = {
        "normalization": "valideval_v5_nfkc_casefold_option_multiset",
        "question": normalize_text(question),
        "options": sorted(_normalized_options(options)),
    }
    return _sha256_text(json.dumps(payload, sort_keys=True, separators=(",", ":")))


def _forbidden_paths(payload: Any, forbidden: frozenset[str], path: str = "$") -> list[str]:
    found: list[str] = []
    if isinstance(payload, Mapping):
        for key, value in payload.items():
            canonical = _canonical_key(key)
            child = f"{path}.{key}"
            if canonical in forbidden:
                found.append(child)
            found.extend(_forbidden_paths(value, forbidden, child))
    elif isinstance(payload, (list, tuple)):
        for index, value in enumerate(payload):
            found.extend(_forbidden_paths(value, forbidden, f"{path}[{index}]"))
    return found


def assert_gold_isolated(payload: Any, *, boundary: str = "generation") -> None:
    """Fail if any nested key can reveal gold or correctness feedback."""

    found = _forbidden_paths(payload, _GOLD_KEYS)
    if found:
        raise GoldAnswerLeakageError(
            f"{boundary} payload contains forbidden gold-derived fields: {', '.join(found)}"
        )


def assert_diagnostic_inputs_isolated(payload: Any) -> None:
    """Fail if diagnostics can access gold, human, external, or synthetic labels."""

    found = _forbidden_paths(payload, _DIAGNOSTIC_LABEL_KEYS)
    if found:
        raise DiagnosticLabelLeakageError(
            "diagnostic input contains forbidden label-derived fields: " + ", ".join(found)
        )


def assert_neutral_artifact_name(path: str | Path) -> None:
    """Reject filenames/directories that can reveal class membership to a consumer."""

    tokens = {_canonical_key(part) for part in Path(path).parts}
    offenders = sorted(tokens & _PATH_LABEL_HINTS)
    if offenders:
        raise DiagnosticLabelLeakageError(
            f"artifact path leaks class information through tokens: {', '.join(offenders)}"
        )


def build_generation_payload(
    item: Mapping[str, Any],
    *,
    prompt: str | None = None,
    few_shot_examples: Sequence[Mapping[str, Any]] | None = None,
    few_shot_near_duplicate_threshold: float = 0.9,
) -> dict[str, Any]:
    """Construct the only payload shape permitted to cross into model generation.

    Gold fields on the source item are deliberately not copied.  Nested public metadata and
    few-shot records are still checked fail-closed.  Few-shot examples must be already-rendered
    demonstrations with no target/gold fields.
    """

    metadata = dict(item.get("public_metadata") or {})
    examples = [dict(example) for example in (few_shot_examples or [])]
    if not 0.0 <= few_shot_near_duplicate_threshold <= 1.0:
        raise ValueError("few_shot_near_duplicate_threshold must be between 0 and 1")
    assert_gold_isolated(metadata, boundary="generation public_metadata")
    assert_gold_isolated(examples, boundary="generation few_shot_examples")
    rendered_prompt = prompt if prompt is not None else item.get("prompt") or item.get("question")
    target_id = str(item.get("item_id") or item.get("id") or "")
    target_tokens = set(_TOKEN_RE.findall(normalize_text(rendered_prompt)))
    for index, example in enumerate(examples):
        example_id = str(example.get("item_id") or example.get("id") or "")
        example_prompt = example.get("prompt") or example.get("question") or ""
        example_tokens = set(_TOKEN_RE.findall(normalize_text(example_prompt)))
        union = target_tokens | example_tokens
        similarity = len(target_tokens & example_tokens) / len(union) if union else 0.0
        if (target_id and example_id == target_id) or (
            target_tokens and similarity >= few_shot_near_duplicate_threshold
        ):
            raise GoldAnswerLeakageError(
                f"generation few_shot_examples[{index}] overlaps the target item"
            )
    payload = {
        "item_id": target_id,
        "prompt": str(rendered_prompt or ""),
        "choices": [str(choice) for choice in (item.get("choices") or item.get("options") or [])],
        "context": item.get("context"),
        "public_metadata": metadata,
        "few_shot_examples": examples,
    }
    assert_gold_isolated(payload)
    return payload


@dataclass(frozen=True)
class ExtractionOutcome:
    """Extraction result that never silently maps a failure to an incorrect answer."""

    status: str
    prediction: str | None
    failure_type: str | None = None

    def __post_init__(self) -> None:
        allowed = {"success", "failed"}
        if self.status not in allowed:
            raise ValueError(f"status must be one of {sorted(allowed)}")
        if self.status == "success" and (self.prediction is None or self.failure_type is not None):
            raise ValueError("successful extraction requires a prediction and no failure_type")
        if self.status == "failed" and (self.prediction is not None or not self.failure_type):
            raise ValueError("failed extraction requires prediction=None and a failure_type")


@dataclass(frozen=True)
class ModelExecutionIdentity:
    canonical_model_id: str
    checkpoint: str
    revision: str
    quantization_class: str
    base_or_instruction: str
    chat_template: str
    prompt_regime: str
    decoding_hash: str
    extraction_version: str


@dataclass(frozen=True)
class IdentityComparison:
    exact_match: bool
    mismatched_fields: tuple[str, ...]
    status: str


def compare_model_execution_identity(
    left: ModelExecutionIdentity, right: ModelExecutionIdentity
) -> IdentityComparison:
    """Require full execution identity; family-name similarity is never exact identity."""

    unverified_markers = ("BLOCKED", "PLANNED", "REQUIRED", "UNKNOWN", "UNVERIFIED")
    mismatches = tuple(
        field
        for field in asdict(left)
        if getattr(left, field) != getattr(right, field)
        or not str(getattr(left, field)).strip()
        or any(marker in str(getattr(left, field)).upper() for marker in unverified_markers)
        or not str(getattr(right, field)).strip()
        or any(marker in str(getattr(right, field)).upper() for marker in unverified_markers)
    )
    return IdentityComparison(
        exact_match=not mismatches,
        mismatched_fields=mismatches,
        status="EXACT_EXECUTION_IDENTITY" if not mismatches else "NOT_EXACT_EXECUTION_IDENTITY",
    )


@dataclass(frozen=True)
class OverlapCandidate:
    left_dataset: str
    left_item_id: str
    right_dataset: str
    right_item_id: str
    match_type: str
    similarity: float
    question_hash: str
    option_aware_hash: str
    option_set_hash: str
    manual_review_required: bool


@dataclass(frozen=True)
class _PreparedItem:
    dataset: str
    item_id: str
    question_hash: str
    ordered_hash: str
    option_set_hash: str
    shingles: frozenset[str]


def _item_question(row: Mapping[str, Any]) -> object:
    return row.get("question") or row.get("prompt") or row.get("input") or ""


def _item_options(row: Mapping[str, Any]) -> Sequence[object]:
    value = row.get("choices") or row.get("options") or []
    return value if isinstance(value, Sequence) and not isinstance(value, (str, bytes)) else []


def _token_shingles(value: object, width: int = 3) -> frozenset[str]:
    tokens = _TOKEN_RE.findall(normalize_text(value))
    if len(tokens) < width:
        return frozenset(tokens)
    return frozenset(
        " ".join(tokens[index : index + width]) for index in range(len(tokens) - width + 1)
    )


def _prepare_items(collections: Mapping[str, Iterable[Mapping[str, Any]]]) -> list[_PreparedItem]:
    prepared: list[_PreparedItem] = []
    for dataset, rows in sorted(collections.items()):
        for index, row in enumerate(rows):
            item_id = str(row.get("item_id") or row.get("id") or f"row_{index:08d}")
            question = _item_question(row)
            options = _item_options(row)
            normalized_question = normalize_text(question)
            prepared.append(
                _PreparedItem(
                    dataset=dataset,
                    item_id=item_id,
                    question_hash=normalized_text_hash(question) if normalized_question else "",
                    ordered_hash=option_aware_hash(question, options)
                    if normalized_question
                    else "",
                    option_set_hash=option_set_hash(question, options)
                    if normalized_question
                    else "",
                    shingles=_token_shingles(question),
                )
            )
    return prepared


def build_overlap_candidates(
    collections: Mapping[str, Iterable[Mapping[str, Any]]],
    *,
    fuzzy_threshold: float = 0.8,
    max_fuzzy_candidates_per_item: int = 20,
    max_exact_pairs_per_hash: int = 10_000,
    max_shingle_bucket_size: int = 500,
) -> list[OverlapCandidate]:
    """Build exact/permutation/fuzzy cross-dataset overlap candidates deterministically.

    Exact matches use hash buckets. Fuzzy retrieval uses a token-shingle inverted index rather
    than a full cross-product. Extremely common shingles are ignored as non-discriminating, and
    an unexpectedly large exact collision bucket fails closed instead of exhausting memory.
    """

    if not 0.0 <= fuzzy_threshold <= 1.0:
        raise ValueError("fuzzy_threshold must be between 0 and 1")
    if max_fuzzy_candidates_per_item <= 0:
        raise ValueError("max_fuzzy_candidates_per_item must be positive")
    if max_exact_pairs_per_hash <= 0 or max_shingle_bucket_size <= 0:
        raise ValueError("overlap candidate limits must be positive")
    items = _prepare_items(collections)
    candidates: dict[tuple[str, str, str, str], OverlapCandidate] = {}

    def emit_exact(attribute: str, match_type: str, manual_review: bool) -> None:
        buckets: dict[str, list[int]] = {}
        for item_index, item in enumerate(items):
            value = str(getattr(item, attribute))
            if value:
                buckets.setdefault(value, []).append(item_index)
        for hash_value, bucket in buckets.items():
            dataset_counts: dict[str, int] = {}
            for item_index in bucket:
                dataset = items[item_index].dataset
                dataset_counts[dataset] = dataset_counts.get(dataset, 0) + 1
            cross_pair_count = (
                len(bucket) ** 2 - sum(count**2 for count in dataset_counts.values())
            ) // 2
            if cross_pair_count > max_exact_pairs_per_hash:
                raise ValueError(
                    f"exact overlap hash {hash_value[:12]} produced {cross_pair_count} pairs; "
                    "inspect the collision bucket before increasing max_exact_pairs_per_hash"
                )
            for offset, left_index in enumerate(bucket):
                for right_index in bucket[offset + 1 :]:
                    left, right = items[left_index], items[right_index]
                    if left.dataset == right.dataset:
                        continue
                    pair = (left.dataset, left.item_id, right.dataset, right.item_id)
                    candidates.setdefault(
                        pair,
                        _candidate(left, right, match_type, 1.0, manual_review),
                    )

    emit_exact("ordered_hash", "EXACT_OPTION_AWARE", False)
    emit_exact("option_set_hash", "OPTION_PERMUTATION", True)
    emit_exact("question_hash", "EXACT_QUESTION", True)

    shingle_index: dict[str, list[int]] = {}
    for item_index, item in enumerate(items):
        for shingle in item.shingles:
            shingle_index.setdefault(shingle, []).append(item_index)
    for left_index, left in enumerate(items):
        possible: set[int] = set()
        for shingle in left.shingles:
            bucket = shingle_index[shingle]
            if len(bucket) <= max_shingle_bucket_size:
                possible.update(bucket)
        fuzzy: list[tuple[float, _PreparedItem]] = []
        for right_index in possible:
            if right_index <= left_index:
                continue
            right = items[right_index]
            if left.dataset == right.dataset:
                continue
            pair = (left.dataset, left.item_id, right.dataset, right.item_id)
            if pair in candidates:
                continue
            union = left.shingles | right.shingles
            similarity = len(left.shingles & right.shingles) / len(union) if union else 0.0
            if similarity >= fuzzy_threshold:
                fuzzy.append((similarity, right))
        for similarity, right in sorted(
            fuzzy, key=lambda pair: (-pair[0], pair[1].dataset, pair[1].item_id)
        )[:max_fuzzy_candidates_per_item]:
            pair = (left.dataset, left.item_id, right.dataset, right.item_id)
            candidates[pair] = _candidate(left, right, "TOKEN_NGRAM_CANDIDATE", similarity, True)

    return sorted(
        candidates.values(),
        key=lambda row: (
            row.left_dataset,
            row.left_item_id,
            row.right_dataset,
            row.right_item_id,
        ),
    )


def _candidate(
    left: _PreparedItem,
    right: _PreparedItem,
    match_type: str,
    similarity: float,
    manual_review_required: bool,
) -> OverlapCandidate:
    return OverlapCandidate(
        left_dataset=left.dataset,
        left_item_id=left.item_id,
        right_dataset=right.dataset,
        right_item_id=right.item_id,
        match_type=match_type,
        similarity=round(similarity, 8),
        question_hash=left.question_hash if left.question_hash == right.question_hash else "",
        option_aware_hash=left.ordered_hash if left.ordered_hash == right.ordered_hash else "",
        option_set_hash=left.option_set_hash
        if left.option_set_hash == right.option_set_hash
        else "",
        manual_review_required=manual_review_required,
    )


def write_overlap_candidates_csv(path: str | Path, rows: Iterable[OverlapCandidate]) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    fields = list(OverlapCandidate.__dataclass_fields__)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))
    return output
