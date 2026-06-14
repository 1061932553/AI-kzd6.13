"""Import legacy calibration JSON into the stage two standard schema.

This module only reads and converts JSON data. It does not open COM ports,
connect to services, access cameras, or execute third-party software.
"""

from __future__ import annotations

from pathlib import Path

from ai_arm_control.calibration.models import (
    ArmLimits,
    HardwareBinding,
    LegacyCalibrationImport,
    StandardCalibrationV2,
)
from ai_arm_control.calibration.validator import (
    as_int_pair,
    as_int_quad,
    get_aliased,
    optional_string,
    require_mapping,
    require_number,
    validate_device_config,
    validate_standard_ranges,
)
from ai_arm_control.config import load_json_file
from ai_arm_control.models.types import JsonObject


def import_legacy_calibration(
    device_data: object | None,
    calibration_data: object,
    *,
    device_id: str | None = None,
) -> LegacyCalibrationImport:
    """Convert legacy JSON objects to calibration schema v2.

    `device_data` may be omitted for the CLI path that receives only a legacy
    calibration file. When omitted, hardware binding fields are still returned
    with `None` values except for the service URL carried by calibration JSON.
    """

    device_values = validate_device_config(
        None if device_data is None else require_mapping("legacy config.json", device_data)
    )
    calibration_values = require_mapping("legacy calibration JSON", calibration_data)

    camera_size = [
        int(
            require_number(
                "图像分辨率宽度像素_",
                get_aliased(calibration_values, "camera_width"),
            )
        ),
        int(
            require_number(
                "图像分辨率高度像素_",
                get_aliased(calibration_values, "camera_height"),
            )
        ),
    ]
    screen_roi = as_int_quad(
        "手机屏幕像素区域",
        get_aliased(calibration_values, "screen_roi"),
    )
    arm_limit_range = as_int_pair(
        "触控笔宽高极限位置",
        get_aliased(calibration_values, "arm_limit_range"),
    )
    press_z_values = as_int_or_float_pair(
        "触控笔下降距离_",
        get_aliased(calibration_values, "press_z_range"),
    )
    press_z = float(press_z_values[0])
    validate_standard_ranges(
        camera_size=camera_size,
        screen_roi=screen_roi,
        arm_limit_range=arm_limit_range,
        press_z=press_z,
    )
    resolved_device_id = device_id or _derive_device_id(calibration_values)
    service_url = optional_string(
        "url地址",
        get_aliased(calibration_values, "service_url", required=False),
    )

    calibration = StandardCalibrationV2(
        device_id=resolved_device_id,
        camera_size=camera_size,
        screen_roi=screen_roi,
        arm_limits=ArmLimits(x_max=arm_limit_range[0], y_max=arm_limit_range[1]),
        press_z=press_z,
    )
    return LegacyCalibrationImport(
        calibration=calibration,
        hardware_binding=HardwareBinding(
            service_url=service_url,
            com_port=optional_string("com", device_values.get("com")),
            camera_name=optional_string("camera", device_values.get("camera")),
            usb_unique_id=optional_string("unique_id", device_values.get("unique_id")),
        ),
        needs_revalidation=True,
        notes=[
            "Legacy values are imported as initial calibration data only.",
            "Mapping matrix, correction grid, and error metrics require fresh validation.",
        ],
        raw_legacy={
            "device_config": dict(device_values) if device_values else None,
            "calibration": dict(calibration_values),
        },
    )


def load_legacy_calibration(
    calibration_path: str | Path,
    device_config_path: str | Path | None = None,
    *,
    device_id: str | None = None,
) -> LegacyCalibrationImport:
    """Read legacy JSON files and convert them without modifying source files."""

    calibration_file = Path(calibration_path)
    if (
        device_config_path is not None
        and calibration_file.name.lower() == "config.json"
        and Path(device_config_path).name.lower() != "config.json"
    ):
        calibration_file, device_config_path = Path(device_config_path), calibration_file
    inferred_device_config_path = (
        Path(device_config_path)
        if device_config_path is not None
        else _find_sibling_device_config(calibration_file)
    )
    device_data = (
        load_json_file(inferred_device_config_path) if inferred_device_config_path else None
    )
    return import_legacy_calibration(
        device_data,
        load_json_file(calibration_file),
        device_id=device_id,
    )


def as_int_or_float_pair(name: str, value: object) -> list[int | float]:
    from ai_arm_control.calibration.validator import require_list

    items = require_list(name, value, 2)
    return [require_number(f"{name}[{index}]", item) for index, item in enumerate(items)]


def _derive_device_id(calibration_values: JsonObject) -> str:
    slot = get_aliased(calibration_values, "slot", required=False)
    if slot is None:
        return "ARM-001"
    slot_number = int(require_number("机位_", slot))
    if slot_number <= 0:
        return "ARM-001"
    return f"ARM-{slot_number:03d}"


def _find_sibling_device_config(calibration_file: Path) -> Path | None:
    sibling = calibration_file.with_name("config.json")
    return sibling if sibling.is_file() else None
