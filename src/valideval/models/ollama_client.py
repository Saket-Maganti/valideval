from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from valideval.schemas import ModelOutput


@dataclass
class OllamaRunner:
    model_id: str
    base_url: str = "http://localhost:11434"
    timeout_seconds: float = 120.0
    temperature: float = 0.0
    num_predict: int = 8

    def generate(self, prompt: str, *, seed: int | None = None) -> ModelOutput:
        try:
            import requests
        except ImportError as exc:  # pragma: no cover - optional dependency.
            raise RuntimeError("OllamaRunner requires the optional 'ollama' extra.") from exc

        payload: dict[str, Any] = {
            "model": self.model_id,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": self.temperature, "num_predict": self.num_predict},
        }
        if seed is not None:
            payload["options"]["seed"] = seed

        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
        except requests.RequestException as exc:  # pragma: no cover - requires local service.
            raise RuntimeError(
                "Ollama is unavailable or did not respond. Start Ollama locally or use the "
                "offline mock panel."
            ) from exc

        data = response.json()
        raw = str(data.get("response", ""))
        prediction = raw.strip().splitlines()[0].strip() if raw.strip() else ""
        return ModelOutput(
            prediction=prediction,
            raw_output=raw,
            metadata={
                "runner": "ollama",
                "model_id": self.model_id,
                "temperature": self.temperature,
                "num_predict": self.num_predict,
                "timeout_seconds": self.timeout_seconds,
                "seed": seed,
            },
        )
