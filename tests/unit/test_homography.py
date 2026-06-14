from __future__ import annotations

import json
from pathlib import Path

import pytest

from ai_arm_control.calibration import (
    HomographyCalibration,
    HomographyError,
    build_homography_calibration,
    select_manual_corners,
)
from ai_arm_control.coordinates import CameraPixel, ScreenPixel
from ai_arm_control.simulators.camera import CameraFrame
from ai_arm_control.vision.screen_rectifier import ScreenRectifier

SOURCE_CORNERS = [
    [1, 1],
    [5, 0],
    [6, 4],
    [0, 5],
]


def test_homography_maps_corners_to_rectangle() -> None:
    calibration = build_homography_calibration(
        SOURCE_CORNERS,
        output_width=4,
        output_height=3,
    )

    mapped = [calibration.camera_to_screen(CameraPixel(x, y)) for x, y in SOURCE_CORNERS]

    assert_point_close(mapped[0], ScreenPixel(0, 0))
    assert_point_close(mapped[1], ScreenPixel(3, 0))
    assert_point_close(mapped[2], ScreenPixel(3, 2))
    assert_point_close(mapped[3], ScreenPixel(0, 2))
    assert calibration.reprojection_error() <= 1e-6


def test_reverse_transform_round_trips_points() -> None:
    calibration = build_homography_calibration(
        SOURCE_CORNERS,
        output_width=8,
        output_height=6,
    )
    original = CameraPixel(2.5, 2.0)

    screen = calibration.camera_to_screen(original)
    round_trip = calibration.screen_to_camera(screen)

    assert_point_close(round_trip, original)


def test_wrong_corner_order_is_rejected() -> None:
    wrong_order = [
        [1, 1],
        [0, 5],
        [6, 4],
        [5, 0],
    ]

    with pytest.raises(HomographyError, match="clockwise|order"):
        select_manual_corners(wrong_order)


def test_degenerate_corners_are_rejected() -> None:
    with pytest.raises(HomographyError):
        build_homography_calibration(
            [[0, 0], [1, 1], [2, 2], [3, 3]],
            output_width=4,
            output_height=3,
        )


def test_matrix_can_be_saved_and_loaded(tmp_path: Path) -> None:
    path = tmp_path / "homography.json"
    calibration = build_homography_calibration(
        SOURCE_CORNERS,
        output_width=4,
        output_height=3,
    )

    calibration.save_json(path)
    loaded = HomographyCalibration.load_json(path)

    assert loaded.to_dict() == calibration.to_dict()


def test_screen_rectifier_outputs_rectangle() -> None:
    calibration = build_homography_calibration(
        SOURCE_CORNERS,
        output_width=4,
        output_height=3,
    )
    frame = CameraFrame(
        camera_name="synthetic",
        width=8,
        height=6,
        channels=3,
        pixel_format="RGB24",
        data=build_gradient_frame(8, 6),
        frame_index=1,
        captured_at="2026-06-14T00:00:00+00:00",
    )

    rectified = ScreenRectifier(calibration).rectify(frame)

    assert rectified.width == 4
    assert rectified.height == 3
    assert rectified.byte_length == 4 * 3 * 3
    assert rectified.metadata["rectified"] is True


def test_cli_fixture_shape_is_readable() -> None:
    fixture = Path("tests/fixtures/phone_tilted.jpg")

    payload = json.loads(fixture.read_text(encoding="utf-8"))

    assert payload["format"] == "ai-arm-control-rgb-json-v1"
    assert payload["corners"] == SOURCE_CORNERS


def build_gradient_frame(width: int, height: int) -> bytes:
    data = bytearray(width * height * 3)
    for y in range(height):
        for x in range(width):
            offset = (y * width + x) * 3
            data[offset : offset + 3] = bytes((x * 20 % 256, y * 20 % 256, 128))
    return bytes(data)


def assert_point_close(actual: object, expected: object) -> None:
    assert actual.x == pytest.approx(expected.x, abs=1e-6)
    assert actual.y == pytest.approx(expected.y, abs=1e-6)
