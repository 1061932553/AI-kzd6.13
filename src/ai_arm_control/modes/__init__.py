"""Automatic/manual mode switching."""

from ai_arm_control.modes.device_lock import (
    DeviceLock,
    DeviceLockError,
    DeviceLockSnapshot,
)
from ai_arm_control.modes.manual_app import (
    ManualAppController,
    ManualAppError,
    ManualControlConfig,
)
from ai_arm_control.modes.mode_manager import (
    ControlMode,
    ModeManager,
    ModeTransitionRecord,
)

try:
    from ai_arm_control.modes.mode_switch import (
        ModeSwitchManager,  # noqa: F401
        ModeSwitchRecord,  # noqa: F401
        ModeSwitchStatus,  # noqa: F401
    )
except ModuleNotFoundError:
    _MODE_SWITCH_EXPORTS: list[str] = []
else:
    _MODE_SWITCH_EXPORTS = [
        "ModeSwitchManager",
        "ModeSwitchRecord",
        "ModeSwitchStatus",
    ]

__all__ = [
    "ControlMode",
    "DeviceLock",
    "DeviceLockError",
    "DeviceLockSnapshot",
    "ManualAppController",
    "ManualAppError",
    "ManualControlConfig",
    "ModeManager",
    "ModeTransitionRecord",
] + _MODE_SWITCH_EXPORTS
