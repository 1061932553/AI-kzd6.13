"""Calibration report generation and version storage."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from ai_arm_control.calibration.correction_grid import CorrectionGrid
from ai_arm_control.calibration.error_metrics import (
    CalibrationErrorSample,
    CalibrationErrorSummary,
    summarize_errors,
)
from ai_arm_control.calibration.session import CalibrationSession
from ai_arm_control.calibration.touch_capture import utc_now_iso
from ai_arm_control.coordinates.models import NormalizedPoint


class CalibrationReportError(RuntimeError):
    """Raised when a calibration report cannot be generated or restored."""


@dataclass(frozen=True, slots=True)
class CalibrationReport:
    version: str
    device_id: str
    session_id: str
    generated_at: str
    before_summary: CalibrationErrorSummary
    after_summary: CalibrationErrorSummary
    correction_grid: CorrectionGrid
    samples: tuple[CalibrationErrorSample, ...]
    metadata: dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": "2.0",
            "version": self.version,
            "device_id": self.device_id,
            "session_id": self.session_id,
            "generated_at": self.generated_at,
            "before_summary": self.before_summary.to_dict(),
            "after_summary": self.after_summary.to_dict(),
            "correction_grid": self.correction_grid.to_dict(),
            "samples": [sample.to_dict() for sample in self.samples],
            "metadata": dict(self.metadata),
        }


def build_calibration_report(session: CalibrationSession) -> CalibrationReport:
    samples = tuple(CalibrationErrorSample.from_record(record) for record in session.records)
    if len(samples) != 16:
        raise CalibrationReportError("16 completed calibration records are required")
    grid = CorrectionGrid.from_samples(list(samples))
    before_summary = summarize_errors(list(samples))
    after_samples = [_build_after_sample(grid, sample) for sample in samples]
    after_summary = summarize_errors(after_samples)
    return CalibrationReport(
        version=f"{session.session_id}-v1",
        device_id=session.device_id,
        session_id=session.session_id,
        generated_at=utc_now_iso(),
        before_summary=before_summary,
        after_summary=after_summary,
        correction_grid=grid,
        samples=samples,
        metadata={"correction": "target_minus_interpolated_error"},
    )


class CalibrationReportStore:
    def __init__(self, directory: str | Path) -> None:
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)

    @property
    def current_path(self) -> Path:
        return self.directory / "current.json"

    def save(self, report: CalibrationReport) -> Path:
        version_path = self.directory / f"{report.version}.json"
        body = json.dumps(report.to_dict(), ensure_ascii=False, indent=2, sort_keys=True)
        version_path.write_text(body, encoding="utf-8")
        self.current_path.write_text(body, encoding="utf-8")
        return version_path

    def version_paths(self) -> list[Path]:
        return sorted(
            path
            for path in self.directory.glob("*.json")
            if path.name != "current.json"
        )

    def rollback_to_previous(self) -> Path:
        versions = self.version_paths()
        if len(versions) < 2:
            raise CalibrationReportError("at least two report versions are required to roll back")
        previous = versions[-2]
        self.current_path.write_text(previous.read_text(encoding="utf-8"), encoding="utf-8")
        return previous


def _distance(a: NormalizedPoint, b: NormalizedPoint) -> float:
    return ((a.x - b.x) ** 2 + (a.y - b.y) ** 2) ** 0.5


def _build_after_sample(
    grid: CorrectionGrid,
    sample: CalibrationErrorSample,
) -> CalibrationErrorSample:
    command = grid.apply(sample.target)
    error = grid.interpolate_error(sample.target)
    expected_actual = NormalizedPoint(command.x + error.x_error, command.y + error.y_error)
    return CalibrationErrorSample(
        point_id=sample.point_id,
        row=sample.row,
        column=sample.column,
        target=sample.target,
        actual=expected_actual,
        x_error=expected_actual.x - sample.target.x,
        y_error=expected_actual.y - sample.target.y,
        total_error=_distance(expected_actual, sample.target),
    )
