"""Calibration data contracts and import helpers."""

from ai_arm_control.calibration.corner_selector import CornerSelection, select_manual_corners
from ai_arm_control.calibration.correction_grid import (
    CorrectionGrid,
    CorrectionGridError,
    CorrectionGridPoint,
    CorrectionVector,
)
from ai_arm_control.calibration.error_metrics import (
    CalibrationErrorSample,
    CalibrationErrorSummary,
    summarize_errors,
)
from ai_arm_control.calibration.grid_generator import CalibrationGridPoint, generate_4x4_grid
from ai_arm_control.calibration.homography import (
    HomographyCalibration,
    HomographyError,
    HomographyMatrix,
    Point2D,
    build_homography_calibration,
)
from ai_arm_control.calibration.legacy_importer import (
    import_legacy_calibration,
    load_legacy_calibration,
)
from ai_arm_control.calibration.models import (
    ArmLimits,
    HardwareBinding,
    LegacyCalibrationImport,
    StandardCalibrationV2,
)
from ai_arm_control.calibration.report import (
    CalibrationReport,
    CalibrationReportError,
    CalibrationReportStore,
    build_calibration_report,
)
from ai_arm_control.calibration.session import (
    CalibrationPointRecord,
    CalibrationPointStatus,
    CalibrationSession,
    CalibrationSessionError,
    CalibrationSessionStatus,
)
from ai_arm_control.calibration.touch_capture import (
    ManualTouchCapture,
    TouchCaptureStore,
    TouchSample,
)
from ai_arm_control.calibration.validator import validate_standard_ranges

__all__ = [
    "ArmLimits",
    "CalibrationGridPoint",
    "CalibrationErrorSample",
    "CalibrationErrorSummary",
    "CalibrationPointRecord",
    "CalibrationPointStatus",
    "CalibrationSession",
    "CalibrationSessionError",
    "CalibrationSessionStatus",
    "CorrectionGrid",
    "CorrectionGridError",
    "CorrectionGridPoint",
    "CorrectionVector",
    "CornerSelection",
    "HardwareBinding",
    "HomographyCalibration",
    "HomographyError",
    "HomographyMatrix",
    "LegacyCalibrationImport",
    "ManualTouchCapture",
    "Point2D",
    "StandardCalibrationV2",
    "TouchCaptureStore",
    "TouchSample",
    "build_homography_calibration",
    "build_calibration_report",
    "generate_4x4_grid",
    "import_legacy_calibration",
    "load_legacy_calibration",
    "select_manual_corners",
    "summarize_errors",
    "validate_standard_ranges",
    "CalibrationReport",
    "CalibrationReportError",
    "CalibrationReportStore",
]
