"""Validation helpers for legacy calibration imports."""

from __future__ import annotations

from typing import Any

from ai_arm_control.config import ConfigError
from ai_arm_control.models.types import JsonObject

FIELD_ALIASES: dict[str, tuple[str, ...]] = {
    "slot": ("机位_", "device_slot", "slot"),
    "camera_width": ("图像分辨率宽度像素_", "camera_width", "image_width"),
    "camera_height": ("图像分辨率高度像素_", "camera_height", "image_height"),
    "screen_roi": ("手机屏幕像素区域", "screen_roi", "screen_region"),
    "press_z_range": ("触控笔下降距离_", "press_z_range", "stylus_down_distance"),
    "arm_limit_range": ("触控笔宽高极限位置", "arm_limit_range", "arm_limits"),
    "service_url": ("url地址", "service_url", "url"),
}


def require_mapping(name: str, value: object) -> JsonObject:
    if not isinstance(value, dict):
        raise ConfigError(f"{name} expects a mapping")
    return value


def require_list(name: str, value: object, length: int | None = None) -> list[Any]:
    if not isinstance(value, list):
        raise ConfigError(f"{name} expects a list")
    if length is not None and len(value) != length:
        raise ConfigError(f"{name} expects {length} item(s)")
    return value


def require_number(name: str, value: object) -> int | float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ConfigError(f"{name} expects a number")
    return value


def optional_string(name: str, value: object) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ConfigError(f"{name} expects a string")
    return value


def as_int_pair(name: str, value: object) -> list[int]:
    items = require_list(name, value, 2)
    return [int(require_number(f"{name}[{index}]", item)) for index, item in enumerate(items)]


def as_int_quad(name: str, value: object) -> list[int]:
    items = require_list(name, value, 4)
    return [int(require_number(f"{name}[{index}]", item)) for index, item in enumerate(items)]


def get_aliased(values: JsonObject, canonical_name: str, *, required: bool = True) -> object:
    for field_name in FIELD_ALIASES[canonical_name]:
        if field_name in values:
            return values[field_name]
    if required:
        names = ", ".join(FIELD_ALIASES[canonical_name])
        raise ConfigError(f"legacy calibration JSON missing field(s): {names}")
    return None


def validate_device_config(values: JsonObject | None) -> JsonObject:
    if values is None:
        return {}
    required_fields = {"com", "unique_id", "camera"}
    missing_fields = required_fields - set(values)
    if missing_fields:
        names = ", ".join(sorted(missing_fields))
        raise ConfigError(f"legacy config.json missing field(s): {names}")
    for field_name in required_fields:
        optional_string(field_name, values[field_name])
    if "name" in values:
        optional_string("name", values["name"])
    return values


def validate_standard_ranges(
    *,
    camera_size: list[int],
    screen_roi: list[int],
    arm_limit_range: list[int],
    press_z: float,
) -> None:
    if camera_size[0] <= 0 or camera_size[1] <= 0:
        raise ConfigError("camera_size expects positive width and height")
    left, top, right, bottom = screen_roi
    if left > right or top > bottom:
        raise ConfigError("screen_roi has an invalid coordinate range")
    if left < 0 or top < 0 or right > camera_size[0] or bottom > camera_size[1]:
        raise ConfigError("screen_roi must stay inside camera_size")
    if arm_limit_range[0] <= 0 or arm_limit_range[1] <= 0:
        raise ConfigError("arm_limits must be positive")
    if press_z <= 0:
        raise ConfigError("press_z must be positive")
