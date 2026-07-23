from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from valideval.config import load_yaml
from valideval.models.base import ModelRunner
from valideval.models.mock import (
    AlwaysA,
    ContextAwareMock,
    FormatFragile,
    KeywordMatcher,
    MajorityLabel,
    NoisyStrongMock,
    NoisyWeakMock,
    ShortcutExploiter,
)
from valideval.schemas import ModelOutput


@dataclass
class ModelPanel:
    panel_id: str
    models: list[ModelRunner]

    @property
    def model_ids(self) -> list[str]:
        return [model.model_id for model in self.models]


@dataclass
class CachedOutputModel:
    model_id: str
    panel_id: str

    def generate(self, prompt: str, *, seed: int | None = None) -> ModelOutput:
        raise ValueError(
            f"Panel '{self.panel_id}' is configured for cached outputs. "
            "Generate or import predictions and build matrices before running diagnostics."
        )


def load_panel(panel_id: str = "mock") -> ModelPanel:
    if panel_id == "mock":
        return ModelPanel(
            panel_id="mock",
            models=[
                AlwaysA(),
                MajorityLabel(),
                KeywordMatcher(),
                ShortcutExploiter(),
                ContextAwareMock(),
                NoisyStrongMock(),
                NoisyWeakMock(),
                FormatFragile(),
            ],
        )

    config_path = Path("configs/panels") / f"{panel_id}.yaml"
    if config_path.exists():
        data = load_yaml(config_path)
        models = [
            CachedOutputModel(str(row["model_id"]), panel_id=panel_id)
            for row in [*data.get("models", []), *data.get("baselines", [])]
            if row.get("model_id")
        ]
        if not models:
            raise ValueError(f"Panel config contains no model_id entries: {config_path}")
        return ModelPanel(panel_id=str(data.get("panel_id", panel_id)), models=models)

    raise ValueError(
        f"Unknown panel '{panel_id}'. Use 'mock' or add configs/panels/{panel_id}.yaml."
    )
