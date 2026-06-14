"""Tap action primitive."""

from __future__ import annotations

import time
from dataclasses import replace

from ai_arm_control.actions.models import (
    TouchActionConfig,
    TouchArmAPI,
    TouchSleeper,
    TouchTarget,
)
from ai_arm_control.actions.result import TouchActionLogEntry, TouchActionResult, TouchActionStatus
from ai_arm_control.calibration.correction_grid import CorrectionGrid
from ai_arm_control.coordinates.mapper import CoordinateMapper
from ai_arm_control.coordinates.models import NormalizedPoint


class SystemSleeper:
    def sleep_ms(self, duration_ms: int) -> None:
        if duration_ms > 0:
            time.sleep(duration_ms / 1000)


class TapAction:
    def __init__(
        self,
        *,
        mapper: CoordinateMapper,
        arm: TouchArmAPI,
        config: TouchActionConfig | None = None,
        correction_grid: CorrectionGrid | None = None,
        sleeper: TouchSleeper | None = None,
    ) -> None:
        self.mapper = mapper
        self.arm = arm
        self.config = config or TouchActionConfig()
        self.correction_grid = correction_grid
        self.sleeper = sleeper or SystemSleeper()

    def execute(
        self,
        point: NormalizedPoint,
        *,
        hold_ms: int | None = None,
        action_name: str = "tap",
    ) -> TouchActionResult:
        timing = self.config.timing
        if hold_ms is not None:
            if hold_ms < 0:
                return _failed(action_name, "hold_ms cannot be negative", [])
            timing = replace(timing, hold_ms=hold_ms)
        logs: list[TouchActionLogEntry] = []
        pen_is_down = False
        try:
            target = self._target(point)
            _log(logs, "coordinate_mapping", TouchActionStatus.SUCCEEDED, target.to_dict())
            _log(
                logs,
                "safety_check",
                TouchActionStatus.SUCCEEDED,
                {"arm_xy": target.to_dict()["arm_xy"]},
            )
            self.arm.move_xy(target.arm_xy.x, target.arm_xy.y)
            _log(
                logs,
                "move_xy",
                TouchActionStatus.SUCCEEDED,
                {"x": target.arm_xy.x, "y": target.arm_xy.y},
            )
            self._sleep(logs, "xy_settle", timing.xy_settle_ms)
            self.arm.pen_down(self.config.press_depth)
            pen_is_down = True
            _log(logs, "pen_down", TouchActionStatus.SUCCEEDED, {"z": self.config.press_depth})
            self._sleep(logs, "down_delay", timing.down_delay_ms)
            self._sleep(logs, "hold", timing.hold_ms)
            self.arm.pen_up()
            pen_is_down = False
            _log(logs, "pen_up", TouchActionStatus.SUCCEEDED)
            self._sleep(logs, "up_delay", timing.up_delay_ms)
        except Exception as exc:
            _log(logs, "failure", TouchActionStatus.FAILED, {"error": str(exc)})
            release_error = _try_pen_up(self.arm, logs)
            pen_is_down = False
            error = str(exc) if release_error is None else f"{exc}; pen_up failed: {release_error}"
            return TouchActionResult(action_name, TouchActionStatus.FAILED, logs, error=error)
        finally:
            if pen_is_down:
                _try_pen_up(self.arm, logs)
        return TouchActionResult(action_name, TouchActionStatus.SUCCEEDED, logs)

    def _target(self, point: NormalizedPoint) -> TouchTarget:
        arm_xy = (
            self.correction_grid.map_to_arm(self.mapper, point)
            if self.correction_grid is not None
            else self.mapper.normalized_to_arm(point)
        )
        return TouchTarget(normalized=point, arm_xy=arm_xy)

    def _sleep(self, logs: list[TouchActionLogEntry], step: str, duration_ms: int) -> None:
        self.sleeper.sleep_ms(duration_ms)
        _log(logs, step, TouchActionStatus.SUCCEEDED, {"duration_ms": duration_ms})


def execute_tap(
    point: NormalizedPoint,
    *,
    mapper: CoordinateMapper,
    arm: TouchArmAPI,
    config: TouchActionConfig | None = None,
    correction_grid: CorrectionGrid | None = None,
    sleeper: TouchSleeper | None = None,
) -> TouchActionResult:
    return TapAction(
        mapper=mapper,
        arm=arm,
        config=config,
        correction_grid=correction_grid,
        sleeper=sleeper,
    ).execute(point)


def _try_pen_up(arm: TouchArmAPI, logs: list[TouchActionLogEntry]) -> str | None:
    try:
        arm.pen_up()
    except Exception as exc:  # pragma: no cover - tested through failure result content.
        _log(logs, "pen_up_after_failure", TouchActionStatus.FAILED, {"error": str(exc)})
        return str(exc)
    _log(logs, "pen_up_after_failure", TouchActionStatus.SUCCEEDED)
    return None


def _log(
    logs: list[TouchActionLogEntry],
    step: str,
    status: TouchActionStatus,
    detail: dict[str, object] | None = None,
) -> None:
    logs.append(TouchActionLogEntry(step=step, status=status, detail=detail or {}))


def _failed(action: str, error: str, logs: list[TouchActionLogEntry]) -> TouchActionResult:
    _log(logs, "validation", TouchActionStatus.FAILED, {"error": error})
    return TouchActionResult(action, TouchActionStatus.FAILED, logs, error=error)
