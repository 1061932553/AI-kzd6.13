"""Offline RGB24 template matching."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ai_arm_control.simulators.camera import CameraFrame, crop_frame

JsonObject = dict[str, Any]


class TemplateMatcherError(ValueError):
    """Raised when image or matcher input is invalid."""


@dataclass(frozen=True, slots=True)
class TemplateImage:
    width: int
    height: int
    channels: int
    data: bytes

    def to_frame(self, *, camera_name: str = "template") -> CameraFrame:
        return CameraFrame(
            camera_name=camera_name,
            width=self.width,
            height=self.height,
            channels=self.channels,
            pixel_format="RGB24",
            data=self.data,
            frame_index=0,
            captured_at="template",
        )


@dataclass(frozen=True, slots=True)
class TemplateMatch:
    x: int
    y: int
    width: int
    height: int
    confidence: float
    search_rect: tuple[int, int, int, int]

    @property
    def center(self) -> tuple[float, float]:
        return (self.x + self.width / 2, self.y + self.height / 2)

    def to_dict(self) -> JsonObject:
        center_x, center_y = self.center
        return {
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "center": [center_x, center_y],
            "confidence": self.confidence,
            "search_rect": list(self.search_rect),
        }


@dataclass(frozen=True, slots=True)
class TemplateMatchResult:
    found: bool
    match: TemplateMatch | None = None
    confidence_threshold: float = 0.85
    candidates_checked: int = 0

    def to_dict(self) -> JsonObject:
        return {
            "found": self.found,
            "match": self.match.to_dict() if self.match else None,
            "confidence_threshold": self.confidence_threshold,
            "candidates_checked": self.candidates_checked,
        }


class TemplateMatcher:
    def __init__(self, *, confidence_threshold: float = 0.85) -> None:
        if not 0.0 <= confidence_threshold <= 1.0:
            raise TemplateMatcherError("confidence_threshold must be between 0.0 and 1.0")
        self.confidence_threshold = confidence_threshold

    def match(
        self,
        frame: CameraFrame,
        template: TemplateImage | CameraFrame,
        *,
        search_rect: tuple[int, int, int, int] | None = None,
    ) -> TemplateMatchResult:
        _validate_rgb24(frame, "frame")
        template_frame = template.to_frame() if isinstance(template, TemplateImage) else template
        _validate_rgb24(template_frame, "template")
        if template_frame.width > frame.width or template_frame.height > frame.height:
            return TemplateMatchResult(
                found=False,
                confidence_threshold=self.confidence_threshold,
            )

        rect = search_rect or (0, 0, frame.width, frame.height)
        search = crop_frame(frame, rect)
        if template_frame.width > search.width or template_frame.height > search.height:
            return TemplateMatchResult(
                found=False,
                confidence_threshold=self.confidence_threshold,
            )

        best: TemplateMatch | None = None
        checked = 0
        max_y = search.height - template_frame.height
        max_x = search.width - template_frame.width
        for y in range(max_y + 1):
            for x in range(max_x + 1):
                checked += 1
                confidence = _confidence(search, template_frame, x, y)
                if best is None or confidence > best.confidence:
                    best = TemplateMatch(
                        x=rect[0] + x,
                        y=rect[1] + y,
                        width=template_frame.width,
                        height=template_frame.height,
                        confidence=confidence,
                        search_rect=rect,
                    )
        found = best is not None and best.confidence >= self.confidence_threshold
        return TemplateMatchResult(
            found=found,
            match=best if found else None,
            confidence_threshold=self.confidence_threshold,
            candidates_checked=checked,
        )


def load_template_image(path: str | Path) -> TemplateImage:
    path = Path(path)
    data = path.read_bytes()
    return _read_ppm(data)


def load_rgb_frame(path: str | Path, *, camera_name: str | None = None) -> CameraFrame:
    image = load_template_image(path)
    return CameraFrame(
        camera_name=camera_name or Path(path).name,
        width=image.width,
        height=image.height,
        channels=image.channels,
        pixel_format="RGB24",
        data=image.data,
        frame_index=1,
        captured_at="fixture",
    )


def _confidence(frame: CameraFrame, template: CameraFrame, start_x: int, start_y: int) -> float:
    total_diff = 0
    channels = frame.channels
    max_diff = template.width * template.height * channels * 255
    for y in range(template.height):
        frame_offset = ((start_y + y) * frame.width + start_x) * channels
        template_offset = y * template.width * channels
        frame_row = frame.data[frame_offset : frame_offset + template.width * channels]
        template_row = template.data[template_offset : template_offset + template.width * channels]
        total_diff += sum(abs(a - b) for a, b in zip(frame_row, template_row, strict=True))
    return 1.0 - (total_diff / max_diff)


def _validate_rgb24(frame: CameraFrame, name: str) -> None:
    if frame.channels != 3 or frame.pixel_format != "RGB24":
        raise TemplateMatcherError(f"{name} must be RGB24")
    if len(frame.data) != frame.width * frame.height * frame.channels:
        raise TemplateMatcherError(f"{name} data length does not match dimensions")


def _read_ppm(data: bytes) -> TemplateImage:
    tokens, offset = _ppm_tokens(data, 4)
    if tokens[0] != b"P6":
        raise TemplateMatcherError("only binary PPM P6 images are supported")
    width = int(tokens[1])
    height = int(tokens[2])
    max_value = int(tokens[3])
    if width <= 0 or height <= 0 or max_value != 255:
        raise TemplateMatcherError("invalid PPM dimensions or max value")
    payload = data[offset:]
    expected = width * height * 3
    if len(payload) != expected:
        raise TemplateMatcherError("PPM payload length does not match dimensions")
    return TemplateImage(width=width, height=height, channels=3, data=payload)


def _ppm_tokens(data: bytes, count: int) -> tuple[list[bytes], int]:
    tokens: list[bytes] = []
    index = 0
    while index < len(data) and len(tokens) < count:
        while index < len(data) and data[index] in b" \t\r\n":
            index += 1
        if index < len(data) and data[index] == ord("#"):
            while index < len(data) and data[index] not in b"\r\n":
                index += 1
            continue
        start = index
        while index < len(data) and data[index] not in b" \t\r\n":
            index += 1
        if start != index:
            tokens.append(data[start:index])
    while index < len(data) and data[index] in b" \t\r\n":
        index += 1
    if len(tokens) != count:
        raise TemplateMatcherError("invalid PPM header")
    return tokens, index
