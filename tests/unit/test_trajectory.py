from __future__ import annotations

import pytest

from ai_arm_control.actions import (
    EasingMode,
    SwipeAction,
    SwipeConfig,
    TouchActionStatus,
    TrajectoryError,
    build_linear_trajectory,
    build_polyline_trajectory,
)
from ai_arm_control.coordinates import (
    Bounds2D,
    CoordinateError,
    CoordinateMapper,
    CoordinateMapperConfig,
    NormalizedPoint,
    ScreenROI,
)


class FakeArm:
    def __init__(self, *, fail_on_move_index: int | None = None) -> None:
        self.calls: list[tuple[str, tuple[float, ...]]] = []
        self.move_count = 0
        self.fail_on_move_index = fail_on_move_index

    def move_xy(self, x: float, y: float) -> object:
        self.move_count += 1
        self.calls.append(("move_xy", (x, y)))
        if self.fail_on_move_index == self.move_count:
            raise RuntimeError("move failed")
        return {"ok": True}

    def pen_down(self, z: float) -> object:
        self.calls.append(("pen_down", (z,)))
        return {"ok": True}

    def pen_up(self) -> object:
        self.calls.append(("pen_up", ()))
        return {"ok": True}


class FakeSleeper:
    def __init__(self) -> None:
        self.durations: list[int] = []

    def sleep_ms(self, duration_ms: int) -> None:
        self.durations.append(duration_ms)


class CancelAfter:
    def __init__(self, checks: int) -> None:
        self.remaining = checks

    def is_cancelled(self) -> bool:
        self.remaining -= 1
        return self.remaining < 0


def build_mapper() -> CoordinateMapper:
    return CoordinateMapper(
        CoordinateMapperConfig(
            screen_roi=ScreenROI.from_sequence([64, 32, 482, 911]),
            arm_bounds=Bounds2D(min_x=0, max_x=366, min_y=0, max_y=160),
        )
    )


def test_linear_trajectory_point_count_and_total_time() -> None:
    trajectory = build_linear_trajectory(
        start=NormalizedPoint(0.5, 0.8),
        end=NormalizedPoint(0.5, 0.2),
        duration_ms=600,
        point_count=30,
    )

    assert len(trajectory) == 30
    assert trajectory[0].normalized == NormalizedPoint(0.5, 0.8)
    assert trajectory[-1].normalized == NormalizedPoint(0.5, 0.2)
    assert trajectory[0].offset_ms == 0
    assert trajectory[-1].offset_ms == 600


def test_polyline_trajectory_includes_corner_path() -> None:
    trajectory = build_polyline_trajectory(
        points=[NormalizedPoint(0.1, 0.1), NormalizedPoint(0.9, 0.1), NormalizedPoint(0.9, 0.9)],
        duration_ms=800,
        point_count=5,
    )

    assert len(trajectory) == 5
    assert trajectory[0].normalized == NormalizedPoint(0.1, 0.1)
    assert trajectory[-1].normalized == NormalizedPoint(0.9, 0.9)
    assert any(point.normalized.y == pytest.approx(0.1) for point in trajectory)


def test_ease_in_out_keeps_endpoints_and_changes_midpoint() -> None:
    linear = build_linear_trajectory(
        start=NormalizedPoint(0.0, 0.0),
        end=NormalizedPoint(1.0, 1.0),
        duration_ms=100,
        point_count=4,
    )
    eased = build_linear_trajectory(
        start=NormalizedPoint(0.0, 0.0),
        end=NormalizedPoint(1.0, 1.0),
        duration_ms=100,
        point_count=4,
        easing=EasingMode.EASE_IN_OUT,
    )

    assert eased[0].normalized == linear[0].normalized
    assert eased[-1].normalized == linear[-1].normalized
    assert eased[1].normalized.x != pytest.approx(linear[1].normalized.x)


def test_invalid_trajectory_parameters_are_rejected() -> None:
    with pytest.raises(TrajectoryError):
        build_linear_trajectory(
            start=NormalizedPoint(0.1, 0.1),
            end=NormalizedPoint(0.2, 0.2),
            duration_ms=0,
            point_count=10,
        )
    with pytest.raises(TrajectoryError):
        build_polyline_trajectory(
            points=[NormalizedPoint(0.1, 0.1)],
            duration_ms=100,
            point_count=2,
        )


def test_swipe_executes_press_move_release_sequence() -> None:
    arm = FakeArm()
    sleeper = FakeSleeper()
    action = SwipeAction(
        mapper=build_mapper(),
        arm=arm,
        swipe_config=SwipeConfig(
            duration_ms=600,
            point_count=20,
            start_delay_ms=10,
            end_hold_ms=15,
        ),
        sleeper=sleeper,
    )

    result = action.execute_line(NormalizedPoint(0.5, 0.8), NormalizedPoint(0.5, 0.2))

    assert result.status is TouchActionStatus.SUCCEEDED
    assert [call[0] for call in arm.calls].count("move_xy") == 20
    assert ("pen_down", (7.0,)) in arm.calls
    assert arm.calls[-1] == ("pen_up", ())
    assert sleeper.durations[0] == 10
    assert sleeper.durations[-1] == 15
    assert sum(sleeper.durations[1:-1]) == 600


def test_all_trajectory_points_are_bounds_checked_before_pen_down() -> None:
    arm = FakeArm()
    action = SwipeAction(
        mapper=build_mapper(),
        arm=arm,
        swipe_config=SwipeConfig(duration_ms=100, point_count=3),
    )

    result = action.execute_line(NormalizedPoint(0.5, 0.5), NormalizedPoint(1.0, 1.0))

    assert result.status is TouchActionStatus.SUCCEEDED
    assert ("pen_down", (7.0,)) in arm.calls


def test_out_of_bounds_path_fails_before_any_move() -> None:
    arm = FakeArm()

    with pytest.raises(CoordinateError):
        NormalizedPoint(1.2, 0.5)

    assert arm.calls == []


def test_cancel_stops_remaining_points_and_releases_pen() -> None:
    arm = FakeArm()
    action = SwipeAction(
        mapper=build_mapper(),
        arm=arm,
        swipe_config=SwipeConfig(duration_ms=100, point_count=6),
        cancel_token=CancelAfter(2),
    )

    result = action.execute_line(NormalizedPoint(0.2, 0.2), NormalizedPoint(0.8, 0.8))

    assert result.status is TouchActionStatus.FAILED
    assert result.error == "swipe cancelled"
    assert ("pen_up", ()) in arm.calls
    assert [call[0] for call in arm.calls].count("move_xy") < 6


def test_exception_during_move_releases_pen() -> None:
    arm = FakeArm(fail_on_move_index=3)
    action = SwipeAction(
        mapper=build_mapper(),
        arm=arm,
        swipe_config=SwipeConfig(duration_ms=100, point_count=5),
    )

    result = action.execute_line(NormalizedPoint(0.2, 0.2), NormalizedPoint(0.8, 0.8))

    assert result.status is TouchActionStatus.FAILED
    assert ("pen_up", ()) in arm.calls
