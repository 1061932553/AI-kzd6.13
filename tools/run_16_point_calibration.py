"""Run a safe 16-point calibration collection session."""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from pathlib import Path

from ai_arm_control.calibration.session import CalibrationSession
from ai_arm_control.calibration.touch_capture import ManualTouchCapture
from ai_arm_control.coordinates import Bounds2D, CoordinateMapper, CoordinateMapperConfig, ScreenROI


@dataclass(slots=True)
class SimulatorCalibrationExecutor:
    sent_points: list[dict[str, object]] = field(default_factory=list)

    def tap_point(self, point, arm_x: float, arm_y: float) -> dict[str, object]:  # noqa: ANN001
        receipt = {
            "mode": "simulator",
            "point_id": point.point_id,
            "arm_x": arm_x,
            "arm_y": arm_y,
            "status": "sent",
        }
        self.sent_points.append(receipt)
        return receipt


def build_default_mapper() -> CoordinateMapper:
    return CoordinateMapper(
        CoordinateMapperConfig(
            screen_roi=ScreenROI.from_sequence([64, 32, 482, 911]),
            arm_bounds=Bounds2D(min_x=0, max_x=366, min_y=0, max_y=160),
        )
    )


def run_simulator(args: argparse.Namespace) -> int:
    session = CalibrationSession.create_4x4(device_id=args.device, margin=args.margin)
    mapper = build_default_mapper()
    executor = SimulatorCalibrationExecutor()
    manual_capture = ManualTouchCapture()

    session.start()
    while session.next_pending() is not None:
        record = session.execute_next(mapper=mapper, executor=executor)
        sample = manual_capture.capture(
            point_id=record.point.point_id,
            target=record.point.target,
            x=record.point.target.x,
            y=record.point.target.y,
        )
        session.record_touch(sample)

    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    session_path = output / f"{session.session_id}.json"
    session.save_json(session_path)
    print(f"session_id={session.session_id}")
    print(f"status={session.status.value}")
    print(f"points={len(session.records)}")
    print(f"output={session_path}")
    return 0


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", required=True, help="simulator or explicit device id")
    parser.add_argument("--hardware", action="store_true", help="request real hardware mode")
    parser.add_argument(
        "--confirm-hardware",
        action="store_true",
        help="second confirmation required before any hardware calibration attempt",
    )
    parser.add_argument("--margin", type=float, default=0.1)
    parser.add_argument("--output", default="reports/calibration_sessions")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if args.hardware:
        if not args.confirm_hardware:
            print(
                "hardware calibration requires --confirm-hardware before any action",
                file=sys.stderr,
            )
            return 2
        print("hardware calibration runner is not enabled in this offline package", file=sys.stderr)
        return 2
    if args.device != "simulator":
        print("non-hardware calibration currently requires --device simulator", file=sys.stderr)
        return 2
    return run_simulator(args)


if __name__ == "__main__":
    raise SystemExit(main())
