from __future__ import annotations

import inspect
import json
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from valideval.no_run_preflight import NO_RUN_FORBIDDEN_ACTIONS, require_dry_run, write_manifest
from valideval.validation.synthetic_benchmark import LEGACY_SYNTHETIC_HARNESS_STATUS

DECOUPLED_SYNTHETIC_STATUS = "scaffold_only_not_executed"
FORBIDDEN_API_PARAMETERS = frozenset(
    {
        "is_flawed",
        "flaw_type",
        "flaw_family",
        "diagnostic",
        "target_flaw",
        "label",
        "injected",
        "ground_truth_flaw",
        "synthetic_label",
        "oracle_flaw",
    }
)
FORBIDDEN_HIDDEN_METADATA_KEYS = frozenset(
    {
        "is_flawed",
        "flaw_type",
        "flaw_strength",
        "injected_flaw",
        "ground_truth_flaw",
        "ground_truth_flaw_type",
        "ground_truth_is_flawed",
        "synthetic_label",
        "oracle_flaw",
    }
)


@dataclass(frozen=True)
class ObservableItemFeatures:
    item_id: str
    prompt: str
    choices: list[str]
    answer: str | None
    subject: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def public_metadata(self) -> dict[str, Any]:
        return {
            str(key): value
            for key, value in self.metadata.items()
            if str(key) not in FORBIDDEN_HIDDEN_METADATA_KEYS
        }


@dataclass(frozen=True)
class FlawAgnosticSyntheticModelConfig:
    ability: float
    verbosity: float = 0.0
    format_sensitivity: float = 0.0
    uncertainty: float = 0.0
    seed: int = 0


class FlawAgnosticSyntheticModel:
    def __init__(self, config: FlawAgnosticSyntheticModelConfig):
        self.config = config

    def predict(self, item: ObservableItemFeatures, variant: str = "original") -> str:
        """Return a deterministic answer from observable item features only."""
        choices = _choice_labels(item.choices)
        if not choices:
            return ""
        rng = random.Random(
            json.dumps(
                {
                    "ability": self.config.ability,
                    "format_sensitivity": self.config.format_sensitivity,
                    "item_id": item.item_id,
                    "metadata": item.public_metadata(),
                    "seed": self.config.seed,
                    "uncertainty": self.config.uncertainty,
                    "variant": variant,
                },
                sort_keys=True,
                default=str,
            )
        )
        if _variant_is_format_stress(variant):
            success_probability = _clip_probability(
                0.5 + 0.15 * self.config.ability - 0.25 * self.config.format_sensitivity
            )
        else:
            success_probability = _clip_probability(
                0.5 + 0.2 * self.config.ability - 0.2 * self.config.uncertainty
            )
        if item.answer in choices and rng.random() < success_probability:
            return str(item.answer)
        return rng.choice([choice for choice in choices if choice != item.answer] or choices)


@dataclass(frozen=True)
class PanelOutput:
    item_id: str
    model_id: str
    prediction: str
    answer: str | None
    valid_output: bool = True


class FixedDiagnosticReadout:
    def score_items(self, panel_outputs: list[PanelOutput]) -> dict[str, float]:
        """Compute one fixed item-instability score without switching by flaw family."""
        grouped: dict[str, list[PanelOutput]] = {}
        for output in panel_outputs:
            grouped.setdefault(output.item_id, []).append(output)
        scores: dict[str, float] = {}
        for item_id, outputs in grouped.items():
            if not outputs:
                scores[item_id] = 0.0
                continue
            invalid_rate = sum(not output.valid_output for output in outputs) / len(outputs)
            correctness = [
                float(output.answer is not None and output.prediction == output.answer)
                for output in outputs
            ]
            mean_correct = sum(correctness) / len(correctness)
            disagreement = 1.0 - max(mean_correct, 1.0 - mean_correct)
            scores[item_id] = max(invalid_rate, disagreement)
        return scores


def build_decoupled_synthetic_preflight(
    *,
    output: str | Path,
    dry_run: bool,
    execute_decoupled_synthetic: bool = False,
) -> dict[str, Any]:
    require_dry_run(
        dry_run=dry_run,
        execute=execute_decoupled_synthetic,
        execute_flag="--execute-decoupled-synthetic",
        action="decoupled synthetic harness preflight",
    )
    model_signature = inspect.signature(FlawAgnosticSyntheticModel.predict)
    readout_signature = inspect.signature(FixedDiagnosticReadout.score_items)
    model_forbidden = _forbidden_parameters(model_signature)
    readout_forbidden = _forbidden_parameters(readout_signature)
    hidden_label_guard = _hidden_label_guard_status()
    flaw_type_guard = _flaw_type_guard_status(model_signature, readout_signature)
    fixed_readout_guard = _fixed_readout_guard_status(readout_signature)
    preflight_status = (
        "dry_run_ready"
        if (
            not model_forbidden
            and not readout_forbidden
            and hidden_label_guard == "pass"
            and flaw_type_guard == "pass"
            and fixed_readout_guard == "pass"
        )
        else "blocked"
    )
    payload: dict[str, Any] = {
        "schema_version": "0.1",
        "mode": "dry_run_only",
        "status": "dry_run_only" if preflight_status == "dry_run_ready" else "blocked",
        "preflight_status": preflight_status,
        "scaffold_status": DECOUPLED_SYNTHETIC_STATUS,
        "module_path": str(Path(__file__)),
        "legacy_harness_status": LEGACY_SYNTHETIC_HARNESS_STATUS,
        "hidden_label_guard": hidden_label_guard,
        "flaw_type_guard": flaw_type_guard,
        "fixed_readout_guard": fixed_readout_guard,
        "forbidden_hidden_metadata_keys": sorted(FORBIDDEN_HIDDEN_METADATA_KEYS),
        "model_api": {
            "class": "FlawAgnosticSyntheticModel",
            "predict_parameters": list(model_signature.parameters),
            "forbidden_parameters_present": model_forbidden,
        },
        "readout_api": {
            "class": "FixedDiagnosticReadout",
            "score_items_parameters": list(readout_signature.parameters),
            "forbidden_parameters_present": readout_forbidden,
        },
        "generation_run": False,
        "model_inference_run": False,
        "auc_computed": False,
        "metrics_written": False,
        "evidence_state_impact": "none",
        "forbidden_actions": NO_RUN_FORBIDDEN_ACTIONS,
        "claim_state": "RESULT_REQUIRED",
        "notes": [
            "This preflight inspects scaffold APIs only.",
            "The decoupled scaffold has not generated items, run models, computed AUC, or tuned thresholds.",
            "Legacy controlled-output synthetic results remain historical wiring/sanity-check artifacts only.",
        ],
    }
    manifest_path = write_manifest(output, payload)
    payload["manifest_path"] = str(manifest_path)
    return payload


def _forbidden_parameters(signature: inspect.Signature) -> list[str]:
    return [name for name in signature.parameters if name in FORBIDDEN_API_PARAMETERS]


def _hidden_label_guard_status() -> str:
    field_names = set(ObservableItemFeatures.__dataclass_fields__)
    sample = ObservableItemFeatures(
        item_id="guard_item",
        prompt="Guard prompt",
        choices=["A", "B"],
        answer="A",
        metadata={key: "hidden" for key in FORBIDDEN_HIDDEN_METADATA_KEYS},
    )
    stripped_keys = set(sample.public_metadata())
    return (
        "pass"
        if field_names.isdisjoint(FORBIDDEN_HIDDEN_METADATA_KEYS)
        and stripped_keys.isdisjoint(FORBIDDEN_HIDDEN_METADATA_KEYS)
        else "blocked"
    )


def _flaw_type_guard_status(
    model_signature: inspect.Signature,
    readout_signature: inspect.Signature,
) -> str:
    forbidden = set(_forbidden_parameters(model_signature)) | set(
        _forbidden_parameters(readout_signature)
    )
    return "pass" if not forbidden else "blocked"


def _fixed_readout_guard_status(readout_signature: inspect.Signature) -> str:
    forbidden_parameters = _forbidden_parameters(readout_signature)
    source = inspect.getsource(FixedDiagnosticReadout.score_items)
    hidden_terms = [term for term in FORBIDDEN_HIDDEN_METADATA_KEYS if term in source]
    return "pass" if not forbidden_parameters and not hidden_terms else "blocked"


def _choice_labels(choices: list[str]) -> list[str]:
    labels = []
    for choice in choices:
        stripped = str(choice).strip()
        if stripped:
            labels.append(stripped[0].upper())
    return [label for label in labels if label]


def _variant_is_format_stress(variant: str) -> bool:
    return variant in {"json_only", "answer_letter_only", "terse_instructions", "format_only"}


def _clip_probability(value: float) -> float:
    return min(max(float(value), 0.01), 0.99)
