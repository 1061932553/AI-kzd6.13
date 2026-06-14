from __future__ import annotations

import os

import pytest

pytestmark = pytest.mark.skipif(
    os.environ.get("AI_ARM_CONTROL_ENABLE_HARDWARE_TESTS") != "1",
    reason="hardware tests require AI_ARM_CONTROL_ENABLE_HARDWARE_TESTS=1",
)


def test_hardware_tests_require_explicit_environment_switch() -> None:
    assert os.environ["AI_ARM_CONTROL_ENABLE_HARDWARE_TESTS"] == "1"
