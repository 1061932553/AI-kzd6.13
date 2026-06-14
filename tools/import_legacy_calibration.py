"""CLI for importing legacy calibration JSON without touching hardware."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Import legacy calibration JSON to schema v2")
    parser.add_argument("calibration_json", type=Path)
    parser.add_argument("--device-config", type=Path, default=None)
    parser.add_argument("--device-id", default=None)
    parser.add_argument("--full", action="store_true", help="print binding and validation metadata")
    return parser


def main(argv: list[str] | None = None) -> int:
    from ai_arm_control.calibration import load_legacy_calibration
    from ai_arm_control.config import ConfigError

    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        result = load_legacy_calibration(
            args.calibration_json,
            args.device_config,
            device_id=args.device_id,
        )
    except ConfigError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    payload = result.to_dict() if args.full else result.calibration.to_dict()
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
