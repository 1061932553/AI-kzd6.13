from __future__ import annotations

from pathlib import Path

from ai_arm_control.actions import StaticFrameProvider, TapImageConfig, execute_tap_image
from ai_arm_control.actions.result import TouchActionStatus
from ai_arm_control.coordinates import Bounds2D, CoordinateMapper, CoordinateMapperConfig, ScreenROI
from ai_arm_control.vision.template_matcher import load_rgb_frame, load_template_image


class FakeArm:
    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple[float, ...]]] = []

    def move_xy(self, x: float, y: float) -> object:
        self.calls.append(("move_xy", (x, y)))
        return {"ok": True}

    def pen_down(self, z: float) -> object:
        self.calls.append(("pen_down", (z,)))
        return {"ok": True}

    def pen_up(self) -> object:
        self.calls.append(("pen_up", ()))
        return {"ok": True}


class NoDelaySleeper:
    def sleep_ms(self, duration_ms: int) -> None:
        return None


def mapper() -> CoordinateMapper:
    return CoordinateMapper(
        CoordinateMapperConfig(
            screen_roi=ScreenROI.from_sequence([0, 0, 24, 18]),
            arm_bounds=Bounds2D(0, 240, 0, 180),
        )
    )


def test_tap_image_finds_target_and_uses_unified_tap() -> None:
    frame = load_rgb_frame("tests/fixtures/screen.png")
    template = load_template_image("tests/fixtures/confirm.png")
    arm = FakeArm()

    result = execute_tap_image(
        frame_provider=StaticFrameProvider(frame),
        template=template,
        mapper=mapper(),
        arm=arm,
        config=TapImageConfig(confidence=0.99),
        sleeper=NoDelaySleeper(),
    )

    assert result.status is TouchActionStatus.SUCCEEDED
    assert arm.calls == [
        ("move_xy", (120.0, 95.0)),
        ("pen_down", (7.0,)),
        ("pen_up", ()),
    ]


def test_tap_image_not_found_does_not_click_and_saves_screenshot(tmp_path: Path) -> None:
    frame = load_rgb_frame("tests/fixtures/screen.png")
    template = load_template_image("tests/fixtures/wrong.png")
    arm = FakeArm()

    result = execute_tap_image(
        frame_provider=StaticFrameProvider(frame),
        template=template,
        mapper=mapper(),
        arm=arm,
        config=TapImageConfig(confidence=0.99, retry=1, failure_screenshot_dir=tmp_path),
        sleeper=NoDelaySleeper(),
    )

    assert result.status is TouchActionStatus.FAILED
    assert result.error == "template not found"
    assert arm.calls == []
    screenshots = list(tmp_path.glob("tap_image_failed_*.ppm"))
    assert len(screenshots) == 1
