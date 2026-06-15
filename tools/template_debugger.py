"""Debug offline template matching without touching cameras or hardware."""

from __future__ import annotations

import argparse
import json
import sys

from ai_arm_control.vision.template_matcher import (
    TemplateMatcher,
    load_rgb_frame,
    load_template_image,
)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", required=True)
    parser.add_argument("--template", required=True)
    parser.add_argument("--confidence", type=float, default=0.85)
    parser.add_argument("--search", nargs=4, type=int, metavar=("LEFT", "TOP", "RIGHT", "BOTTOM"))
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    frame = load_rgb_frame(args.image)
    template = load_template_image(args.template)
    result = TemplateMatcher(confidence_threshold=args.confidence).match(
        frame,
        template,
        search_rect=tuple(args.search) if args.search else None,
    )
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    return 0 if result.found else 1


if __name__ == "__main__":
    raise SystemExit(main())
