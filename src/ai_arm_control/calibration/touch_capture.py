"""Touch sample capture helpers for 16-point calibration."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Literal

from ai_arm_control.coordinates.models import NormalizedPoint

TouchSource = Literal["manual", "web"]


def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="milliseconds")


@dataclass(frozen=True, slots=True)
class TouchSample:
    point_id: str
    target: NormalizedPoint
    actual: NormalizedPoint
    source: TouchSource
    captured_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> dict[str, object]:
        return {
            "point_id": self.point_id,
            "target": {"x": self.target.x, "y": self.target.y},
            "actual": {"x": self.actual.x, "y": self.actual.y},
            "source": self.source,
            "captured_at": self.captured_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> TouchSample:
        target = data.get("target")
        actual = data.get("actual")
        if not isinstance(target, dict) or not isinstance(actual, dict):
            raise ValueError("touch sample target and actual must be objects")
        return cls(
            point_id=str(data["point_id"]),
            target=NormalizedPoint(target["x"], target["y"]),
            actual=NormalizedPoint(actual["x"], actual["y"]),
            source=_parse_source(data.get("source")),
            captured_at=str(data["captured_at"]),
        )


class ManualTouchCapture:
    """Validate manually entered touch coordinates."""

    def capture(self, *, point_id: str, target: NormalizedPoint, x: float, y: float) -> TouchSample:
        return TouchSample(
            point_id=point_id,
            target=target,
            actual=NormalizedPoint(x, y),
            source="manual",
        )


class TouchCaptureStore:
    """In-memory web touch capture store keyed by calibration point id."""

    def __init__(self) -> None:
        self._samples: dict[str, TouchSample] = {}

    def record_web_touch(
        self,
        *,
        point_id: str,
        target: NormalizedPoint,
        x: float,
        y: float,
    ) -> TouchSample:
        sample = TouchSample(
            point_id=point_id,
            target=target,
            actual=NormalizedPoint(x, y),
            source="web",
        )
        self._samples[point_id] = sample
        return sample

    def get(self, point_id: str) -> TouchSample | None:
        return self._samples.get(point_id)

    def clear(self) -> None:
        self._samples.clear()


def _parse_source(value: object) -> TouchSource:
    if value not in ("manual", "web"):
        raise ValueError("touch sample source must be manual or web")
    return value
