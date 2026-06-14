"""Standard arm action layer."""

from ai_arm_control.actions.long_press import execute_long_press
from ai_arm_control.actions.models import (
    TouchActionConfig,
    TouchActionError,
    TouchActionTiming,
    TouchTarget,
)
from ai_arm_control.actions.multi_tap import execute_multi_tap
from ai_arm_control.actions.result import (
    TouchActionLogEntry,
    TouchActionResult,
    TouchActionStatus,
)
from ai_arm_control.actions.tap import TapAction, execute_tap

try:
    from ai_arm_control.actions.standard_arm import (
        StandardArmActionConfig,  # noqa: F401
        StandardArmActionLayer,  # noqa: F401
        StandardArmActionResult,  # noqa: F401
        StandardArmSubAction,  # noqa: F401
    )
except ModuleNotFoundError:  # pragma: no cover - compatibility for branch-limited PRs.
    _STANDARD_ARM_EXPORTS: list[str] = []
else:
    _STANDARD_ARM_EXPORTS = [
        "StandardArmActionConfig",
        "StandardArmActionLayer",
        "StandardArmActionResult",
        "StandardArmSubAction",
    ]

__all__ = [
    "TapAction",
    "TouchActionConfig",
    "TouchActionError",
    "TouchActionLogEntry",
    "TouchActionResult",
    "TouchActionStatus",
    "TouchActionTiming",
    "TouchTarget",
    "execute_long_press",
    "execute_multi_tap",
    "execute_tap",
] + _STANDARD_ARM_EXPORTS
