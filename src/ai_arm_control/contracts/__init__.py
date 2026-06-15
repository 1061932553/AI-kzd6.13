"""Public interface contracts package."""

from __future__ import annotations

from typing import Protocol

from ai_arm_control.models import ArmCommand, CommandResult, DeviceStateInfo


class StandardDeviceAPI(Protocol):
    """Unified device action interface used by orchestration code."""

    def connect(self) -> CommandResult:
        """Acquire the device resource through the adapter boundary."""

    def disconnect(self) -> CommandResult:
        """Release the device resource through the adapter boundary."""

    def home(self) -> CommandResult:
        """Return the arm to the configured home position."""

    def move_xy(self, x: int, y: int) -> CommandResult:
        """Move to an XY position after safety validation."""

    def pen_down(self, z: int) -> CommandResult:
        """Move the stylus to a configured down Z value."""

    def pen_up(self) -> CommandResult:
        """Raise the stylus to the configured up Z value."""

    def stop(self) -> CommandResult:
        """Stop accepting queued work and move the adapter to a stopped state."""

    def get_status(self) -> DeviceStateInfo:
        """Return current device state without touching hardware unexpectedly."""

    def health_check(self) -> bool:
        """Return whether the adapter can accept commands."""

    def execute(self, command: ArmCommand) -> CommandResult:
        """Execute one device command through the adapter boundary."""

    def load_calibration(self, calibration: object) -> None:
        """Attach calibration data for later coordinate conversion steps."""


__all__ = ["StandardDeviceAPI"]
