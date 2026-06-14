"""Manual corner selection data helpers."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from ai_arm_control.calibration.homography import (
    HomographyError,
    Point2D,
    parse_corners,
    validate_corner_order,
)
from ai_arm_control.models.types import JsonObject


@dataclass(frozen=True, slots=True)
class CornerSelection:
    corners: tuple[Point2D, Point2D, Point2D, Point2D]

    def __post_init__(self) -> None:
        validate_corner_order(self.corners)

    def to_dict(self) -> JsonObject:
        return {"corners": [corner.to_list() for corner in self.corners]}

    @classmethod
    def from_dict(cls, data: object) -> CornerSelection:
        if not isinstance(data, dict):
            raise HomographyError("corner selection expects a mapping")
        return cls(parse_corners(data["corners"]))

    def save_json(self, path: str | Path) -> None:
        Path(path).write_text(
            json.dumps(self.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    @classmethod
    def load_json(cls, path: str | Path) -> CornerSelection:
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))


def select_manual_corners(corners: object) -> CornerSelection:
    return CornerSelection(parse_corners(corners))
