"""Offline camera preview helper.

This tool reads a test-video JSON file and writes a cropped debug PPM. It does
not open USB cameras.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Preview offline test video ROI")
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--device-id", default="ARM-PREVIEW")
    parser.add_argument("--roi", nargs=4, type=int, default=[0, 0, 4, 4])
    parser.add_argument("--output-dir", type=Path, default=Path("reports/debug_screenshots"))
    return parser


def main(argv: list[str] | None = None) -> int:
    from ai_arm_control.vision import CameraService, CameraServiceConfig, TestVideoFrameSource

    args = build_parser().parse_args(argv)
    service = CameraService(
        source=TestVideoFrameSource(args.source),
        config=CameraServiceConfig(
            device_id=args.device_id,
            screen_roi=tuple(args.roi),
            debug_output_dir=args.output_dir,
        ),
    )
    service.open()
    roi = service.capture_screen_roi()
    path = service.save_debug_screenshot(roi, prefix="camera_preview")
    service.close()
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
