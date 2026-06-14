from __future__ import annotations

import json

import pytest

from ai_arm_control.calibration.correction_grid import CorrectionGrid, CorrectionGridError
from ai_arm_control.calibration.error_metrics import samples_from_session, summarize_errors
from ai_arm_control.calibration.report import CalibrationReportStore, build_calibration_report
from ai_arm_control.calibration.session import CalibrationSession
from ai_arm_control.coordinates import (
    Bounds2D,
    CoordinateMapper,
    CoordinateMapperConfig,
    NormalizedPoint,
    ScreenROI,
)


def load_fixed_session() -> CalibrationSession:
    return CalibrationSession.load_json("tests/fixtures/calibration_session.json")


def build_grid() -> CorrectionGrid:
    return CorrectionGrid.from_samples(samples_from_session(load_fixed_session()))


def test_error_metrics_are_computed_from_actual_minus_target() -> None:
    samples = samples_from_session(load_fixed_session())
    first = samples[0]
    summary = summarize_errors(samples)

    assert first.x_error == pytest.approx(0.011)
    assert first.y_error == pytest.approx(-0.019)
    assert first.total_error == pytest.approx((0.011**2 + 0.019**2) ** 0.5)
    assert summary.sample_count == 16
    assert summary.average_error > 0
    assert summary.maximum_error >= summary.average_error
    assert summary.p95_error == pytest.approx(summary.maximum_error)


def test_correction_grid_has_16_serializable_points() -> None:
    grid = build_grid()
    data = grid.to_dict()

    assert len(grid.points) == 16
    assert data["rows"] == 4
    assert data["columns"] == 4
    assert len(data["points"]) == 16


def test_bilinear_interpolation_returns_known_center_error() -> None:
    grid = build_grid()

    error = grid.interpolate_error(NormalizedPoint(0.5, 0.5))

    assert error.x_error == pytest.approx(0.0125, abs=1e-10)
    assert error.y_error == pytest.approx(-0.0165, abs=1e-10)


def test_apply_subtracts_interpolated_error() -> None:
    grid = build_grid()

    corrected = grid.apply(NormalizedPoint(0.5, 0.5))

    assert corrected.x == pytest.approx(0.4875)
    assert corrected.y == pytest.approx(0.5165)


def test_grid_outside_point_is_rejected_or_explicitly_clamped() -> None:
    grid = build_grid()

    with pytest.raises(CorrectionGridError, match="outside correction grid"):
        grid.interpolate_error(NormalizedPoint(0.05, 0.5))

    clamped = grid.interpolate_error(NormalizedPoint(0.05, 0.5), clamp=True)
    assert clamped.x_error == pytest.approx(0.011)


def test_compensated_mapping_reuses_coordinate_mapper() -> None:
    grid = build_grid()
    mapper = CoordinateMapper(
        CoordinateMapperConfig(
            screen_roi=ScreenROI.from_sequence([64, 32, 482, 911]),
            arm_bounds=Bounds2D(min_x=0, max_x=366, min_y=0, max_y=160),
        )
    )

    arm = grid.map_to_arm(mapper, NormalizedPoint(0.5, 0.5))

    assert arm.x == pytest.approx(178.425)
    assert arm.y == pytest.approx(82.64)


def test_report_contains_before_after_summaries_and_grid() -> None:
    report = build_calibration_report(load_fixed_session())

    assert report.before_summary.average_error > 0
    assert report.after_summary.average_error == pytest.approx(0.0)
    assert report.before_summary.maximum_error > report.after_summary.maximum_error
    assert report.before_summary.p95_error > report.after_summary.p95_error
    assert len(report.correction_grid.points) == 16
    assert report.version == "cal-fixed-p2-06-v1"


def test_report_store_saves_versions_and_rolls_back(tmp_path) -> None:  # noqa: ANN001
    store = CalibrationReportStore(tmp_path)
    report = build_calibration_report(load_fixed_session())
    first_path = store.save(report)
    second = build_calibration_report(load_fixed_session())
    second = type(second)(
        version="cal-fixed-p2-06-v2",
        device_id=second.device_id,
        session_id=second.session_id,
        generated_at=second.generated_at,
        before_summary=second.before_summary,
        after_summary=second.after_summary,
        correction_grid=second.correction_grid,
        samples=second.samples,
        metadata=second.metadata,
    )
    store.save(second)

    rollback_path = store.rollback_to_previous()
    current = json.loads(store.current_path.read_text(encoding="utf-8"))

    assert rollback_path == first_path
    assert current["version"] == report.version
