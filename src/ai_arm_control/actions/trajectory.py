"""Swipe trajectory generation and validation."""

from __future__ import annotations

from dataclasses import dataclass

from ai_arm_control.actions.interpolation import (
    EasingMode,
    interpolate_scalar,
    interpolate_time_offsets,
)
from ai_arm_control.coordinates.mapper import CoordinateMapper
from ai_arm_control.coordinates.models import ArmXY, NormalizedPoint, require_finite_number


class TrajectoryError(ValueError):
    """Raised when a swipe trajectory cannot be generated safely."""


@dataclass(frozen=True, slots=True)
class TrajectoryPoint:
    index: int
    normalized: NormalizedPoint
    offset_ms: int

    def to_dict(self) -> dict[str, object]:
        return {
            "index": self.index,
            "normalized": {"x": self.normalized.x, "y": self.normalized.y},
            "offset_ms": self.offset_ms,
        }


@dataclass(frozen=True, slots=True)
class ArmTrajectoryPoint:
    index: int
    normalized: NormalizedPoint
    arm_xy: ArmXY
    offset_ms: int

    def to_dict(self) -> dict[str, object]:
        return {
            "index": self.index,
            "normalized": {"x": self.normalized.x, "y": self.normalized.y},
            "arm_xy": {"x": self.arm_xy.x, "y": self.arm_xy.y},
            "offset_ms": self.offset_ms,
        }


def build_linear_trajectory(
    *,
    start: NormalizedPoint,
    end: NormalizedPoint,
    duration_ms: int,
    point_count: int,
    easing: EasingMode = EasingMode.LINEAR,
) -> list[TrajectoryPoint]:
    if point_count < 2:
        raise TrajectoryError("point_count must be at least 2")
    if duration_ms <= 0:
        raise TrajectoryError("duration_ms must be positive")
    offsets = interpolate_time_offsets(duration_ms, point_count)
    points: list[TrajectoryPoint] = []
    for index, offset in enumerate(offsets):
        ratio = index / (point_count - 1)
        if index == 0:
            normalized = start
        elif index == point_count - 1:
            normalized = end
        else:
            normalized = NormalizedPoint(
                interpolate_scalar(start.x, end.x, ratio, easing=easing),
                interpolate_scalar(start.y, end.y, ratio, easing=easing),
            )
        points.append(
            TrajectoryPoint(
                index=index,
                normalized=normalized,
                offset_ms=offset,
            )
        )
    return points


def build_polyline_trajectory(
    *,
    points: list[NormalizedPoint],
    duration_ms: int,
    point_count: int,
    easing: EasingMode = EasingMode.LINEAR,
) -> list[TrajectoryPoint]:
    if len(points) < 2:
        raise TrajectoryError("polyline requires at least two points")
    if point_count < len(points):
        raise TrajectoryError("point_count must be at least the number of path points")
    if duration_ms <= 0:
        raise TrajectoryError("duration_ms must be positive")

    lengths = [
        _segment_length(points[index], points[index + 1])
        for index in range(len(points) - 1)
    ]
    total_length = sum(lengths)
    if total_length <= 0:
        raise TrajectoryError("polyline length must be positive")

    offsets = interpolate_time_offsets(duration_ms, point_count)
    trajectory: list[TrajectoryPoint] = []
    for index, offset in enumerate(offsets):
        progress = index / (point_count - 1)
        progress = _ease_for_polyline(progress, easing)
        if index == 0:
            normalized = points[0]
        elif index == point_count - 1:
            normalized = points[-1]
        else:
            normalized = _point_at_distance(points, lengths, total_length * progress)
        trajectory.append(TrajectoryPoint(index=index, normalized=normalized, offset_ms=offset))
    return trajectory


def map_trajectory_to_arm(
    trajectory: list[TrajectoryPoint],
    mapper: CoordinateMapper,
) -> list[ArmTrajectoryPoint]:
    return [
        ArmTrajectoryPoint(
            index=point.index,
            normalized=point.normalized,
            arm_xy=mapper.normalized_to_arm(point.normalized),
            offset_ms=point.offset_ms,
        )
        for point in trajectory
    ]


def validate_total_time(
    trajectory: list[TrajectoryPoint],
    duration_ms: int,
    *,
    tolerance_ms: int = 1,
) -> None:
    if not trajectory:
        raise TrajectoryError("trajectory cannot be empty")
    actual = trajectory[-1].offset_ms - trajectory[0].offset_ms
    if abs(actual - duration_ms) > tolerance_ms:
        raise TrajectoryError("trajectory total time exceeds tolerance")


def _segment_length(start: NormalizedPoint, end: NormalizedPoint) -> float:
    return ((end.x - start.x) ** 2 + (end.y - start.y) ** 2) ** 0.5


def _point_at_distance(
    points: list[NormalizedPoint],
    lengths: list[float],
    distance: float,
) -> NormalizedPoint:
    remaining = distance
    for index, length in enumerate(lengths):
        if remaining <= length or index == len(lengths) - 1:
            ratio = 0.0 if length == 0 else remaining / length
            return NormalizedPoint(
                points[index].x + (points[index + 1].x - points[index].x) * ratio,
                points[index].y + (points[index + 1].y - points[index].y) * ratio,
            )
        remaining -= length
    return points[-1]


def _ease_for_polyline(ratio: float, easing: EasingMode) -> float:
    eased = interpolate_scalar(0.0, 1.0, require_finite_number("ratio", ratio), easing=easing)
    return max(0.0, min(1.0, eased))
