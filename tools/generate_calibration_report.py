"""Generate a local correction-grid calibration report from a P2-05 session JSON."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ai_arm_control.calibration.report import CalibrationReportStore, build_calibration_report
from ai_arm_control.calibration.session import CalibrationSession


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("session_json", help="P2-05 calibration session JSON")
    parser.add_argument("--output", default="reports/calibration")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    session = CalibrationSession.load_json(args.session_json)
    report = build_calibration_report(session)
    output_path = CalibrationReportStore(Path(args.output)).save(report)
    print(f"version={report.version}")
    print(f"average_error={report.before_summary.average_error:.12f}")
    print(f"maximum_error={report.before_summary.maximum_error:.12f}")
    print(f"p95_error={report.before_summary.p95_error:.12f}")
    print(f"after_average_error={report.after_summary.average_error:.12f}")
    print(f"output={output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
