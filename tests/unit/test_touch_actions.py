from __future__ import annotations

import pytest

from ai_arm_control.actions import (
    TouchActionConfig,
    TouchActionStatus,
    TouchActionTiming,
    execute_long_press,
    execute_multi_tap,
    execute_tap,
)
from ai_arm_control.calibration.correction_grid import CorrectionGrid
from ai_arm_control.calibration.error_metrics import samples_from_session
from ai_arm_control.calibration.session import CalibrationSession
from ai_arm_control.coordinates import (
    Bounds2D,
    CoordinateError,
    CoordinateMapper,
    CoordinateMapperConfig,
    NormalizedPoint,
    ScreenROI,
)


class FakeArm:
    def __init__(self, *, fail_on: str | None = None) -> None:
        self.calls: list[tuple[str, tuple[float, ...]]] = []
        self.fail_on = fail_on

    def move_xy(self, x: float, y: float) -> object:
        self.calls.append(("move_xy", (x, y)))
        if self.fail_on == "move_xy":
            raise RuntimeError("move failed")
        return {"ok": True}

    def pen_down(self, z: float) -> object:
        self.calls.append(("pen_down", (z,)))
        if self.fail_on == "pen_down":
            raise RuntimeError("down failed")
        return {"ok": True}

    def pen_up(self) -> object:
        self.calls.append(("pen_up", ()))
        if self.fail_on == "pen_up":
            raise RuntimeError("up failed")
        return {"ok": True}


class FakeSleeper:
    def __init__(self) -> None:
        self.durations: list[int] = []

    def sleep_ms(self, duration_ms: int) -> None:
        self.durations.append(duration_ms)


def build_mapper() -> CoordinateMapper:
    return CoordinateMapper(
        CoordinateMapperConfig(
            screen_roi=ScreenROI.from_sequence([64, 32, 482, 911]),
            arm_bounds=Bounds2D(min_x=0, max_x=366, min_y=0, max_y=160),
        )
    )


def test_tap_uses_configurable_timing_and_returns_structured_result() -> None:
    arm = FakeArm()
    sleeper = FakeSleeper()
    config = TouchActionConfig(
        press_depth=7.5,
        timing=TouchActionTiming(xy_settle_ms=10, down_delay_ms=20, hold_ms=30, up_delay_ms=40),
    )

    result = execute_tap(
        NormalizedPoint(0.5, 0.5),
        mapper=build_mapper(),
        arm=arm,
        config=config,
        sleeper=sleeper,
    )

    assert result.status is TouchActionStatus.SUCCEEDED
    assert result.to_dict()["status"] == "succeeded"
    assert arm.calls == [
        ("move_xy", (183.0, 80.0)),
        ("pen_down", (7.5,)),
        ("pen_up", ()),
    ]
    assert sleeper.durations == [10, 20, 30, 40]
    assert [entry.step for entry in result.logs] == [
        "coordinate_mapping",
        "safety_check",
        "move_xy",
        "xy_settle",
        "pen_down",
        "down_delay",
        "hold",
        "pen_up",
        "up_delay",
    ]


def test_long_press_overrides_hold_duration() -> None:
    arm = FakeArm()
    sleeper = FakeSleeper()

    result = execute_long_press(
        NormalizedPoint(0.25, 0.75),
        duration_ms=1500,
        mapper=build_mapper(),
        arm=arm,
        sleeper=sleeper,
    )

    assert result.status is TouchActionStatus.SUCCEEDED
    assert 1500 in sleeper.durations
    assert result.action == "long_press"


def test_multi_tap_uses_count_interval_and_hold() -> None:
    arm = FakeArm()
    sleeper = FakeSleeper()

    result = execute_multi_tap(
        NormalizedPoint(0.4, 0.7),
        count=3,
        interval_ms=55,
        hold_ms=25,
        mapper=build_mapper(),
        arm=arm,
        sleeper=sleeper,
    )

    assert result.status is TouchActionStatus.SUCCEEDED
    assert [call[0] for call in arm.calls] == [
        "move_xy",
        "pen_down",
        "pen_up",
        "move_xy",
        "pen_down",
        "pen_up",
        "move_xy",
        "pen_down",
        "pen_up",
    ]
    assert sleeper.durations.count(25) == 3
    assert sleeper.durations.count(55) == 2


def test_out_of_bounds_coordinate_fails_before_arm_calls() -> None:
    arm = FakeArm()

    with pytest.raises(CoordinateError):
        NormalizedPoint(1.2, 0.5)

    assert arm.calls == []


def test_correction_grid_out_of_bounds_returns_failure_without_move_or_down() -> None:
    arm = FakeArm()
    grid = CorrectionGrid.from_samples(
        samples_from_session(CalibrationSession.load_json("tests/fixtures/calibration_session.json"))
    )

    result = execute_tap(
        NormalizedPoint(0.0, 0.5),
        mapper=build_mapper(),
        arm=arm,
        correction_grid=grid,
    )

    assert result.status is TouchActionStatus.FAILED
    assert [call[0] for call in arm.calls] == ["pen_up"]


def test_step_failure_attempts_pen_up_and_returns_failure() -> None:
    arm = FakeArm(fail_on="pen_down")

    result = execute_tap(NormalizedPoint(0.5, 0.5), mapper=build_mapper(), arm=arm)

    assert result.status is TouchActionStatus.FAILED
    assert ("pen_up", ()) in arm.calls
    assert result.error is not None
    assert any(entry.step == "pen_up_after_failure" for entry in result.logs)


def test_move_failure_does_not_continue_to_pen_down_but_still_releases() -> None:
    arm = FakeArm(fail_on="move_xy")

    result = execute_tap(NormalizedPoint(0.5, 0.5), mapper=build_mapper(), arm=arm)

    assert result.status is TouchActionStatus.FAILED
    assert [call[0] for call in arm.calls] == ["move_xy", "pen_up"]
