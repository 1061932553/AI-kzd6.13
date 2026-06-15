from __future__ import annotations

from pathlib import Path

from ai_arm_control.simulators.camera import CameraFrame
from ai_arm_control.vision.template_matcher import (
    TemplateImage,
    TemplateMatcher,
    load_rgb_frame,
    load_template_image,
)


def frame_from_pixels(width: int, height: int, pixels: list[tuple[int, int, int]]) -> CameraFrame:
    return CameraFrame(
        camera_name="unit",
        width=width,
        height=height,
        channels=3,
        pixel_format="RGB24",
        data=b"".join(bytes(pixel) for pixel in pixels),
        frame_index=1,
        captured_at="unit",
    )


def test_template_matcher_finds_exact_template_center() -> None:
    background = [(10, 10, 10)] * 100
    pixels = list(background)
    for y in range(3, 5):
        for x in range(4, 7):
            pixels[y * 10 + x] = (200, 20, 30)
    frame = frame_from_pixels(10, 10, pixels)
    template = TemplateImage(width=3, height=2, channels=3, data=bytes((200, 20, 30)) * 6)

    result = TemplateMatcher(confidence_threshold=0.99).match(frame, template)

    assert result.found
    assert result.match is not None
    assert result.match.x == 4
    assert result.match.y == 3
    assert result.match.center == (5.5, 4.0)
    assert result.match.confidence == 1.0


def test_template_matcher_uses_search_rect_and_best_confidence() -> None:
    pixels = [(0, 0, 0)] * 100
    for y in range(1, 3):
        for x in range(1, 3):
            pixels[y * 10 + x] = (100, 100, 100)
    for y in range(7, 9):
        for x in range(7, 9):
            pixels[y * 10 + x] = (200, 200, 200)
    frame = frame_from_pixels(10, 10, pixels)
    template = TemplateImage(width=2, height=2, channels=3, data=bytes((200, 200, 200)) * 4)

    result = TemplateMatcher(confidence_threshold=0.95).match(
        frame,
        template,
        search_rect=(5, 5, 10, 10),
    )

    assert result.found
    assert result.match is not None
    assert (result.match.x, result.match.y) == (7, 7)


def test_wrong_template_does_not_report_success() -> None:
    frame = frame_from_pixels(4, 4, [(10, 10, 10)] * 16)
    template = TemplateImage(width=2, height=2, channels=3, data=bytes((255, 0, 0)) * 4)

    result = TemplateMatcher(confidence_threshold=0.99).match(frame, template)

    assert not result.found
    assert result.match is None


def test_template_larger_than_frame_returns_not_found() -> None:
    frame = frame_from_pixels(2, 2, [(0, 0, 0)] * 4)
    template = TemplateImage(width=3, height=3, channels=3, data=bytes((0, 0, 0)) * 9)

    result = TemplateMatcher().match(frame, template)

    assert not result.found
    assert result.candidates_checked == 0


def test_ppm_fixture_loader_reads_named_png_files() -> None:
    frame = load_rgb_frame(Path("tests/fixtures/screen.png"))
    template = load_template_image(Path("tests/fixtures/confirm.png"))

    assert frame.width == 24
    assert frame.height == 18
    assert template.width == 4
    assert template.height == 3
