"""Swipe action primitive."""

from __future__ import annotations

from dataclasses import dataclass

from ai_arm_control.actions.interpolation import EasingMode
from ai_arm_control.actions.models import TouchActionConfig, TouchArmAPI, TouchSleeper
from ai_arm_control.actions.result import TouchActionLogEntry, TouchActionResult, TouchActionStatus
from ai_arm_control.actions.tap import SystemSleeper
from ai_arm_control.actions.trajectory import (
    TrajectoryPoint,
    build_linear_trajectory,
    build_polyline_trajectory,
    validate_total_time,
)
from ai_arm_control.calibration.correction_grid import CorrectionGrid
from ai_arm_control.coordinates.mapper import CoordinateMapper
from ai_arm_control.coordinates.models import NormalizedPoint


class SwipeCancelled(RuntimeError):
    """Raised by a cancellation token to stop a swipe."""


class SwipeCancelToken:
    def is_cancelled(self) -> bool:
        return False


@dataclass(frozen=True, slots=True)
class SwipeConfig:
    duration_ms: int = 600
    point_count: int = 30
    start_delay_ms: int = 80
    end_hold_ms: int = 80
    easing: EasingMode = EasingMode.LINEAR

    def __post_init__(self) -> None:
        if self.duration_ms <= 0:
            raise ValueError("duration_ms must be positive")
        if self.point_count < 2:
            raise ValueError("point_count must be at least 2")
        if self.start_delay_ms < 0:
            raise ValueError("start_delay_ms cannot be negative")
        if self.end_hold_ms < 0:
            raise ValueError("end_hold_ms cannot be negative")


class SwipeAction:
    def __init__(
        self,
        *,
        mapper: CoordinateMapper,
        arm: TouchArmAPI,
        touch_config: TouchActionConfig | None = None,
        swipe_config: SwipeConfig | None = None,
        correction_grid: CorrectionGrid | None = None,
        sleeper: TouchSleeper | None = None,
        cancel_token: SwipeCancelToken | None = None,
    ) -> None:
        self.mapper = mapper
        self.arm = arm
        self.touch_config = touch_config or TouchActionConfig()
        self.swipe_config = swipe_config or SwipeConfig()
        self.correction_grid = correction_grid
        self.sleeper = sleeper or SystemSleeper()
        self.cancel_token = cancel_token or SwipeCancelToken()

    def execute_line(self, start: NormalizedPoint, end: NormalizedPoint) -> TouchActionResult:
        trajectory = build_linear_trajectory(
            start=start,
            end=end,
            duration_ms=self.swipe_config.duration_ms,
            point_count=self.swipe_config.point_count,
            easing=self.swipe_config.easing,
        )
        return self.execute_trajectory(trajectory)

    def execute_polyline(self, points: list[NormalizedPoint]) -> TouchActionResult:
        trajectory = build_polyline_trajectory(
            points=points,
            duration_ms=self.swipe_config.duration_ms,
            point_count=self.swipe_config.point_count,
            easing=self.swipe_config.easing,
        )
        return self.execute_trajectory(trajectory)

    def execute_trajectory(self, trajectory: list[TrajectoryPoint]) -> TouchActionResult:
        logs: list[TouchActionLogEntry] = []
        pen_is_down = False
        try:
            validate_total_time(trajectory, self.swipe_config.duration_ms)
            arm_points = [self._map(point) for point in trajectory]
            _log(logs, "trajectory_ready", {"point_count": len(arm_points)})
            self._check_cancelled()
            first = arm_points[0]
            self.arm.move_xy(first.arm_xy.x, first.arm_xy.y)
            _log(logs, "move_start", first.to_dict())
            self.sleeper.sleep_ms(self.swipe_config.start_delay_ms)
            _log(logs, "start_delay", {"duration_ms": self.swipe_config.start_delay_ms})
            self.arm.pen_down(self.touch_config.press_depth)
            pen_is_down = True
            _log(logs, "pen_down", {"z": self.touch_config.press_depth})

            previous_offset = first.offset_ms
            for point in arm_points[1:]:
                self._check_cancelled()
                wait_ms = max(0, point.offset_ms - previous_offset)
                self.sleeper.sleep_ms(wait_ms)
                _log(logs, "trajectory_wait", {"duration_ms": wait_ms, "index": point.index})
                self.arm.move_xy(point.arm_xy.x, point.arm_xy.y)
                _log(logs, "move_point", point.to_dict())
                previous_offset = point.offset_ms

            self.sleeper.sleep_ms(self.swipe_config.end_hold_ms)
            _log(logs, "end_hold", {"duration_ms": self.swipe_config.end_hold_ms})
            self.arm.pen_up()
            pen_is_down = False
            _log(logs, "pen_up")
        except Exception as exc:
            _log(logs, "failure", {"error": str(exc)}, status=TouchActionStatus.FAILED)
            release_error = _try_pen_up(self.arm, logs)
            pen_is_down = False
            error = str(exc) if release_error is None else f"{exc}; pen_up failed: {release_error}"
            return TouchActionResult("swipe", TouchActionStatus.FAILED, logs, error=error)
        finally:
            if pen_is_down:
                _try_pen_up(self.arm, logs)
        return TouchActionResult("swipe", TouchActionStatus.SUCCEEDED, logs)

    def _map(self, point: TrajectoryPoint):
        arm_xy = (
            self.correction_grid.map_to_arm(self.mapper, point.normalized)
            if self.correction_grid is not None
            else self.mapper.normalized_to_arm(point.normalized)
        )
        return _ArmSwipePoint(point.index, point.normalized, arm_xy, point.offset_ms)

    def _check_cancelled(self) -> None:
        if self.cancel_token.is_cancelled():
            raise SwipeCancelled("swipe cancelled")


@dataclass(frozen=True, slots=True)
class _ArmSwipePoint:
    index: int
    normalized: NormalizedPoint
    arm_xy: object
    offset_ms: int

    def to_dict(self) -> dict[str, object]:
        return {
            "index": self.index,
            "normalized": {"x": self.normalized.x, "y": self.normalized.y},
            "arm_xy": {"x": self.arm_xy.x, "y": self.arm_xy.y},
            "offset_ms": self.offset_ms,
        }


def execute_swipe(
    start: NormalizedPoint,
    end: NormalizedPoint,
    *,
    mapper: CoordinateMapper,
    arm: TouchArmAPI,
    touch_config: TouchActionConfig | None = None,
    swipe_config: SwipeConfig | None = None,
    correction_grid: CorrectionGrid | None = None,
    sleeper: TouchSleeper | None = None,
    cancel_token: SwipeCancelToken | None = None,
) -> TouchActionResult:
    return SwipeAction(
        mapper=mapper,
        arm=arm,
        touch_config=touch_config,
        swipe_config=swipe_config,
        correction_grid=correction_grid,
        sleeper=sleeper,
        cancel_token=cancel_token,
    ).execute_line(start, end)


def _try_pen_up(arm: TouchArmAPI, logs: list[TouchActionLogEntry]) -> str | None:
    try:
        arm.pen_up()
    except Exception as exc:  # pragma: no cover
        _log(logs, "pen_up_after_failure", {"error": str(exc)}, status=TouchActionStatus.FAILED)
        return str(exc)
    _log(logs, "pen_up_after_failure")
    return None


def _log(
    logs: list[TouchActionLogEntry],
    step: str,
    detail: dict[str, object] | None = None,
    *,
    status: TouchActionStatus = TouchActionStatus.SUCCEEDED,
) -> None:
    logs.append(TouchActionLogEntry(step=step, status=status, detail=detail or {}))
