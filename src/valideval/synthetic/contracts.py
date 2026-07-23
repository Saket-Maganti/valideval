"""Generator/detector separation contracts for V5 synthetic validation."""

from __future__ import annotations

import hashlib
import json
import random
import re
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field
from typing import Any

HIDDEN_SYNTHETIC_KEYS = frozenset(
    {
        "condition",
        "flaw_family",
        "flaw_label",
        "flaw_type",
        "generator_family",
        "ground_truth_flaw",
        "heldout_family",
        "hidden_label",
        "injected_flaw",
        "is_flawed",
        "label",
        "oracle_flaw",
        "private_seed",
        "severity",
        "synthetic_label",
    }
)
_KEY_RE = re.compile(r"[^a-z0-9]+")


class SyntheticBoundaryError(ValueError):
    """Raised when hidden synthetic state crosses the diagnostic boundary."""


def _key(value: object) -> str:
    return _KEY_RE.sub("_", str(value).strip().casefold()).strip("_")


def _hidden_paths(value: Any, path: str = "$") -> list[str]:
    found: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if _key(key) in HIDDEN_SYNTHETIC_KEYS:
                found.append(child_path)
            found.extend(_hidden_paths(child, child_path))
    elif isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            found.extend(_hidden_paths(child, f"{path}[{index}]"))
    return found


def assert_public_synthetic_isolation(value: Any) -> None:
    """Reject hidden labels, conditions, seeds, and generator fields recursively."""

    found = _hidden_paths(value)
    if found:
        raise SyntheticBoundaryError(
            "hidden synthetic state reached public/diagnostic input: " + ", ".join(found)
        )


@dataclass(frozen=True)
class ObservableSyntheticItem:
    item_id: str
    prompt: str
    choices: tuple[str, ...]
    public_metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        assert_public_synthetic_isolation(asdict(self))


@dataclass(frozen=True)
class HiddenSyntheticTruth:
    item_id: str
    condition: str
    flaw_family: str
    severity: float
    generator_family: str
    heldout_family: bool


@dataclass(frozen=True)
class ObservablePanelResponses:
    item_id: str
    model_responses: tuple[str | None, ...]
    public_covariates: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        assert_public_synthetic_isolation(asdict(self))


class FixedSyntheticReadout:
    """One frozen, flaw-agnostic readout over observable response patterns only."""

    def score(self, rows: Sequence[ObservablePanelResponses]) -> dict[str, float]:
        scores: dict[str, float] = {}
        for row in rows:
            responses = list(row.model_responses)
            if not responses:
                scores[row.item_id] = 1.0
                continue
            missing_rate = sum(response is None for response in responses) / len(responses)
            observed = [str(response) for response in responses if response is not None]
            if not observed:
                disagreement = 1.0
            else:
                modal_count = max(Counter(observed).values())
                disagreement = 1.0 - modal_count / len(observed)
            scores[row.item_id] = max(missing_rate, disagreement)
        return scores


def _neutral_item_id(rng: random.Random, used: set[str]) -> str:
    while True:
        value = f"syn_{rng.getrandbits(96):024x}"
        if value not in used:
            used.add(value)
            return value


def _render_fixture(condition: str, index: int) -> tuple[str, tuple[str, ...]]:
    # This fixture validates plumbing only. Observable manifestations differ by condition, but
    # class names, severity, seeds, and generator identifiers never cross the boundary.
    number = 10 + index
    choices = (str(number - 1), str(number), str(number + 1), str(number + 2))
    if condition == "no_flaw":
        prompt = f"Select the integer equal to {number}."
    elif condition == "one_flaw":
        prompt = f"Select the number near {number}; use the most defensible interpretation."
    elif condition == "multiple_flaws":
        prompt = f"Using the incomplete rule shown, select a value related to {number}."
    elif condition == "unseen_flaw":
        prompt = f"Select the value denoted by the undefined symbol next to {number}."
    else:
        prompt = f"Select a value for the displayed quantity {number}."
    return prompt, choices


def _fixture_response(item: ObservableSyntheticItem, model_index: int) -> str | None:
    digest = hashlib.sha256(
        json.dumps(
            {"item_id": item.item_id, "model_index": model_index, "prompt": item.prompt},
            sort_keys=True,
        ).encode("utf-8")
    ).digest()
    if digest[0] % 17 == 0:
        return None
    return item.choices[digest[1] % len(item.choices)]


def build_non_evidence_fixture(
    *,
    seed: int,
    item_count: int = 12,
    panel_size: int = 4,
) -> tuple[
    list[ObservableSyntheticItem],
    list[HiddenSyntheticTruth],
    list[ObservablePanelResponses],
]:
    """Build a deterministic wiring fixture with a separate private truth mapping."""

    if item_count < 4:
        raise ValueError("fixture item_count must be at least 4")
    if panel_size < 2:
        raise ValueError("fixture panel_size must be at least 2")
    rng = random.Random(seed)
    conditions = ["no_flaw", "one_flaw", "multiple_flaws", "unseen_flaw"]
    assignments = [conditions[index % len(conditions)] for index in range(item_count)]
    rng.shuffle(assignments)
    used: set[str] = set()
    public_items: list[ObservableSyntheticItem] = []
    hidden_truth: list[HiddenSyntheticTruth] = []
    for index, condition in enumerate(assignments):
        item_id = _neutral_item_id(rng, used)
        prompt, choices = _render_fixture(condition, index)
        public_items.append(
            ObservableSyntheticItem(
                item_id=item_id,
                prompt=prompt,
                choices=choices,
                public_metadata={"artifact_class": "NON_EVIDENCE_FIXTURE", "schema_version": "5.0"},
            )
        )
        hidden_truth.append(
            HiddenSyntheticTruth(
                item_id=item_id,
                condition=condition,
                flaw_family={
                    "no_flaw": "none",
                    "one_flaw": "ambiguous_instruction",
                    "multiple_flaws": "mixed",
                    "unseen_flaw": "undefined_symbol",
                }[condition],
                severity={
                    "no_flaw": 0.0,
                    "one_flaw": 0.5,
                    "multiple_flaws": 1.0,
                    "unseen_flaw": 0.75,
                }[condition],
                generator_family="v5_wiring_fixture",
                heldout_family=condition == "unseen_flaw",
            )
        )
    rng.shuffle(public_items)
    responses = [
        ObservablePanelResponses(
            item_id=item.item_id,
            model_responses=tuple(_fixture_response(item, model) for model in range(panel_size)),
            public_covariates={"panel_size": panel_size},
        )
        for item in public_items
    ]
    assert_public_synthetic_isolation([asdict(item) for item in public_items])
    assert_public_synthetic_isolation([asdict(row) for row in responses])
    return public_items, hidden_truth, responses
