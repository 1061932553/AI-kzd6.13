"""Interpolation helpers for swipe trajectories."""

from __future__ import annotations

from enum import StrEnum


class EasingMode(StrEnum):
    LINEAR = "linear"
    EASE_IN_OUT = "ease_in_out"


def interpolate_scalar(
    start: float,
    end: float,
    ratio: float,
    *,
    easing: EasingMode = EasingMode.LINEAR,
) -> float:
    if not 0.0 <= ratio <= 1.0:
        raise ValueError("ratio must be between 0.0 and 1.0")
    eased = _ease(ratio, easing)
    return start + (end - start) * eased


def interpolate_time_offsets(duration_ms: int, point_count: int) -> list[int]:
    if duration_ms < 0:
        raise ValueError("duration_ms cannot be negative")
    if point_count < 2:
        raise ValueError("point_count must be at least 2")
    if point_count == 2:
        return [0, duration_ms]
    return [round(duration_ms * index / (point_count - 1)) for index in range(point_count)]


def _ease(ratio: float, easing: EasingMode) -> float:
    if easing is EasingMode.LINEAR:
        return ratio
    if easing is EasingMode.EASE_IN_OUT:
        return ratio * ratio * (3.0 - 2.0 * ratio)
    raise ValueError(f"unsupported easing mode: {easing}")
