"""Generate deterministic 4x4 calibration targets."""

from __future__ import annotations

from dataclasses import dataclass

from ai_arm_control.coordinates.models import NormalizedPoint, require_finite_number


class CalibrationGridError(ValueError):
    """Raised when calibration grid input is invalid."""


@dataclass(frozen=True, slots=True)
class CalibrationGridPoint:
    point_id: str
    row: int
    column: int
    target: NormalizedPoint

    def to_dict(self) -> dict[str, object]:
        return {
            "point_id": self.point_id,
            "row": self.row,
            "column": self.column,
            "target": {"x": self.target.x, "y": self.target.y},
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> CalibrationGridPoint:
        target = data.get("target")
        if not isinstance(target, dict):
            raise CalibrationGridError("grid point target must be an object")
        return cls(
            point_id=str(data["point_id"]),
            row=int(data["row"]),
            column=int(data["column"]),
            target=NormalizedPoint(target["x"], target["y"]),
        )


def generate_4x4_grid(*, margin: float = 0.1) -> list[CalibrationGridPoint]:
    """Return 16 stable calibration points in row-major order.

    The default margin keeps points away from the physical edge while still
    covering all screen regions. Set margin to 0.0 to include exact corners.
    """

    margin = require_finite_number("margin", margin)
    if not 0.0 <= margin < 0.5:
        raise CalibrationGridError("margin must be in the range [0.0, 0.5)")

    step = (1.0 - margin * 2.0) / 3.0
    points: list[CalibrationGridPoint] = []
    for row in range(4):
        for column in range(4):
            index = row * 4 + column + 1
            points.append(
                CalibrationGridPoint(
                    point_id=f"P{index:02d}",
                    row=row,
                    column=column,
                    target=NormalizedPoint(margin + column * step, margin + row * step),
                )
            )
    return points
