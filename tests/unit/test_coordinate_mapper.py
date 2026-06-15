from __future__ import annotations

import math

import pytest

from ai_arm_control.coordinates import (
    ArmXY,
    Bounds2D,
    CoordinateError,
    CoordinateMapper,
    CoordinateMapperConfig,
    NormalizedPoint,
    ScreenPixel,
    ScreenROI,
    validate_normalized,
)


def build_mapper(*, flip_x: bool = False, flip_y: bool = False) -> CoordinateMapper:
    return CoordinateMapper(
        CoordinateMapperConfig(
            screen_roi=ScreenROI.from_sequence([64, 32, 482, 911]),
            arm_bounds=Bounds2D(min_x=0, max_x=366, min_y=0, max_y=160),
            flip_x=flip_x,
            flip_y=flip_y,
        )
    )


@pytest.mark.parametrize(
    ("point", "expected_screen", "expected_arm"),
    [
        (NormalizedPoint(0.0, 0.0), ScreenPixel(64, 32), ArmXY(0, 0)),
        (NormalizedPoint(0.5, 0.5), ScreenPixel(273, 471.5), ArmXY(183, 80)),
        (NormalizedPoint(1.0, 1.0), ScreenPixel(482, 911), ArmXY(366, 160)),
    ],
)
def test_normalized_maps_to_left_top_center_and_right_bottom(
    point: NormalizedPoint,
    expected_screen: ScreenPixel,
    expected_arm: ArmXY,
) -> None:
    mapper = build_mapper()

    screen = mapper.normalized_to_screen(point)
    arm = mapper.normalized_to_arm(point)

    assert_close(screen.x, expected_screen.x)
    assert_close(screen.y, expected_screen.y)
    assert_close(arm.x, expected_arm.x)
    assert_close(arm.y, expected_arm.y)


def test_screen_roi_to_arm_mapping_reuses_normalized_pipeline() -> None:
    mapper = build_mapper()

    arm = mapper.screen_to_arm(ScreenPixel(273, 471.5))

    assert_close(arm.x, 183)
    assert_close(arm.y, 80)


def test_x_and_y_flip_are_supported() -> None:
    mapper = build_mapper(flip_x=True, flip_y=True)

    top_left_arm = mapper.normalized_to_arm(NormalizedPoint(0.0, 0.0))
    bottom_right_arm = mapper.normalized_to_arm(NormalizedPoint(1.0, 1.0))

    assert top_left_arm == ArmXY(366, 160)
    assert bottom_right_arm == ArmXY(0, 0)


def test_arm_to_normalized_round_trip_with_flip() -> None:
    mapper = build_mapper(flip_x=True, flip_y=False)
    point = NormalizedPoint(0.25, 0.75)

    arm = mapper.normalized_to_arm(point)
    round_trip = mapper.arm_to_normalized(arm)

    assert_close(round_trip.x, point.x)
    assert_close(round_trip.y, point.y)


@pytest.mark.parametrize(
    ("x", "y"),
    [
        (-0.01, 0.5),
        (0.5, -0.01),
        (1.01, 0.5),
        (0.5, 1.01),
    ],
)
def test_out_of_range_normalized_coordinates_are_rejected(x: float, y: float) -> None:
    with pytest.raises(CoordinateError):
        validate_normalized(x, y)


@pytest.mark.parametrize(
    ("x", "y"),
    [
        ("0.5", 0.5),
        (0.5, None),
        (math.nan, 0.5),
        (True, 0.5),
    ],
)
def test_non_numeric_normalized_coordinates_are_rejected(x: object, y: object) -> None:
    with pytest.raises(CoordinateError):
        validate_normalized(x, y)


def test_screen_pixel_outside_roi_is_rejected_before_arm_mapping() -> None:
    mapper = build_mapper()

    with pytest.raises(CoordinateError, match="screen pixel is outside screen_roi"):
        mapper.screen_to_arm(ScreenPixel(63, 32))


def test_arm_out_of_bounds_is_rejected() -> None:
    mapper = build_mapper()

    with pytest.raises(CoordinateError, match="arm coordinate is outside configured bounds"):
        mapper.arm_to_normalized(ArmXY(367, 80))


def test_roi_and_bounds_validation_rejects_invalid_ranges() -> None:
    with pytest.raises(CoordinateError):
        ScreenROI.from_sequence([64, 32, 64, 911])
    with pytest.raises(CoordinateError):
        Bounds2D(min_x=10, max_x=10, min_y=0, max_y=1)


def assert_close(actual: float, expected: float) -> None:
    assert actual == pytest.approx(expected, abs=1e-6)
