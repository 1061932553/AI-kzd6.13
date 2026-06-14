"""Calibration schema models for stage two.

These models are pure data contracts. They do not connect to services, serial
ports, cameras, or hardware.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Self

from ai_arm_control.config import ConfigError
from ai_arm_control.models.types import JsonObject

SCHEMA_VERSION = "2.0"


@dataclass(frozen=True, slots=True, kw_only=True)
class ArmLimits:
    x_min: int = 0
    x_max: int
    y_min: int = 0
    y_max: int

    def __post_init__(self) -> None:
        if self.x_min > self.x_max:
            raise ConfigError("arm_limits.x_min cannot be greater than x_max")
        if self.y_min > self.y_max:
            raise ConfigError("arm_limits.y_min cannot be greater than y_max")
        if self.x_min < 0 or self.y_min < 0:
            raise ConfigError("arm_limits minimum values cannot be negative")

    def to_dict(self) -> JsonObject:
        return {
            "x_min": self.x_min,
            "x_max": self.x_max,
            "y_min": self.y_min,
            "y_max": self.y_max,
        }

    @classmethod
    def from_dict(cls, data: object) -> Self:
        from ai_arm_control.calibration.validator import require_mapping, require_number

        values = require_mapping(cls.__name__, data)
        unknown_fields = set(values) - {"x_min", "x_max", "y_min", "y_max"}
        if unknown_fields:
            raise ConfigError(f"{cls.__name__} got unknown field(s): {sorted(unknown_fields)}")
        return cls(
            x_min=int(require_number("arm_limits.x_min", values.get("x_min", 0))),
            x_max=int(require_number("arm_limits.x_max", values["x_max"])),
            y_min=int(require_number("arm_limits.y_min", values.get("y_min", 0))),
            y_max=int(require_number("arm_limits.y_max", values["y_max"])),
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class HardwareBinding:
    service_url: str | None = None
    com_port: str | None = None
    camera_name: str | None = None
    usb_unique_id: str | None = None

    def __eq__(self, other: object) -> bool:
        if isinstance(other, dict):
            return self.to_dict() == other
        if isinstance(other, HardwareBinding):
            return self.to_dict() == other.to_dict()
        return False

    def to_dict(self) -> JsonObject:
        return {
            "service_url": self.service_url,
            "com_port": self.com_port,
            "camera_name": self.camera_name,
            "usb_unique_id": self.usb_unique_id,
        }


@dataclass(frozen=True, slots=True, kw_only=True)
class StandardCalibrationV2:
    device_id: str
    camera_size: list[int]
    screen_roi: list[int]
    arm_limits: ArmLimits
    press_z: float
    schema_version: str = SCHEMA_VERSION
    mapping_matrix: list[list[float]] = field(default_factory=list)
    correction_grid: list[JsonObject] = field(default_factory=list)
    average_error: float | None = None
    maximum_error: float | None = None
    metadata: JsonObject = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise ConfigError(f"unsupported calibration schema_version: {self.schema_version}")
        if len(self.camera_size) != 2 or self.camera_size[0] <= 0 or self.camera_size[1] <= 0:
            raise ConfigError("camera_size expects two positive values")
        if len(self.screen_roi) != 4:
            raise ConfigError("screen_roi expects 4 item(s)")
        left, top, right, bottom = self.screen_roi
        if left > right or top > bottom:
            raise ConfigError("screen_roi has an invalid coordinate range")
        camera_width, camera_height = self.camera_size
        if left < 0 or top < 0 or right > camera_width or bottom > camera_height:
            raise ConfigError("screen_roi must stay inside camera_size")
        if self.arm_limits.x_max <= self.arm_limits.x_min:
            raise ConfigError("arm_limits x range must be positive")
        if self.arm_limits.y_max <= self.arm_limits.y_min:
            raise ConfigError("arm_limits y range must be positive")
        if self.press_z <= 0:
            raise ConfigError("press_z must be positive")
        if self.average_error is not None and self.average_error < 0:
            raise ConfigError("average_error cannot be negative")
        if self.maximum_error is not None and self.maximum_error < 0:
            raise ConfigError("maximum_error cannot be negative")

    def to_dict(self, *, include_empty_stage_fields: bool = True) -> JsonObject:
        data: JsonObject = {
            "schema_version": self.schema_version,
            "device_id": self.device_id,
            "camera_size": list(self.camera_size),
            "screen_roi": list(self.screen_roi),
            "arm_limits": self.arm_limits.to_dict(),
            "press_z": self.press_z,
        }
        if include_empty_stage_fields:
            data.update(
                {
                    "mapping_matrix": [list(row) for row in self.mapping_matrix],
                    "correction_grid": [dict(point) for point in self.correction_grid],
                    "average_error": self.average_error,
                    "maximum_error": self.maximum_error,
                }
            )
        if self.metadata:
            data["metadata"] = dict(self.metadata)
        return data

    @classmethod
    def from_dict(cls, data: object) -> Self:
        from ai_arm_control.calibration.validator import (
            as_int_pair,
            as_int_quad,
            require_mapping,
            require_number,
        )

        values = require_mapping(cls.__name__, data)
        allowed_fields = {
            "schema_version",
            "device_id",
            "camera_size",
            "screen_roi",
            "arm_limits",
            "press_z",
            "mapping_matrix",
            "correction_grid",
            "average_error",
            "maximum_error",
            "metadata",
        }
        unknown_fields = set(values) - allowed_fields
        if unknown_fields:
            raise ConfigError(f"{cls.__name__} got unknown field(s): {sorted(unknown_fields)}")
        return cls(
            schema_version=str(values.get("schema_version", SCHEMA_VERSION)),
            device_id=str(values["device_id"]),
            camera_size=as_int_pair("camera_size", values["camera_size"]),
            screen_roi=as_int_quad("screen_roi", values["screen_roi"]),
            arm_limits=ArmLimits.from_dict(values["arm_limits"]),
            press_z=float(require_number("press_z", values["press_z"])),
            mapping_matrix=[
                [float(require_number("mapping_matrix item", item)) for item in row]
                for row in values.get("mapping_matrix", [])
            ],
            correction_grid=[
                dict(require_mapping("correction_grid item", item))
                for item in values.get("correction_grid", [])
            ],
            average_error=(
                None
                if values.get("average_error") is None
                else float(require_number("average_error", values["average_error"]))
            ),
            maximum_error=(
                None
                if values.get("maximum_error") is None
                else float(require_number("maximum_error", values["maximum_error"]))
            ),
            metadata=dict(values.get("metadata", {})),
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class LegacyCalibrationImport:
    calibration: StandardCalibrationV2
    hardware_binding: HardwareBinding = field(default_factory=HardwareBinding)
    needs_revalidation: bool = True
    notes: list[str] = field(default_factory=list)
    raw_legacy: JsonObject = field(default_factory=dict)

    def to_dict(self) -> JsonObject:
        return {
            "calibration": self.calibration.to_dict(),
            "hardware_binding": self.hardware_binding.to_dict(),
            "needs_revalidation": self.needs_revalidation,
            "notes": list(self.notes),
            "raw_legacy": dict(self.raw_legacy),
        }


CalibrationJson = dict[str, Any]
