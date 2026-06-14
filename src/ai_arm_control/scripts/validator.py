"""Static validator for touch scripts.

Validation is deliberately conservative: unknown fields are rejected, repeat
blocks are bounded, and every coordinate or timing value is checked before a
future runner can see the script.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Any

from ai_arm_control.scripts.schema import (
    SCRIPT_VERSION,
    ScriptAction,
    ValidationIssue,
    ValidationResult,
)

JsonObject = dict[str, Any]


@dataclass(frozen=True, slots=True)
class ScriptValidationLimits:
    max_steps: int = 500
    max_repeat_count: int = 100
    max_repeat_depth: int = 5
    max_expanded_steps: int = 5_000
    wait_min_ms: int = 0
    wait_max_ms: int = 600_000
    tap_hold_min_ms: int = 1
    tap_hold_max_ms: int = 5_000
    long_press_min_ms: int = 500
    long_press_max_ms: int = 5_000
    multi_tap_min_count: int = 1
    multi_tap_max_count: int = 20
    multi_tap_interval_max_ms: int = 5_000
    swipe_min_duration_ms: int = 100
    swipe_max_duration_ms: int = 10_000
    swipe_min_points: int = 2
    swipe_max_points: int = 100


class ScriptValidator:
    def __init__(self, limits: ScriptValidationLimits | None = None) -> None:
        self.limits = limits or ScriptValidationLimits()
        self._issues: list[ValidationIssue] = []

    def validate(self, script: object) -> ValidationResult:
        self._issues = []
        if not isinstance(script, dict):
            self._add("$", "script must be a JSON object")
            return self._result()

        self._validate_root(script)
        steps = script.get("steps")
        if isinstance(steps, list):
            expanded = self._validate_steps(steps, "$.steps", (), depth=0)
            if expanded > self.limits.max_expanded_steps:
                self._add(
                    "$.steps",
                    f"expanded step count must be <= {self.limits.max_expanded_steps}",
                    field="steps",
                )
        return self._result()

    def _validate_root(self, script: JsonObject) -> None:
        allowed = {"script_version", "steps", "metadata"}
        self._reject_unknown(script, allowed, "$")
        if script.get("script_version") != SCRIPT_VERSION:
            self._add(
                "$.script_version",
                f"script_version must be {SCRIPT_VERSION!r}",
                field="script_version",
            )
        steps = script.get("steps")
        if not isinstance(steps, list):
            self._add("$.steps", "steps is required and must be a list", field="steps")
        elif not steps:
            self._add("$.steps", "steps must not be empty", field="steps")
        elif len(steps) > self.limits.max_steps:
            self._add(
                "$.steps",
                f"steps length must be <= {self.limits.max_steps}",
                field="steps",
            )

    def _validate_steps(
        self,
        steps: list[object],
        path: str,
        index_path: tuple[int, ...],
        *,
        depth: int,
    ) -> int:
        expanded_count = 0
        for index, step in enumerate(steps):
            step_path = f"{path}[{index}]"
            current_path = (*index_path, index)
            expanded_count += self._validate_step(step, step_path, current_path, depth=depth)
        return expanded_count

    def _validate_step(
        self,
        step: object,
        path: str,
        index_path: tuple[int, ...],
        *,
        depth: int,
    ) -> int:
        if not isinstance(step, dict):
            self._add(path, "step must be an object", step_index=index_path[-1])
            return 1
        action_value = step.get("action")
        try:
            action = ScriptAction(action_value)
        except ValueError:
            self._add(
                f"{path}.action",
                "action is required and must be one of: "
                + ", ".join(item.value for item in ScriptAction),
                field="action",
                step_index=index_path[-1],
            )
            return 1

        match action:
            case ScriptAction.TAP:
                self._validate_tap(step, path, index_path[-1])
            case ScriptAction.LONG_PRESS:
                self._validate_long_press(step, path, index_path[-1])
            case ScriptAction.MULTI_TAP:
                self._validate_multi_tap(step, path, index_path[-1])
            case ScriptAction.SWIPE:
                self._validate_swipe(step, path, index_path[-1])
            case ScriptAction.WAIT:
                self._validate_wait(step, path, index_path[-1])
            case ScriptAction.HOME | ScriptAction.STOP:
                self._reject_unknown(step, {"action"}, path, step_index=index_path[-1])
            case ScriptAction.REPEAT:
                return self._validate_repeat(step, path, index_path, depth=depth)
        return 1

    def _validate_tap(self, step: JsonObject, path: str, step_index: int) -> None:
        allowed = {"action", "x", "y", "hold_ms", "timeout_ms", "retry"}
        self._reject_unknown(step, allowed, path, step_index=step_index)
        self._require_normalized_xy(step, path, step_index)
        self._optional_int_range(
            step,
            "hold_ms",
            self.limits.tap_hold_min_ms,
            self.limits.tap_hold_max_ms,
            path,
            step_index,
        )
        self._optional_timeout_retry(step, path, step_index)

    def _validate_long_press(self, step: JsonObject, path: str, step_index: int) -> None:
        allowed = {"action", "x", "y", "duration_ms", "timeout_ms", "retry"}
        self._reject_unknown(step, allowed, path, step_index=step_index)
        self._require_normalized_xy(step, path, step_index)
        self._required_int_range(
            step,
            "duration_ms",
            self.limits.long_press_min_ms,
            self.limits.long_press_max_ms,
            path,
            step_index,
        )
        self._optional_timeout_retry(step, path, step_index)

    def _validate_multi_tap(self, step: JsonObject, path: str, step_index: int) -> None:
        allowed = {
            "action",
            "x",
            "y",
            "count",
            "interval_ms",
            "hold_ms",
            "timeout_ms",
            "retry",
        }
        self._reject_unknown(step, allowed, path, step_index=step_index)
        self._require_normalized_xy(step, path, step_index)
        self._required_int_range(
            step,
            "count",
            self.limits.multi_tap_min_count,
            self.limits.multi_tap_max_count,
            path,
            step_index,
        )
        self._optional_int_range(
            step,
            "interval_ms",
            0,
            self.limits.multi_tap_interval_max_ms,
            path,
            step_index,
        )
        self._optional_int_range(
            step,
            "hold_ms",
            self.limits.tap_hold_min_ms,
            self.limits.tap_hold_max_ms,
            path,
            step_index,
        )
        self._optional_timeout_retry(step, path, step_index)

    def _validate_swipe(self, step: JsonObject, path: str, step_index: int) -> None:
        allowed = {
            "action",
            "start",
            "end",
            "path",
            "duration_ms",
            "points",
            "start_delay_ms",
            "end_hold_ms",
            "timeout_ms",
            "retry",
        }
        self._reject_unknown(step, allowed, path, step_index=step_index)
        has_start_end = "start" in step or "end" in step
        has_path = "path" in step
        if has_path and has_start_end:
            self._add(
                path,
                "swipe must use either path or start/end, not both",
                step_index=step_index,
            )
        if has_path:
            path_points = step.get("path")
            if not isinstance(path_points, list) or len(path_points) < 2:
                self._add(f"{path}.path", "path must contain at least 2 points", "path", step_index)
            else:
                for index, point in enumerate(path_points):
                    self._require_point_array(point, f"{path}.path[{index}]", "path", step_index)
        else:
            self._require_point_array(step.get("start"), f"{path}.start", "start", step_index)
            self._require_point_array(step.get("end"), f"{path}.end", "end", step_index)
        self._required_int_range(
            step,
            "duration_ms",
            self.limits.swipe_min_duration_ms,
            self.limits.swipe_max_duration_ms,
            path,
            step_index,
        )
        self._optional_int_range(
            step,
            "points",
            self.limits.swipe_min_points,
            self.limits.swipe_max_points,
            path,
            step_index,
        )
        self._optional_int_range(step, "start_delay_ms", 0, 5_000, path, step_index)
        self._optional_int_range(step, "end_hold_ms", 0, 5_000, path, step_index)
        self._optional_timeout_retry(step, path, step_index)

    def _validate_wait(self, step: JsonObject, path: str, step_index: int) -> None:
        self._reject_unknown(step, {"action", "duration_ms"}, path, step_index=step_index)
        self._required_int_range(
            step,
            "duration_ms",
            self.limits.wait_min_ms,
            self.limits.wait_max_ms,
            path,
            step_index,
        )

    def _validate_repeat(
        self,
        step: JsonObject,
        path: str,
        index_path: tuple[int, ...],
        *,
        depth: int,
    ) -> int:
        self._reject_unknown(step, {"action", "count", "steps"}, path, step_index=index_path[-1])
        self._required_int_range(
            step,
            "count",
            1,
            self.limits.max_repeat_count,
            path,
            index_path[-1],
        )
        if depth >= self.limits.max_repeat_depth:
            self._add(
                path,
                f"repeat depth must be <= {self.limits.max_repeat_depth}",
                step_index=index_path[-1],
            )
            return 1
        child_steps = step.get("steps")
        if not isinstance(child_steps, list) or not child_steps:
            self._add(
                f"{path}.steps",
                "repeat.steps must be a non-empty list",
                "steps",
                index_path[-1],
            )
            return 1
        child_expanded = self._validate_steps(
            child_steps,
            f"{path}.steps",
            index_path,
            depth=depth + 1,
        )
        count = step.get("count") if isinstance(step.get("count"), int) else 1
        return max(1, child_expanded * count)

    def _require_normalized_xy(self, step: JsonObject, path: str, step_index: int) -> None:
        self._required_number_range(step, "x", 0.0, 1.0, path, step_index)
        self._required_number_range(step, "y", 0.0, 1.0, path, step_index)

    def _require_point_array(
        self,
        value: object,
        path: str,
        field: str,
        step_index: int,
    ) -> None:
        if not isinstance(value, list | tuple) or len(value) != 2:
            self._add(path, f"{field} must be a [x, y] coordinate", field, step_index)
            return
        for axis, item in zip(("x", "y"), value, strict=True):
            if not self._is_number(item) or not 0.0 <= float(item) <= 1.0:
                self._add(
                    f"{path}.{axis}",
                    f"{field}.{axis} must be a finite number between 0.0 and 1.0",
                    field,
                    step_index,
                )

    def _required_number_range(
        self,
        step: JsonObject,
        field: str,
        minimum: float,
        maximum: float,
        path: str,
        step_index: int,
    ) -> None:
        if field not in step:
            self._add(f"{path}.{field}", f"{field} is required", field, step_index)
            return
        value = step[field]
        if not self._is_number(value) or not minimum <= float(value) <= maximum:
            self._add(
                f"{path}.{field}",
                f"{field} must be a finite number between {minimum} and {maximum}",
                field,
                step_index,
            )

    def _required_int_range(
        self,
        step: JsonObject,
        field: str,
        minimum: int,
        maximum: int,
        path: str,
        step_index: int,
    ) -> None:
        if field not in step:
            self._add(f"{path}.{field}", f"{field} is required", field, step_index)
            return
        self._validate_int_range(step[field], field, minimum, maximum, path, step_index)

    def _optional_int_range(
        self,
        step: JsonObject,
        field: str,
        minimum: int,
        maximum: int,
        path: str,
        step_index: int,
    ) -> None:
        if field in step:
            self._validate_int_range(step[field], field, minimum, maximum, path, step_index)

    def _validate_int_range(
        self,
        value: object,
        field: str,
        minimum: int,
        maximum: int,
        path: str,
        step_index: int,
    ) -> None:
        if isinstance(value, bool) or not isinstance(value, int):
            self._add(f"{path}.{field}", f"{field} must be an integer", field, step_index)
            return
        if not minimum <= value <= maximum:
            self._add(
                f"{path}.{field}",
                f"{field} must be between {minimum} and {maximum}",
                field,
                step_index,
            )

    def _optional_timeout_retry(self, step: JsonObject, path: str, step_index: int) -> None:
        self._optional_int_range(step, "timeout_ms", 1, 600_000, path, step_index)
        self._optional_int_range(step, "retry", 0, 5, path, step_index)

    def _reject_unknown(
        self,
        value: JsonObject,
        allowed: set[str],
        path: str,
        *,
        step_index: int | None = None,
    ) -> None:
        for field in sorted(set(value) - allowed):
            self._add(f"{path}.{field}", f"unknown field: {field}", field, step_index)

    @staticmethod
    def _is_number(value: object) -> bool:
        return not isinstance(value, bool) and isinstance(value, int | float) and isfinite(value)

    def _add(
        self,
        path: str,
        message: str,
        field: str | None = None,
        step_index: int | None = None,
    ) -> None:
        self._issues.append(
            ValidationIssue(path=path, message=message, field=field, step_index=step_index)
        )

    def _result(self) -> ValidationResult:
        return ValidationResult(valid=not self._issues, issues=list(self._issues))


def validate_script(
    script: object,
    *,
    limits: ScriptValidationLimits | None = None,
) -> ValidationResult:
    return ScriptValidator(limits).validate(script)
