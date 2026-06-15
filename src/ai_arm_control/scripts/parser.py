"""JSON parser for statically validated touch scripts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ai_arm_control.scripts.schema import (
    ScriptAction,
    ScriptStep,
    ScriptValidationError,
    TouchScript,
)
from ai_arm_control.scripts.validator import ScriptValidationLimits, validate_script

JsonObject = dict[str, Any]


class ScriptParseError(ValueError):
    """Raised when script JSON cannot be decoded."""


def load_script(
    path: str | Path,
    *,
    limits: ScriptValidationLimits | None = None,
) -> TouchScript:
    path = Path(path)
    try:
        raw_text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ScriptParseError(f"cannot read script file: {path}") from exc
    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise ScriptParseError(f"invalid JSON script: {path}") from exc
    return parse_script(data, limits=limits)


def parse_script(
    data: object,
    *,
    limits: ScriptValidationLimits | None = None,
) -> TouchScript:
    result = validate_script(data, limits=limits)
    if not result.valid:
        raise ScriptValidationError(result.issues)
    assert isinstance(data, dict)
    steps = _parse_steps(data["steps"], ())
    return TouchScript(script_version=data["script_version"], steps=steps, raw=dict(data))


def _parse_steps(values: list[object], index_path: tuple[int, ...]) -> list[ScriptStep]:
    steps: list[ScriptStep] = []
    for index, value in enumerate(values):
        assert isinstance(value, dict)
        current_path = (*index_path, index)
        action = ScriptAction(value["action"])
        parsed = ScriptStep(action=action, data=dict(value), index_path=current_path)
        steps.append(parsed)
        if action is ScriptAction.REPEAT:
            parsed.data["steps"] = _parse_steps(value["steps"], current_path)
    return steps
