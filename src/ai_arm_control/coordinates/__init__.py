"""Coordinate models and mapping helpers."""

from ai_arm_control.coordinates.bounds import Bounds2D, ensure_in_bounds
from ai_arm_control.coordinates.mapper import CoordinateMapper, CoordinateMapperConfig
from ai_arm_control.coordinates.models import (
    ArmXY,
    CameraPixel,
    CoordinateError,
    NormalizedPoint,
    ScreenPixel,
    ScreenROI,
)
from ai_arm_control.coordinates.normalizer import normalize_screen_pixel, validate_normalized

__all__ = [
    "ArmXY",
    "Bounds2D",
    "CameraPixel",
    "CoordinateError",
    "CoordinateMapper",
    "CoordinateMapperConfig",
    "NormalizedPoint",
    "ScreenPixel",
    "ScreenROI",
    "ensure_in_bounds",
    "normalize_screen_pixel",
    "validate_normalized",
]
