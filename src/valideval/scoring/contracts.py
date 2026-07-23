from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ParsedPrediction:
    value: str | None
    status: str
    failure_type: str
    detail: str | None = None

    @property
    def succeeded(self) -> bool:
        return (
            self.status == "success" and self.failure_type == "SUCCESS" and self.value is not None
        )
