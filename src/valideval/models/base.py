from __future__ import annotations

from typing import Protocol

from valideval.schemas import ModelOutput


class ModelRunner(Protocol):
    model_id: str

    def generate(self, prompt: str, *, seed: int | None = None) -> ModelOutput: ...
