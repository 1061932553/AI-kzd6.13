"""Long-press action primitive."""

from __future__ import annotations

from ai_arm_control.actions.models import TouchActionConfig, TouchArmAPI, TouchSleeper
from ai_arm_control.actions.result import TouchActionResult
from ai_arm_control.actions.tap import TapAction
from ai_arm_control.calibration.correction_grid import CorrectionGrid
from ai_arm_control.coordinates.mapper import CoordinateMapper
from ai_arm_control.coordinates.models import NormalizedPoint


def execute_long_press(
    point: NormalizedPoint,
    *,
    duration_ms: int,
    mapper: CoordinateMapper,
    arm: TouchArmAPI,
    config: TouchActionConfig | None = None,
    correction_grid: CorrectionGrid | None = None,
    sleeper: TouchSleeper | None = None,
) -> TouchActionResult:
    action = TapAction(
        mapper=mapper,
        arm=arm,
        config=config,
        correction_grid=correction_grid,
        sleeper=sleeper,
    )
    return action.execute(point, hold_ms=duration_ms, action_name="long_press")
