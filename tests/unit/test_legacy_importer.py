from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from ai_arm_control.calibration import (
    StandardCalibrationV2,
    import_legacy_calibration,
    load_legacy_calibration,
)
from ai_arm_control.config import ConfigError

LEGACY_DEVICE = {
    "name": "1号机械臂",
    "com": "COM4",
    "unique_id": "USBVID_1A86&PID_75235&2B28DE69&0&8",
    "camera": "USB Camera2-B",
}

LEGACY_CALIBRATION = {
    "机位_": 1,
    "图像分辨率宽度像素_": 540,
    "图像分辨率高度像素_": 960,
    "触控笔下降距离_": [7.0, 7.5],
    "url地址": "http://127.0.0.1:8082/MyWcfService/getstring",
    "手机屏幕像素区域": [64, 32, 482, 911],
    "触控笔宽高极限位置": [366, 160],
}


EXPECTED_STANDARD = {
    "schema_version": "2.0",
    "device_id": "ARM-001",
    "camera_size": [540, 960],
    "screen_roi": [64, 32, 482, 911],
    "arm_limits": {
        "x_min": 0,
        "x_max": 366,
        "y_min": 0,
        "y_max": 160,
    },
    "press_z": 7.0,
    "mapping_matrix": [],
    "correction_grid": [],
    "average_error": None,
    "maximum_error": None,
}


def test_correct_legacy_files_import_to_standard_json(tmp_path: Path) -> None:
    config_path, calibration_path = write_legacy_files(tmp_path)

    result = load_legacy_calibration(calibration_path, config_path)

    assert result.calibration.to_dict() == EXPECTED_STANDARD
    assert result.hardware_binding.to_dict() == {
        "service_url": "http://127.0.0.1:8082/MyWcfService/getstring",
        "com_port": "COM4",
        "camera_name": "USB Camera2-B",
        "usb_unique_id": "USBVID_1A86&PID_75235&2B28DE69&0&8",
    }
    assert result.needs_revalidation is True


def test_missing_required_field_reports_clear_error() -> None:
    bad_calibration = dict(LEGACY_CALIBRATION)
    del bad_calibration["手机屏幕像素区域"]

    with pytest.raises(ConfigError, match="手机屏幕像素区域"):
        import_legacy_calibration(LEGACY_DEVICE, bad_calibration)


def test_wrong_field_type_reports_clear_error() -> None:
    bad_calibration = dict(LEGACY_CALIBRATION)
    bad_calibration["触控笔下降距离_"] = "7.0"

    with pytest.raises(ConfigError, match="触控笔下降距离_ expects a list"):
        import_legacy_calibration(LEGACY_DEVICE, bad_calibration)


def test_out_of_range_screen_roi_is_rejected() -> None:
    bad_calibration = dict(LEGACY_CALIBRATION)
    bad_calibration["手机屏幕像素区域"] = [64, 32, 600, 911]

    with pytest.raises(ConfigError, match="screen_roi must stay inside camera_size"):
        import_legacy_calibration(LEGACY_DEVICE, bad_calibration)


def test_alias_json_version_imports_to_same_standard_shape() -> None:
    alias_calibration = {
        "slot": 1,
        "camera_width": 540,
        "camera_height": 960,
        "press_z_range": [7.0, 7.5],
        "service_url": "http://127.0.0.1:8082/MyWcfService/getstring",
        "screen_roi": [64, 32, 482, 911],
        "arm_limit_range": [366, 160],
    }

    result = import_legacy_calibration(LEGACY_DEVICE, alias_calibration)

    assert result.calibration.to_dict() == EXPECTED_STANDARD


def test_original_files_are_not_modified(tmp_path: Path) -> None:
    config_path, calibration_path = write_legacy_files(tmp_path)
    before_config = config_path.read_text(encoding="utf-8")
    before_calibration = calibration_path.read_text(encoding="utf-8")

    load_legacy_calibration(calibration_path, config_path)

    assert config_path.read_text(encoding="utf-8") == before_config
    assert calibration_path.read_text(encoding="utf-8") == before_calibration


def test_same_input_produces_same_output() -> None:
    first = import_legacy_calibration(LEGACY_DEVICE, LEGACY_CALIBRATION).calibration.to_dict()
    second = import_legacy_calibration(LEGACY_DEVICE, LEGACY_CALIBRATION).calibration.to_dict()

    assert first == second


def test_standard_json_round_trips() -> None:
    imported = import_legacy_calibration(LEGACY_DEVICE, LEGACY_CALIBRATION).calibration

    loaded = StandardCalibrationV2.from_dict(imported.to_dict())

    assert loaded == imported


def test_cli_imports_calibration_file_without_hardware(tmp_path: Path) -> None:
    _, calibration_path = write_legacy_files(tmp_path)

    completed = subprocess.run(
        [sys.executable, "-m", "tools.import_legacy_calibration", str(calibration_path)],
        cwd=Path.cwd(),
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0
    assert json.loads(completed.stdout) == EXPECTED_STANDARD
    assert completed.stderr == ""


def write_legacy_files(tmp_path: Path) -> tuple[Path, Path]:
    config_path = tmp_path / "config.json"
    calibration_path = tmp_path / "1.json"
    config_path.write_text(json.dumps(LEGACY_DEVICE, ensure_ascii=False), encoding="utf-8")
    calibration_path.write_text(
        json.dumps(LEGACY_CALIBRATION, ensure_ascii=False),
        encoding="utf-8",
    )
    return config_path, calibration_path
