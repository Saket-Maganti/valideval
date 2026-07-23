from __future__ import annotations

import hashlib
import json
import random
import re
from pathlib import Path
from typing import Any

from valideval.config import load_yaml
from valideval.schemas import BenchmarkItem, ConstructSpec, ScoreResult
from valideval.scoring import score_mcq
from valideval.scoring.mcq_utils import choice_text, item_choice_map

LABELS = ("A", "B", "C", "D")
PROMPT_DIR = Path("configs/prompts/gpqa")
DEFAULT_CONSTRUCT = (
    "graduate-level scientific question answering requiring expert-level domain reasoning"
)


class GPQADiamondJSONLBenchmark:
    benchmark_id = "gpqa_diamond"
    claimed_construct = DEFAULT_CONSTRUCT

    def __init__(
        self,
        path: str | Path,
        *,
        benchmark_id: str = "gpqa_diamond",
        artifact_scope: str = "real_gpqa_audit",
    ):
        self.path = Path(path)
        self.benchmark_id = benchmark_id
        self.artifact_scope = artifact_scope
        self.construct_spec = ConstructSpec(
            claimed_construct=self.claimed_construct,
            construct_tags=["graduate_science_reasoning", "multiple_choice"],
            construct_critical_fields=["question", "choices"],
            expected_threats=[
                "answer-choice artifacts",
                "distractor quality problems",
                "extraction/scoring instability",
                "item difficulty floor effects",
                "benchmark saturation for very strong models",
                "contamination/provenance uncertainty",
                "prompt-format sensitivity",
                "small item-count uncertainty",
                "proxy IRT limitations with small model panels",
            ],
            limitations=[
                "GPQA support uses a local JSONL export; ValidEval does not download or redistribute GPQA data.",
                "IRT outputs are proxy diagnostics and should not be described as ground-truth latent abilities.",
                _scope_limitation(artifact_scope),
            ],
            description=(
                "Local GPQA Diamond adapter for multiple-choice item loading, prompt rendering, "
                "and deterministic extraction/scoring validation."
            ),
            metadata={
                "benchmark_family": "gpqa",
                "split": "diamond",
                "artifact_scope": artifact_scope,
                "item_format_label": "GPQA-style multiple-choice items",
                "intended_use_report_label": _scope_intended_use(artifact_scope),
            },
        )
        self._items: list[BenchmarkItem] | None = None
        self._templates: dict[str, dict[str, Any]] = {}

    def load_items(self) -> list[BenchmarkItem]:
        if self._items is not None:
            return list(self._items)
        if not self.path.exists():
            raise FileNotFoundError(
                f"GPQA Diamond JSONL file does not exist: {self.path}. "
                "Provide a local JSONL export; ValidEval will not download GPQA automatically."
            )

        seen: set[str] = set()
        items: list[BenchmarkItem] = []
        with self.path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    record = json.loads(stripped)
                except json.JSONDecodeError as exc:
                    raise ValueError(
                        f"Invalid GPQA JSONL at line {line_number}: {exc.msg}."
                    ) from exc
                item = self._record_to_item(record, line_number=line_number, seen=seen)
                items.append(item)
        if not items:
            raise ValueError(f"GPQA Diamond JSONL contains no items: {self.path}")
        self._items = items
        return list(items)

    def render_prompt(self, item: BenchmarkItem, variant: str = "full") -> str:
        if (
            variant not in self.available_prompt_variants()
            and not (PROMPT_DIR / f"{variant}.yaml").exists()
        ):
            raise ValueError(
                f"Unknown GPQA prompt variant '{variant}'. "
                f"Available primary variants: {', '.join(self.available_prompt_variants())}."
            )
        template = self._template(variant).get("template")
        if not isinstance(template, str) or not template.strip():
            raise ValueError(f"GPQA prompt template is missing text for variant: {variant}")
        return template.format(
            question=item.prompt,
            choices=self._choice_lines(item, variant=variant),
        ).strip()

    def score_prediction(self, item: BenchmarkItem, prediction: str) -> ScoreResult:
        return score_mcq(item, prediction)

    def available_prompt_variants(self) -> list[str]:
        return [
            "full",
            "question_only",
            "choices_only",
            "randomized_choices",
            "answer_letter_only",
        ]

    def prompt_template_hash(self, variant: str) -> str:
        template = self._template(variant)
        payload = {
            "template_id": template.get("template_id", f"gpqa/{variant}"),
            "template": template.get("template", ""),
        }
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

    def _record_to_item(
        self,
        record: dict[str, Any],
        *,
        line_number: int,
        seen: set[str],
    ) -> BenchmarkItem:
        if not isinstance(record, dict):
            raise ValueError(f"GPQA JSONL line {line_number} must be a JSON object.")

        item_id = _required_str(record, "item_id", line_number)
        if item_id in seen:
            raise ValueError(f"Duplicate GPQA item_id at line {line_number}: {item_id}")
        seen.add(item_id)

        question = _required_str(record, "question", line_number)
        choices = _validate_choices(record.get("choices"), line_number=line_number, item_id=item_id)
        answer = _required_str(record, "answer", line_number).upper()
        if answer not in LABELS:
            raise ValueError(
                f"GPQA item {item_id} line {line_number} has answer '{answer}', "
                "expected one of A/B/C/D."
            )
        metadata = record.get("metadata") or {}
        if not isinstance(metadata, dict):
            raise ValueError(f"GPQA item {item_id} line {line_number} metadata must be an object.")
        _validate_no_answer_leakage(
            metadata,
            item_id=item_id,
            answer_label=answer,
            answer_text=str(choices[answer]),
        )

        domain = record.get("domain") or record.get("discipline")
        source = str(record.get("source", "gpqa"))
        split = str(record.get("split", "diamond"))
        item_metadata = {
            "benchmark_family": "gpqa",
            "split": split,
            "source": source,
            "artifact_scope": self.artifact_scope,
            "is_synthetic_fixture": self.artifact_scope == "gpqa_fixture_dry_run",
            "source_metadata": metadata,
        }
        if domain:
            item_metadata["domain"] = str(domain)

        return BenchmarkItem(
            item_id=item_id,
            prompt=question,
            answer=answer,
            choices=[f"{label}. {choices[label]}" for label in LABELS],
            source_document=source,
            metadata=item_metadata,
            construct_tags=[str(domain)] if domain else ["gpqa"],
            construct_critical_fields=["question", "choices"],
        )

    def _choice_lines(self, item: BenchmarkItem, *, variant: str) -> str:
        choices = item.choices or []
        if variant == "randomized_choices":
            choices = list(choices)
            rng = random.Random(_stable_int(f"{item.item_id}|{variant}"))
            rng.shuffle(choices)
        return "\n".join(choices)

    def _template(self, variant: str) -> dict[str, Any]:
        if variant not in self._templates:
            path = PROMPT_DIR / f"{variant}.yaml"
            if not path.exists():
                raise FileNotFoundError(f"Missing GPQA prompt template: {path}")
            self._templates[variant] = load_yaml(path)
        return self._templates[variant]


def _required_str(record: dict[str, Any], field: str, line_number: int) -> str:
    value = record.get(field)
    if not isinstance(value, str) or not value.strip():
        item = record.get("item_id", f"line {line_number}")
        raise ValueError(f"GPQA item {item} line {line_number} missing required field: {field}")
    return value.strip()


def _validate_choices(value: Any, *, line_number: int, item_id: str) -> dict[str, str]:
    if not isinstance(value, dict):
        raise ValueError(f"GPQA item {item_id} line {line_number} choices must be an object.")
    labels = {str(label).upper() for label in value}
    if labels != set(LABELS):
        raise ValueError(
            f"GPQA item {item_id} line {line_number} must contain exactly choices A/B/C/D."
        )
    output: dict[str, str] = {}
    for label in LABELS:
        text = value.get(label) if label in value else value.get(label.lower())
        if not isinstance(text, str) or not text.strip():
            raise ValueError(
                f"GPQA item {item_id} line {line_number} choice {label} must be non-empty text."
            )
        output[label] = text.strip()
    return output


FORBIDDEN_METADATA_KEY_RE = re.compile(r"(answer|correct|gold|target|solution|label)", re.I)


def _validate_no_answer_leakage(
    value: Any,
    *,
    item_id: str,
    answer_label: str,
    answer_text: str,
    path: str = "metadata",
) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            if FORBIDDEN_METADATA_KEY_RE.search(str(key)):
                raise ValueError(
                    f"GPQA item {item_id} metadata key '{path}.{key}' may leak the answer."
                )
            _validate_no_answer_leakage(
                nested,
                item_id=item_id,
                answer_label=answer_label,
                answer_text=answer_text,
                path=f"{path}.{key}",
            )
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            _validate_no_answer_leakage(
                nested,
                item_id=item_id,
                answer_label=answer_label,
                answer_text=answer_text,
                path=f"{path}[{index}]",
            )
    elif isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {answer_label.lower(), choice_text(answer_text).lower()}:
            raise ValueError(f"GPQA item {item_id} metadata value at '{path}' may leak the answer.")


def _stable_int(text: str) -> int:
    return int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:16], 16)


def _scope_limitation(artifact_scope: str) -> str:
    if artifact_scope == "gpqa_fixture_dry_run":
        return (
            "This GPQA fixture dry-run uses synthetic, non-GPQA items and mock outputs; "
            "it provides no scientific evidence about GPQA Diamond."
        )
    return (
        "A real GPQA audit requires a verified local GPQA Diamond JSONL export and cached "
        "open/local model outputs."
    )


def _scope_intended_use(artifact_scope: str) -> str:
    if artifact_scope == "gpqa_fixture_dry_run":
        return "GPQA fixture dry-run only; schema, scoring, and report plumbing validation."
    return "Real GPQA audit only after local data and cached open/local model outputs are supplied."


def randomized_choice_mapping_preserves_answer(item: BenchmarkItem) -> bool:
    choices = item_choice_map(item)
    answer = item.answer[0] if isinstance(item.answer, list) else item.answer
    return str(answer).upper() in choices
