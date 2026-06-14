"""Homography calibration primitives.

This module uses pure Python linear algebra. It does not depend on OpenCV and
does not access cameras, COM ports, services, or hardware.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from ai_arm_control.coordinates import CameraPixel, ScreenPixel
from ai_arm_control.models.types import JsonObject

MatrixRows = tuple[
    tuple[float, float, float],
    tuple[float, float, float],
    tuple[float, float, float],
]


class HomographyError(ValueError):
    """Raised when homography data is invalid or degenerate."""


@dataclass(frozen=True, slots=True)
class Point2D:
    x: float
    y: float

    def to_list(self) -> list[float]:
        return [self.x, self.y]

    @classmethod
    def from_sequence(cls, value: object, *, name: str = "point") -> Point2D:
        if not isinstance(value, list | tuple) or len(value) != 2:
            raise HomographyError(f"{name} expects [x, y]")
        try:
            return cls(float(value[0]), float(value[1]))
        except (TypeError, ValueError) as exc:
            raise HomographyError(f"{name} expects numeric values") from exc


@dataclass(frozen=True, slots=True)
class HomographyMatrix:
    values: MatrixRows

    def apply(self, point: Point2D) -> Point2D:
        x, y = point.x, point.y
        rows = self.values
        denominator = rows[2][0] * x + rows[2][1] * y + rows[2][2]
        if abs(denominator) < 1e-12:
            raise HomographyError("homography transform denominator is too close to zero")
        return Point2D(
            (rows[0][0] * x + rows[0][1] * y + rows[0][2]) / denominator,
            (rows[1][0] * x + rows[1][1] * y + rows[1][2]) / denominator,
        )

    def inverse(self) -> HomographyMatrix:
        return HomographyMatrix(_invert_3x3(self.values))

    def to_list(self) -> list[list[float]]:
        return [list(row) for row in self.values]

    @classmethod
    def from_list(cls, rows: object) -> HomographyMatrix:
        if not isinstance(rows, list) or len(rows) != 3:
            raise HomographyError("homography matrix expects 3 rows")
        parsed_rows: list[tuple[float, float, float]] = []
        for index, row in enumerate(rows):
            if not isinstance(row, list) or len(row) != 3:
                raise HomographyError(f"homography matrix row {index} expects 3 values")
            parsed_rows.append((float(row[0]), float(row[1]), float(row[2])))
        return cls((parsed_rows[0], parsed_rows[1], parsed_rows[2]))


@dataclass(frozen=True, slots=True)
class HomographyCalibration:
    source_corners: tuple[Point2D, Point2D, Point2D, Point2D]
    output_width: int
    output_height: int
    matrix: HomographyMatrix
    inverse_matrix: HomographyMatrix

    def camera_to_screen(self, point: CameraPixel | Point2D) -> ScreenPixel:
        point2d = point if isinstance(point, Point2D) else Point2D(point.x, point.y)
        mapped = self.matrix.apply(point2d)
        return ScreenPixel(mapped.x, mapped.y)

    def screen_to_camera(self, point: ScreenPixel | Point2D) -> CameraPixel:
        point2d = point if isinstance(point, Point2D) else Point2D(point.x, point.y)
        mapped = self.inverse_matrix.apply(point2d)
        return CameraPixel(mapped.x, mapped.y)

    def reprojection_error(self) -> float:
        destination = destination_corners(self.output_width, self.output_height)
        errors = []
        for source, expected in zip(self.source_corners, destination, strict=True):
            mapped = self.matrix.apply(source)
            errors.append(((mapped.x - expected.x) ** 2 + (mapped.y - expected.y) ** 2) ** 0.5)
        return max(errors)

    def to_dict(self) -> JsonObject:
        return {
            "schema_version": "2.0",
            "source_corners": [corner.to_list() for corner in self.source_corners],
            "output_size": [self.output_width, self.output_height],
            "matrix": self.matrix.to_list(),
            "inverse_matrix": self.inverse_matrix.to_list(),
            "maximum_reprojection_error": self.reprojection_error(),
        }

    @classmethod
    def from_dict(cls, data: object) -> HomographyCalibration:
        if not isinstance(data, dict):
            raise HomographyError("homography calibration expects a mapping")
        source = parse_corners(data["source_corners"])
        output_size = data["output_size"]
        if not isinstance(output_size, list) or len(output_size) != 2:
            raise HomographyError("output_size expects [width, height]")
        matrix = HomographyMatrix.from_list(data["matrix"])
        inverse_matrix = HomographyMatrix.from_list(data["inverse_matrix"])
        return cls(
            source_corners=source,
            output_width=int(output_size[0]),
            output_height=int(output_size[1]),
            matrix=matrix,
            inverse_matrix=inverse_matrix,
        )

    def save_json(self, path: str | Path) -> None:
        Path(path).write_text(
            json.dumps(self.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    @classmethod
    def load_json(cls, path: str | Path) -> HomographyCalibration:
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))


def build_homography_calibration(
    source_corners: object,
    *,
    output_width: int,
    output_height: int,
) -> HomographyCalibration:
    corners = parse_corners(source_corners)
    validate_corner_order(corners)
    destination = destination_corners(output_width, output_height)
    matrix = solve_homography(corners, destination)
    inverse = matrix.inverse()
    calibration = HomographyCalibration(
        source_corners=corners,
        output_width=output_width,
        output_height=output_height,
        matrix=matrix,
        inverse_matrix=inverse,
    )
    if calibration.reprojection_error() > 1e-6:
        raise HomographyError("homography reprojection error exceeds tolerance")
    return calibration


def parse_corners(value: object) -> tuple[Point2D, Point2D, Point2D, Point2D]:
    if not isinstance(value, list | tuple) or len(value) != 4:
        raise HomographyError("four corners are required")
    corners = tuple(
        Point2D.from_sequence(item, name=f"corner[{index}]") for index, item in enumerate(value)
    )
    return corners  # type: ignore[return-value]


def validate_corner_order(corners: tuple[Point2D, Point2D, Point2D, Point2D]) -> None:
    top_left, top_right, bottom_right, bottom_left = corners
    if _polygon_area(corners) <= 0:
        raise HomographyError(
            "corners must be ordered clockwise: top-left, top-right, "
            "bottom-right, bottom-left"
        )
    if top_left.x >= top_right.x or bottom_left.x >= bottom_right.x:
        raise HomographyError("corner order is invalid: left corners must precede right corners")
    if top_left.y >= bottom_left.y or top_right.y >= bottom_right.y:
        raise HomographyError("corner order is invalid: top corners must precede bottom corners")
    if abs(_polygon_area(corners)) < 1e-6:
        raise HomographyError("corners form a degenerate quadrilateral")


def destination_corners(width: int, height: int) -> tuple[Point2D, Point2D, Point2D, Point2D]:
    if width <= 1 or height <= 1:
        raise HomographyError("output width and height must be greater than 1")
    return (
        Point2D(0.0, 0.0),
        Point2D(float(width - 1), 0.0),
        Point2D(float(width - 1), float(height - 1)),
        Point2D(0.0, float(height - 1)),
    )


def solve_homography(
    source: tuple[Point2D, Point2D, Point2D, Point2D],
    destination: tuple[Point2D, Point2D, Point2D, Point2D],
) -> HomographyMatrix:
    rows: list[list[float]] = []
    rhs: list[float] = []
    for src, dst in zip(source, destination, strict=True):
        x, y, u, v = src.x, src.y, dst.x, dst.y
        rows.append([x, y, 1.0, 0.0, 0.0, 0.0, -u * x, -u * y])
        rhs.append(u)
        rows.append([0.0, 0.0, 0.0, x, y, 1.0, -v * x, -v * y])
        rhs.append(v)
    solution = _solve_linear_system(rows, rhs)
    return HomographyMatrix(
        (
            (solution[0], solution[1], solution[2]),
            (solution[3], solution[4], solution[5]),
            (solution[6], solution[7], 1.0),
        )
    )


def _solve_linear_system(matrix: list[list[float]], vector: list[float]) -> list[float]:
    size = len(vector)
    augmented = [row[:] + [value] for row, value in zip(matrix, vector, strict=True)]
    for column in range(size):
        pivot = max(range(column, size), key=lambda row: abs(augmented[row][column]))
        if abs(augmented[pivot][column]) < 1e-12:
            raise HomographyError("homography source points are degenerate")
        augmented[column], augmented[pivot] = augmented[pivot], augmented[column]
        pivot_value = augmented[column][column]
        augmented[column] = [value / pivot_value for value in augmented[column]]
        for row_index in range(size):
            if row_index == column:
                continue
            factor = augmented[row_index][column]
            augmented[row_index] = [
                value - factor * pivot_value
                for value, pivot_value in zip(augmented[row_index], augmented[column], strict=True)
            ]
    return [row[-1] for row in augmented]


def _invert_3x3(matrix: MatrixRows) -> MatrixRows:
    a, b, c = matrix[0]
    d, e, f = matrix[1]
    g, h, i = matrix[2]
    determinant = (
        a * (e * i - f * h)
        - b * (d * i - f * g)
        + c * (d * h - e * g)
    )
    if abs(determinant) < 1e-12:
        raise HomographyError("homography matrix is not invertible")
    inv = (
        (
            (e * i - f * h) / determinant,
            (c * h - b * i) / determinant,
            (b * f - c * e) / determinant,
        ),
        (
            (f * g - d * i) / determinant,
            (a * i - c * g) / determinant,
            (c * d - a * f) / determinant,
        ),
        (
            (d * h - e * g) / determinant,
            (b * g - a * h) / determinant,
            (a * e - b * d) / determinant,
        ),
    )
    return inv


def _polygon_area(corners: tuple[Point2D, Point2D, Point2D, Point2D]) -> float:
    total = 0.0
    for index, current in enumerate(corners):
        nxt = corners[(index + 1) % len(corners)]
        total += current.x * nxt.y - nxt.x * current.y
    return total / 2.0
