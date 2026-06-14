"""4x4 local correction grid with bilinear interpolation."""

from __future__ import annotations

from dataclasses import dataclass

from ai_arm_control.calibration.error_metrics import CalibrationErrorSample
from ai_arm_control.coordinates.mapper import CoordinateMapper
from ai_arm_control.coordinates.models import ArmXY, CoordinateError, NormalizedPoint


class CorrectionGridError(ValueError):
    """Raised when a correction grid cannot be built or applied safely."""


@dataclass(frozen=True, slots=True)
class CorrectionVector:
    x_error: float
    y_error: float

    def to_dict(self) -> dict[str, float]:
        return {"x_error": self.x_error, "y_error": self.y_error}


@dataclass(frozen=True, slots=True)
class CorrectionGridPoint:
    point_id: str
    row: int
    column: int
    target: NormalizedPoint
    error: CorrectionVector

    def to_dict(self) -> dict[str, object]:
        return {
            "point_id": self.point_id,
            "row": self.row,
            "column": self.column,
            "target": {"x": self.target.x, "y": self.target.y},
            "error": self.error.to_dict(),
        }


@dataclass(frozen=True, slots=True)
class CorrectionGrid:
    points: tuple[CorrectionGridPoint, ...]
    rows: int = 4
    columns: int = 4

    @classmethod
    def from_samples(cls, samples: list[CalibrationErrorSample]) -> CorrectionGrid:
        if len(samples) != 16:
            raise CorrectionGridError("4x4 correction grid requires exactly 16 samples")
        points = tuple(
            CorrectionGridPoint(
                point_id=sample.point_id,
                row=sample.row,
                column=sample.column,
                target=sample.target,
                error=CorrectionVector(sample.x_error, sample.y_error),
            )
            for sample in samples
        )
        grid = cls(points=points)
        grid._validate()
        return grid

    @property
    def min_x(self) -> float:
        return min(point.target.x for point in self.points)

    @property
    def max_x(self) -> float:
        return max(point.target.x for point in self.points)

    @property
    def min_y(self) -> float:
        return min(point.target.y for point in self.points)

    @property
    def max_y(self) -> float:
        return max(point.target.y for point in self.points)

    def interpolate_error(self, point: NormalizedPoint, *, clamp: bool = False) -> CorrectionVector:
        x = _clamp(point.x, self.min_x, self.max_x) if clamp else point.x
        y = _clamp(point.y, self.min_y, self.max_y) if clamp else point.y
        if not clamp and not self._contains(x, y):
            raise CorrectionGridError("point is outside correction grid")

        left_column, right_column, tx = self._axis_bounds(x, axis="x")
        top_row, bottom_row, ty = self._axis_bounds(y, axis="y")
        q11 = self._point(top_row, left_column).error
        q21 = self._point(top_row, right_column).error
        q12 = self._point(bottom_row, left_column).error
        q22 = self._point(bottom_row, right_column).error
        top_x = _lerp(q11.x_error, q21.x_error, tx)
        bottom_x = _lerp(q12.x_error, q22.x_error, tx)
        top_y = _lerp(q11.y_error, q21.y_error, tx)
        bottom_y = _lerp(q12.y_error, q22.y_error, tx)
        return CorrectionVector(_lerp(top_x, bottom_x, ty), _lerp(top_y, bottom_y, ty))

    def apply(self, point: NormalizedPoint, *, clamp: bool = False) -> NormalizedPoint:
        error = self.interpolate_error(point, clamp=clamp)
        return NormalizedPoint(point.x - error.x_error, point.y - error.y_error)

    def map_to_arm(
        self,
        mapper: CoordinateMapper,
        point: NormalizedPoint,
        *,
        clamp: bool = False,
    ) -> ArmXY:
        try:
            corrected = self.apply(point, clamp=clamp)
        except CoordinateError as exc:
            raise CorrectionGridError(str(exc)) from exc
        return mapper.normalized_to_arm(corrected)

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": "2.0",
            "rows": self.rows,
            "columns": self.columns,
            "bounds": {
                "x_min": self.min_x,
                "x_max": self.max_x,
                "y_min": self.min_y,
                "y_max": self.max_y,
            },
            "points": [point.to_dict() for point in self.points],
        }

    def _validate(self) -> None:
        keys = {(point.row, point.column) for point in self.points}
        expected = {(row, column) for row in range(self.rows) for column in range(self.columns)}
        if keys != expected:
            raise CorrectionGridError("correction grid must contain every row and column once")
        for row in range(self.rows):
            xs = [self._point(row, column).target.x for column in range(self.columns)]
            if xs != sorted(xs):
                raise CorrectionGridError("grid x coordinates must increase left to right")
        for column in range(self.columns):
            ys = [self._point(row, column).target.y for row in range(self.rows)]
            if ys != sorted(ys):
                raise CorrectionGridError("grid y coordinates must increase top to bottom")

    def _contains(self, x: float, y: float) -> bool:
        return self.min_x <= x <= self.max_x and self.min_y <= y <= self.max_y

    def _point(self, row: int, column: int) -> CorrectionGridPoint:
        for point in self.points:
            if point.row == row and point.column == column:
                return point
        raise CorrectionGridError(f"missing correction grid point row={row} column={column}")

    def _axis_bounds(self, value: float, *, axis: str) -> tuple[int, int, float]:
        values = [
            self._point(0, index).target.x if axis == "x" else self._point(index, 0).target.y
            for index in range(4)
        ]
        for index in range(3):
            start = values[index]
            end = values[index + 1]
            if start <= value <= end:
                ratio = 0.0 if end == start else (value - start) / (end - start)
                return index, index + 1, ratio
        if value == values[-1]:
            return 2, 3, 1.0
        raise CorrectionGridError("point is outside correction grid")


def _lerp(start: float, end: float, ratio: float) -> float:
    return start + (end - start) * ratio


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))
