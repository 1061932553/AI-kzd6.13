"""Models and protocols for script-level touch actions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from ai_arm_control.coordinates.models import ArmXY, NormalizedPoint, require_finite_number


class TouchActionError(ValueError):
    """Raised when a touch action request or configuration is invalid."""


class TouchArmAPI(Protocol):
    def move_xy(self, x: float, y: float) -> object: ...

    def pen_down(self, z: float) -> object: ...

    def pen_up(self) -> object: ...


class TouchSleeper(Protocol):
    def sleep_ms(self, duration_ms: int) -> None: ...


@dataclass(frozen=True, slots=True)
class TouchActionTiming:
    xy_settle_ms: int = 80
    down_delay_ms: int = 80
    hold_ms: int = 100
    up_delay_ms: int = 80
    tap_interval_ms: int = 120

    def __post_init__(self) -> None:
        for field_name in (
            "xy_settle_ms",
            "down_delay_ms",
            "hold_ms",
            "up_delay_ms",
            "tap_interval_ms",
        ):
            if getattr(self, field_name) < 0:
                raise TouchActionError(f"{field_name} cannot be negative")


@dataclass(frozen=True, slots=True)
class TouchActionConfig:
    press_depth: float = 7.0
    timing: TouchActionTiming = TouchActionTiming()

    def __post_init__(self) -> None:
        press_depth = require_finite_number("press_depth", self.press_depth)
        if press_depth <= 0:
            raise TouchActionError("press_depth must be positive")
        object.__setattr__(self, "press_depth", press_depth)


@dataclass(frozen=True, slots=True)
class TouchTarget:
    normalized: NormalizedPoint
    arm_xy: ArmXY

    def to_dict(self) -> dict[str, object]:
        return {
            "normalized": {"x": self.normalized.x, "y": self.normalized.y},
            "arm_xy": {"x": self.arm_xy.x, "y": self.arm_xy.y},
        }
