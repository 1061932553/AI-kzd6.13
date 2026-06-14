"""Error metrics for completed calibration samples."""

from __future__ import annotations

from dataclasses import dataclass
from math import hypot

from ai_arm_control.calibration.session import CalibrationPointRecord, CalibrationSession
from ai_arm_control.coordinates.models import NormalizedPoint


class CalibrationMetricsError(ValueError):
    """Raised when calibration metrics cannot be computed."""


@dataclass(frozen=True, slots=True)
class CalibrationErrorSample:
    point_id: str
    row: int
    column: int
    target: NormalizedPoint
    actual: NormalizedPoint
    x_error: float
    y_error: float
    total_error: float

    @classmethod
    def from_record(cls, record: CalibrationPointRecord) -> CalibrationErrorSample:
        if record.actual is None:
            raise CalibrationMetricsError(
                f"calibration point {record.point.point_id} has no actual touch"
            )
        x_error = record.actual.x - record.point.target.x
        y_error = record.actual.y - record.point.target.y
        return cls(
            point_id=record.point.point_id,
            row=record.point.row,
            column=record.point.column,
            target=record.point.target,
            actual=record.actual,
            x_error=x_error,
            y_error=y_error,
            total_error=hypot(x_error, y_error),
        )

    def corrected_actual(self) -> NormalizedPoint:
        return NormalizedPoint(self.actual.x - self.x_error, self.actual.y - self.y_error)

    def to_dict(self) -> dict[str, object]:
        return {
            "point_id": self.point_id,
            "row": self.row,
            "column": self.column,
            "target": {"x": self.target.x, "y": self.target.y},
            "actual": {"x": self.actual.x, "y": self.actual.y},
            "x_error": self.x_error,
            "y_error": self.y_error,
            "total_error": self.total_error,
        }


@dataclass(frozen=True, slots=True)
class CalibrationErrorSummary:
    average_error: float
    maximum_error: float
    p95_error: float
    sample_count: int

    def to_dict(self) -> dict[str, object]:
        return {
            "average_error": self.average_error,
            "maximum_error": self.maximum_error,
            "p95_error": self.p95_error,
            "sample_count": self.sample_count,
        }


def samples_from_session(session: CalibrationSession) -> list[CalibrationErrorSample]:
    samples = [CalibrationErrorSample.from_record(record) for record in session.records]
    if len(samples) != 16:
        raise CalibrationMetricsError("16 completed calibration samples are required")
    return samples


def summarize_errors(samples: list[CalibrationErrorSample]) -> CalibrationErrorSummary:
    if not samples:
        raise CalibrationMetricsError("at least one calibration sample is required")
    totals = sorted(sample.total_error for sample in samples)
    p95_index = max(0, int(len(totals) * 0.95 + 0.999999) - 1)
    return CalibrationErrorSummary(
        average_error=sum(totals) / len(totals),
        maximum_error=totals[-1],
        p95_error=totals[p95_index],
        sample_count=len(samples),
    )
