from __future__ import annotations

import json
from pathlib import Path

import pytest

from ai_arm_control.scripts import load_script, parse_script, validate_script
from ai_arm_control.scripts.schema import ScriptAction, ScriptValidationError
from ai_arm_control.scripts.validator import ScriptValidationLimits


def valid_script() -> dict[str, object]:
    return {
        "script_version": "1.0",
        "steps": [
            {"action": "tap", "x": 0.5, "y": 0.3},
            {"action": "wait", "duration_ms": 1000},
            {"action": "long_press", "x": 0.6, "y": 0.5, "duration_ms": 1500},
            {"action": "multi_tap", "x": 0.4, "y": 0.7, "count": 3},
            {
                "action": "swipe",
                "start": [0.5, 0.8],
                "end": [0.5, 0.2],
                "duration_ms": 600,
            },
            {
                "action": "repeat",
                "count": 2,
                "steps": [{"action": "tap", "x": 0.2, "y": 0.2}],
            },
            {"action": "home"},
            {"action": "stop"},
        ],
    }


def issue_messages(result) -> list[str]:
    return [issue.message for issue in result.issues]


def test_valid_script_passes_and_parses_actions() -> None:
    parsed = parse_script(valid_script())

    assert parsed.script_version == "1.0"
    assert parsed.steps[0].action is ScriptAction.TAP
    assert parsed.steps[-1].action is ScriptAction.STOP


def test_example_script_file_validates() -> None:
    script = load_script(Path("examples/scripts/basic_actions.json"))

    assert script.script_version == "1.0"
    assert len(script.steps) == 8


def test_invalid_action_reports_step_and_field() -> None:
    result = validate_script({"script_version": "1.0", "steps": [{"action": "drag"}]})

    assert not result.valid
    issue = result.issues[0]
    assert issue.path == "$.steps[0].action"
    assert issue.field == "action"
    assert issue.step_index == 0


def test_missing_required_field_and_unknown_field_are_reported() -> None:
    result = validate_script(
        {"script_version": "1.0", "steps": [{"action": "tap", "x": 0.5, "extra": True}]}
    )

    messages = issue_messages(result)
    assert "y is required" in messages
    assert "unknown field: extra" in messages


def test_coordinate_and_non_number_values_are_rejected() -> None:
    result = validate_script(
        {"script_version": "1.0", "steps": [{"action": "tap", "x": -0.1, "y": "0.5"}]}
    )

    assert not result.valid
    assert any(issue.field == "x" for issue in result.issues)
    assert any(issue.field == "y" for issue in result.issues)


def test_time_count_and_retry_limits_are_rejected() -> None:
    result = validate_script(
        {
            "script_version": "1.0",
            "steps": [
                {"action": "long_press", "x": 0.5, "y": 0.5, "duration_ms": 100},
                {"action": "multi_tap", "x": 0.5, "y": 0.5, "count": 999},
                {
                    "action": "swipe",
                    "start": [0.1, 0.1],
                    "end": [0.9, 0.9],
                    "duration_ms": 50,
                    "points": 1,
                    "retry": 99,
                },
            ],
        }
    )

    messages = " ".join(issue_messages(result))
    assert "duration_ms must be between 500 and 5000" in messages
    assert "count must be between 1 and 20" in messages
    assert "points must be between 2 and 100" in messages
    assert "retry must be between 0 and 5" in messages


def test_script_version_and_max_steps_are_checked() -> None:
    result = validate_script(
        {"script_version": "2.0", "steps": [{"action": "home"}] * 3},
        limits=ScriptValidationLimits(max_steps=2),
    )

    messages = issue_messages(result)
    assert "script_version must be '1.0'" in messages
    assert "steps length must be <= 2" in messages


def test_repeat_cannot_be_infinite_or_unbounded() -> None:
    result = validate_script(
        {
            "script_version": "1.0",
            "steps": [
                {
                    "action": "repeat",
                    "count": 101,
                    "steps": [{"action": "tap", "x": 0.1, "y": 0.1}],
                }
            ],
        }
    )

    assert not result.valid
    assert "count must be between 1 and 100" in issue_messages(result)


def test_expanded_repeat_limit_is_checked() -> None:
    result = validate_script(
        {
            "script_version": "1.0",
            "steps": [
                {
                    "action": "repeat",
                    "count": 10,
                    "steps": [{"action": "tap", "x": 0.1, "y": 0.1}],
                }
            ],
        },
        limits=ScriptValidationLimits(max_repeat_count=100, max_expanded_steps=5),
    )

    assert not result.valid
    assert "expanded step count must be <= 5" in issue_messages(result)


def test_swipe_path_and_start_end_are_mutually_exclusive() -> None:
    result = validate_script(
        {
            "script_version": "1.0",
            "steps": [
                {
                    "action": "swipe",
                    "start": [0.1, 0.1],
                    "end": [0.2, 0.2],
                    "path": [[0.1, 0.1], [0.2, 0.2]],
                    "duration_ms": 600,
                }
            ],
        }
    )

    assert not result.valid
    assert "swipe must use either path or start/end, not both" in issue_messages(result)


def test_parse_raises_structured_validation_error() -> None:
    with pytest.raises(ScriptValidationError) as exc:
        parse_script({"script_version": "1.0", "steps": [{"action": "wait"}]})

    assert exc.value.issues[0].field == "duration_ms"


def test_json_schema_file_is_valid_json() -> None:
    data = json.loads(Path("schemas/script_v1.json").read_text(encoding="utf-8"))

    assert data["title"] == "AI Arm Control Script v1"
