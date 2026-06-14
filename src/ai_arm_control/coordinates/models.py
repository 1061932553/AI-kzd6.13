"""Pure coordinate data models."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite


class CoordinateError(ValueError):
    """Raised when coordinate input is invalid or outside configured bounds."""


def require_finite_number(name: str, value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise CoordinateError(f"{name} must be a finite number")
    number = float(value)
    if not isfinite(number):
        raise CoordinateError(f"{name} must be a finite number")
    return number


@dataclass(frozen=True, slots=True)
class NormalizedPoint:
    x: float
    y: float

    def __post_init__(self) -> None:
        x = require_finite_number("normalized.x", self.x)
        y = require_finite_number("normalized.y", self.y)
        if not 0.0 <= x <= 1.0:
            raise CoordinateError("normalized.x must be between 0.0 and 1.0")
        if not 0.0 <= y <= 1.0:
            raise CoordinateError("normalized.y must be between 0.0 and 1.0")
        object.__setattr__(self, "x", x)
        object.__setattr__(self, "y", y)


@dataclass(frozen=True, slots=True)
class CameraPixel:
    x: float
    y: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "x", require_finite_number("camera.x", self.x))
        object.__setattr__(self, "y", require_finite_number("camera.y", self.y))


@dataclass(frozen=True, slots=True)
class ScreenPixel:
    x: float
    y: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "x", require_finite_number("screen.x", self.x))
        object.__setattr__(self, "y", require_finite_number("screen.y", self.y))


@dataclass(frozen=True, slots=True)
class ArmXY:
    x: float
    y: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "x", require_finite_number("arm.x", self.x))
        object.__setattr__(self, "y", require_finite_number("arm.y", self.y))


@dataclass(frozen=True, slots=True)
class ScreenROI:
    left: float
    top: float
    right: float
    bottom: float

    def __post_init__(self) -> None:
        left = require_finite_number("screen_roi.left", self.left)
        top = require_finite_number("screen_roi.top", self.top)
        right = require_finite_number("screen_roi.right", self.right)
        bottom = require_finite_number("screen_roi.bottom", self.bottom)
        if left >= right:
            raise CoordinateError("screen_roi.left must be less than right")
        if top >= bottom:
            raise CoordinateError("screen_roi.top must be less than bottom")
        object.__setattr__(self, "left", left)
        object.__setattr__(self, "top", top)
        object.__setattr__(self, "right", right)
        object.__setattr__(self, "bottom", bottom)

    @property
    def width(self) -> float:
        return self.right - self.left

    @property
    def height(self) -> float:
        return self.bottom - self.top

    @classmethod
    def from_sequence(cls, values: list[int | float] | tuple[int | float, ...]) -> ScreenROI:
        if len(values) != 4:
            raise CoordinateError("screen_roi expects 4 values")
        return cls(values[0], values[1], values[2], values[3])
