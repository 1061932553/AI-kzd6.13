"""Structured results for touch action primitives."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class TouchActionStatus(StrEnum):
    SUCCEEDED = "succeeded"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class TouchActionLogEntry:
    step: str
    status: TouchActionStatus
    detail: dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return {
            "step": self.step,
            "status": self.status.value,
            "detail": dict(self.detail),
        }


@dataclass(frozen=True, slots=True)
class TouchActionResult:
    action: str
    status: TouchActionStatus
    logs: list[TouchActionLogEntry]
    error: str | None = None

    @property
    def succeeded(self) -> bool:
        return self.status is TouchActionStatus.SUCCEEDED

    def to_dict(self) -> dict[str, object]:
        return {
            "action": self.action,
            "status": self.status.value,
            "logs": [entry.to_dict() for entry in self.logs],
            "error": self.error,
        }
