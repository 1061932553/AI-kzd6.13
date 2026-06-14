"""Offline corner calibration tool.

The fixture accepted by this tool is a project-local JSON RGB frame container.
It intentionally does not open cameras or decode arbitrary JPEG files.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Calibrate screen corners from offline fixture")
    parser.add_argument("image", type=Path)
    parser.add_argument("--corners-json", default=None, help="override corners as JSON list")
    parser.add_argument("--output", type=Path, default=Path("reports/homography_calibration.json"))
    parser.add_argument("--preview-dir", type=Path, default=Path("reports/debug_screenshots"))
    return parser


def main(argv: list[str] | None = None) -> int:
    from ai_arm_control.calibration import HomographyError, build_homography_calibration
    from ai_arm_control.vision.screen_rectifier import ScreenRectifier

    args = build_parser().parse_args(argv)
    try:
        payload = json.loads(args.image.read_text(encoding="utf-8"))
        frame = _frame_from_payload(payload)
        corners = json.loads(args.corners_json) if args.corners_json else payload["corners"]
        output_width, output_height = payload["output_size"]
        calibration = build_homography_calibration(
            corners,
            output_width=int(output_width),
            output_height=int(output_height),
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        calibration.save_json(args.output)
        preview = ScreenRectifier(calibration).save_preview(
            frame,
            args.preview_dir,
            device_id=str(payload.get("device_id", "ARM-PREVIEW")),
        )
    except (OSError, json.JSONDecodeError, KeyError, HomographyError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"calibration": str(args.output), "preview": str(preview)}, indent=2))
    return 0


def _frame_from_payload(payload: object) -> Any:
    from ai_arm_control.models.types import utc_now
    from ai_arm_control.simulators.camera import CameraFrame

    if not isinstance(payload, dict):
        raise ValueError("fixture expects a mapping")
    if payload.get("format") != "ai-arm-control-rgb-json-v1":
        raise ValueError("unsupported fixture format")
    width = int(payload["width"])
    height = int(payload["height"])
    channels = int(payload.get("channels", 3))
    data = _decode_frame_payload(payload["frames"][0], width, height, channels)
    return CameraFrame(
        camera_name=str(payload.get("device_id", "fixture")),
        width=width,
        height=height,
        channels=channels,
        pixel_format="RGB24",
        data=data,
        frame_index=1,
        captured_at=utc_now().isoformat(),
        metadata={"source": "offline_fixture"},
    )


def _decode_frame_payload(item: object, width: int, height: int, channels: int) -> bytes:
    if channels != 3:
        raise ValueError("only RGB24 fixtures are supported")
    if not isinstance(item, dict):
        raise ValueError("fixture frame expects a mapping")
    byte_length = width * height * channels
    if "data_hex" in item:
        data = bytes.fromhex(str(item["data_hex"]))
        if len(data) != byte_length:
            raise ValueError("data_hex length does not match frame dimensions")
        return data
    fill = item.get("fill")
    if (
        not isinstance(fill, list)
        or len(fill) != 3
        or any(not isinstance(value, int) for value in fill)
    ):
        raise ValueError("fixture frame requires fill [r, g, b] or data_hex")
    if any(value < 0 or value > 255 for value in fill):
        raise ValueError("fill values must be between 0 and 255")
    return bytes(fill) * (width * height)


if __name__ == "__main__":
    raise SystemExit(main())
