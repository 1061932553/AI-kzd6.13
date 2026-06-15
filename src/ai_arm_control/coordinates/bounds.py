"""Bounds helpers for pure coordinate mapping."""

from __future__ import annotations

from dataclasses import dataclass

from ai_arm_control.coordinates.models import CoordinateError, require_finite_number


@dataclass(frozen=True, slots=True)
class Bounds2D:
    min_x: float
    max_x: float
    min_y: float
    max_y: float

    def __post_init__(self) -> None:
        min_x = require_finite_number("bounds.min_x", self.min_x)
        max_x = require_finite_number("bounds.max_x", self.max_x)
        min_y = require_finite_number("bounds.min_y", self.min_y)
        max_y = require_finite_number("bounds.max_y", self.max_y)
        if min_x >= max_x:
            raise CoordinateError("bounds.min_x must be less than max_x")
        if min_y >= max_y:
            raise CoordinateError("bounds.min_y must be less than max_y")
        object.__setattr__(self, "min_x", min_x)
        object.__setattr__(self, "max_x", max_x)
        object.__setattr__(self, "min_y", min_y)
        object.__setattr__(self, "max_y", max_y)

    @property
    def width(self) -> float:
        return self.max_x - self.min_x

    @property
    def height(self) -> float:
        return self.max_y - self.min_y

    def contains(self, x: float, y: float, *, tolerance: float = 1e-9) -> bool:
        return (
            self.min_x - tolerance <= x <= self.max_x + tolerance
            and self.min_y - tolerance <= y <= self.max_y + tolerance
        )


def ensure_in_bounds(x: float, y: float, bounds: Bounds2D, *, label: str) -> None:
    if not bounds.contains(x, y):
        raise CoordinateError(f"{label} is outside configured bounds")
