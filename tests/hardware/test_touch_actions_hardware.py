from __future__ import annotations

import os

import pytest


def pytestmark_condition(config) -> bool:  # noqa: ANN001
    return not config.getoption("--hardware") or os.environ.get(
        "AI_ARM_CONTROL_ENABLE_HARDWARE_TESTS"
    ) != "1"


def test_touch_action_hardware_requires_explicit_switches(request) -> None:  # noqa: ANN001
    if pytestmark_condition(request.config):
        pytest.skip("hardware tests require --hardware and AI_ARM_CONTROL_ENABLE_HARDWARE_TESTS=1")
    pytest.fail("real touch-action hardware test is not wired in P2-07 offline package")
