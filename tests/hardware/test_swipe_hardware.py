from __future__ import annotations

import os

import pytest


def test_swipe_hardware_requires_explicit_switches(request) -> None:  # noqa: ANN001
    if not request.config.getoption("--hardware"):
        pytest.skip("hardware tests require --hardware")
    if os.environ.get("AI_ARM_CONTROL_ENABLE_HARDWARE_TESTS") != "1":
        pytest.skip("hardware tests require AI_ARM_CONTROL_ENABLE_HARDWARE_TESTS=1")
    pytest.fail("real swipe hardware test is not wired in P2-08 offline package")
