"""Data contracts for versioned touch scripts.

These models are intentionally pure data containers. They do not import action
executors, adapters, HTTP clients, COM ports, cameras, or any hardware-facing
module.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

JsonObject = dict[str, Any]

SCRIPT_VERSION = "1.0"


class ScriptAction(StrEnum):
    TAP = "tap"
    LONG_PRESS = "long_press"
    MULTI_TAP = "multi_tap"
    SWIPE = "swipe"
    WAIT = "wait"
    HOME = "home"
    REPEAT = "repeat"
    STOP = "stop"


@dataclass(frozen=True, slots=True)
class ScriptStep:
    action: ScriptAction
    data: JsonObject
    index_path: tuple[int, ...]

    def to_dict(self) -> JsonObject:
        return dict(self.data)


@dataclass(frozen=True, slots=True)
class TouchScript:
    script_version: str
    steps: list[ScriptStep]
    raw: JsonObject

    def to_dict(self) -> JsonObject:
        return {
            "script_version": self.script_version,
            "steps": [step.to_dict() for step in self.steps],
        }


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    path: str
    message: str
    field: str | None = None
    step_index: int | None = None

    def to_dict(self) -> JsonObject:
        return {
            "path": self.path,
            "field": self.field,
            "step_index": self.step_index,
            "message": self.message,
        }


@dataclass(frozen=True, slots=True)
class ValidationResult:
    valid: bool
    issues: list[ValidationIssue] = field(default_factory=list)

    def to_dict(self) -> JsonObject:
        return {
            "valid": self.valid,
            "issues": [issue.to_dict() for issue in self.issues],
        }


class ScriptValidationError(ValueError):
    """Raised when a script cannot be parsed after static validation."""

    def __init__(self, issues: list[ValidationIssue]) -> None:
        super().__init__("script validation failed")
        self.issues = issues

    def to_dict(self) -> JsonObject:
        return {"error": str(self), "issues": [issue.to_dict() for issue in self.issues]}
