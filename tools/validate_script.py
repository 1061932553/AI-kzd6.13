"""Validate a v1 touch script without executing hardware actions."""

from __future__ import annotations

import argparse
import json
import sys

from ai_arm_control.scripts.parser import ScriptParseError, load_script
from ai_arm_control.scripts.schema import ScriptValidationError


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("script", help="Path to a JSON script file")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        script = load_script(args.script)
    except ScriptValidationError as exc:
        print(json.dumps(exc.to_dict(), ensure_ascii=False, indent=2))
        return 1
    except ScriptParseError as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False, indent=2))
        return 1

    print(
        json.dumps(
            {
                "valid": True,
                "script_version": script.script_version,
                "step_count": len(script.steps),
                "hardware_actions_executed": False,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
