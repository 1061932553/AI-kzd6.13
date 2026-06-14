"""Multi-tap action primitive."""

from __future__ import annotations

from ai_arm_control.actions.models import (
    TouchActionConfig,
    TouchActionError,
    TouchArmAPI,
    TouchSleeper,
)
from ai_arm_control.actions.result import TouchActionLogEntry, TouchActionResult, TouchActionStatus
from ai_arm_control.actions.tap import TapAction
from ai_arm_control.calibration.correction_grid import CorrectionGrid
from ai_arm_control.coordinates.mapper import CoordinateMapper
from ai_arm_control.coordinates.models import NormalizedPoint


def execute_multi_tap(
    point: NormalizedPoint,
    *,
    count: int,
    mapper: CoordinateMapper,
    arm: TouchArmAPI,
    config: TouchActionConfig | None = None,
    interval_ms: int | None = None,
    hold_ms: int | None = None,
    correction_grid: CorrectionGrid | None = None,
    sleeper: TouchSleeper | None = None,
) -> TouchActionResult:
    if count <= 0:
        raise TouchActionError("count must be positive")
    action_config = config or TouchActionConfig()
    interval = action_config.timing.tap_interval_ms if interval_ms is None else interval_ms
    if interval < 0:
        raise TouchActionError("interval_ms cannot be negative")
    tapper = TapAction(
        mapper=mapper,
        arm=arm,
        config=action_config,
        correction_grid=correction_grid,
        sleeper=sleeper,
    )
    logs: list[TouchActionLogEntry] = []
    for index in range(count):
        result = tapper.execute(point, hold_ms=hold_ms, action_name=f"multi_tap[{index + 1}]")
        logs.extend(result.logs)
        if not result.succeeded:
            return TouchActionResult(
                "multi_tap",
                TouchActionStatus.FAILED,
                logs,
                error=result.error,
            )
        logs.append(
            TouchActionLogEntry(
                step="tap_completed",
                status=TouchActionStatus.SUCCEEDED,
                detail={"index": index + 1, "count": count},
            )
        )
        if index < count - 1:
            tapper.sleeper.sleep_ms(interval)
            logs.append(
                TouchActionLogEntry(
                    step="tap_interval",
                    status=TouchActionStatus.SUCCEEDED,
                    detail={"duration_ms": interval},
                )
            )
    return TouchActionResult("multi_tap", TouchActionStatus.SUCCEEDED, logs)
