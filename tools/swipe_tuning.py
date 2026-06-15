"""Generate offline swipe trajectory timing samples for tuning."""

from __future__ import annotations

import argparse
import json
import sys

from ai_arm_control.actions.interpolation import EasingMode
from ai_arm_control.actions.trajectory import build_linear_trajectory
from ai_arm_control.coordinates.models import NormalizedPoint


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", nargs=2, type=float, default=[0.5, 0.8])
    parser.add_argument("--end", nargs=2, type=float, default=[0.5, 0.2])
    parser.add_argument("--duration-ms", type=int, default=600)
    parser.add_argument("--points", type=int, default=30)
    parser.add_argument("--easing", choices=[item.value for item in EasingMode], default="linear")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    trajectory = build_linear_trajectory(
        start=NormalizedPoint(args.start[0], args.start[1]),
        end=NormalizedPoint(args.end[0], args.end[1]),
        duration_ms=args.duration_ms,
        point_count=args.points,
        easing=EasingMode(args.easing),
    )
    print(json.dumps([point.to_dict() for point in trajectory], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
