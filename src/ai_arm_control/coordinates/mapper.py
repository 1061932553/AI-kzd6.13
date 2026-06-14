"""Pure coordinate mapper for normalized, screen, camera, and arm XY spaces."""

from __future__ import annotations

from dataclasses import dataclass

from ai_arm_control.coordinates.bounds import Bounds2D, ensure_in_bounds
from ai_arm_control.coordinates.models import (
    ArmXY,
    CameraPixel,
    CoordinateError,
    NormalizedPoint,
    ScreenPixel,
    ScreenROI,
)
from ai_arm_control.coordinates.normalizer import normalize_screen_pixel


@dataclass(frozen=True, slots=True, kw_only=True)
class CoordinateMapperConfig:
    screen_roi: ScreenROI
    arm_bounds: Bounds2D
    flip_x: bool = False
    flip_y: bool = False
    tolerance: float = 1e-6

    def __post_init__(self) -> None:
        if self.tolerance < 0:
            raise CoordinateError("tolerance cannot be negative")


class CoordinateMapper:
    """Map coordinates without accessing cameras, arms, UI, or hardware."""

    def __init__(self, config: CoordinateMapperConfig) -> None:
        self.config = config

    def normalized_to_screen(self, point: NormalizedPoint) -> ScreenPixel:
        return ScreenPixel(
            self.config.screen_roi.left + point.x * self.config.screen_roi.width,
            self.config.screen_roi.top + point.y * self.config.screen_roi.height,
        )

    def screen_to_normalized(self, point: ScreenPixel) -> NormalizedPoint:
        return normalize_screen_pixel(point, self.config.screen_roi)

    def normalized_to_camera(self, point: NormalizedPoint) -> CameraPixel:
        screen = self.normalized_to_screen(point)
        return CameraPixel(screen.x, screen.y)

    def camera_to_normalized(self, point: CameraPixel) -> NormalizedPoint:
        return self.screen_to_normalized(ScreenPixel(point.x, point.y))

    def normalized_to_arm(self, point: NormalizedPoint) -> ArmXY:
        arm_x_ratio = 1.0 - point.x if self.config.flip_x else point.x
        arm_y_ratio = 1.0 - point.y if self.config.flip_y else point.y
        arm = ArmXY(
            self.config.arm_bounds.min_x + arm_x_ratio * self.config.arm_bounds.width,
            self.config.arm_bounds.min_y + arm_y_ratio * self.config.arm_bounds.height,
        )
        ensure_in_bounds(arm.x, arm.y, self.config.arm_bounds, label="arm coordinate")
        return arm

    def arm_to_normalized(self, point: ArmXY) -> NormalizedPoint:
        ensure_in_bounds(point.x, point.y, self.config.arm_bounds, label="arm coordinate")
        normalized_x = (point.x - self.config.arm_bounds.min_x) / self.config.arm_bounds.width
        normalized_y = (point.y - self.config.arm_bounds.min_y) / self.config.arm_bounds.height
        if self.config.flip_x:
            normalized_x = 1.0 - normalized_x
        if self.config.flip_y:
            normalized_y = 1.0 - normalized_y
        return NormalizedPoint(normalized_x, normalized_y)

    def screen_to_arm(self, point: ScreenPixel) -> ArmXY:
        return self.normalized_to_arm(self.screen_to_normalized(point))

    def arm_to_screen(self, point: ArmXY) -> ScreenPixel:
        return self.normalized_to_screen(self.arm_to_normalized(point))
