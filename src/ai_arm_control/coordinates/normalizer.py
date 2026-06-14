"""Normalized coordinate validation and conversion helpers."""

from __future__ import annotations

from ai_arm_control.coordinates.models import (
    CoordinateError,
    NormalizedPoint,
    ScreenPixel,
    ScreenROI,
)


def validate_normalized(x: object, y: object) -> NormalizedPoint:
    return NormalizedPoint(x, y)  # type: ignore[arg-type]


def normalize_screen_pixel(screen_pixel: ScreenPixel, roi: ScreenROI) -> NormalizedPoint:
    normalized_x = (screen_pixel.x - roi.left) / roi.width
    normalized_y = (screen_pixel.y - roi.top) / roi.height
    try:
        return NormalizedPoint(normalized_x, normalized_y)
    except CoordinateError as exc:
        raise CoordinateError("screen pixel is outside screen_roi") from exc
