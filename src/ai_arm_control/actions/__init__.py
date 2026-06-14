"""Standard arm action layer."""

from ai_arm_control.actions.interpolation import EasingMode
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
from ai_arm_control.actions.swipe import SwipeAction, SwipeCancelToken, SwipeConfig, execute_swipe
from ai_arm_control.actions.tap import TapAction, execute_tap
from ai_arm_control.actions.trajectory import (
    ArmTrajectoryPoint,
    TrajectoryError,
    TrajectoryPoint,
    build_linear_trajectory,
    build_polyline_trajectory,
    map_trajectory_to_arm,
)

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
    "ArmTrajectoryPoint",
    "EasingMode",
    "SwipeAction",
    "SwipeCancelToken",
    "SwipeConfig",
    "TouchActionConfig",
    "TouchActionError",
    "TouchActionLogEntry",
    "TouchActionResult",
    "TouchActionStatus",
    "TouchActionTiming",
    "TouchTarget",
    "TrajectoryError",
    "TrajectoryPoint",
    "build_linear_trajectory",
    "build_polyline_trajectory",
    "execute_swipe",
    "execute_long_press",
    "execute_multi_tap",
    "execute_tap",
    "map_trajectory_to_arm",
] + _STANDARD_ARM_EXPORTS
