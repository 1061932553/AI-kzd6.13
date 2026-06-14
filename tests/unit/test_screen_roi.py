from __future__ import annotations

from pathlib import Path

import pytest

from ai_arm_control.simulators import CameraSimulator, CameraSimulatorConfig
from ai_arm_control.vision import CameraService, CameraServiceConfig, SimulatorFrameSource
from ai_arm_control.vision.screen_roi import ScreenROIExtractor, save_debug_ppm


def test_screen_roi_extracts_configured_size() -> None:
    simulator = CameraSimulator(CameraSimulatorConfig(width=10, height=8))
    simulator.open()
    frame = simulator.capture_frame()

    cropped = ScreenROIExtractor((2, 1, 7, 5)).extract(frame)

    assert cropped.width == 5
    assert cropped.height == 4
    assert cropped.metadata["crop_rect"] == (2, 1, 7, 5)


def test_screen_roi_rejects_out_of_bounds() -> None:
    simulator = CameraSimulator(CameraSimulatorConfig(width=10, height=8))
    simulator.open()
    frame = simulator.capture_frame()

    with pytest.raises(ValueError):
        ScreenROIExtractor((0, 0, 11, 8)).extract(frame)


def test_camera_service_reads_continuous_frames_and_roi() -> None:
    simulator = CameraSimulator(CameraSimulatorConfig(width=10, height=8))
    service = CameraService(
        source=SimulatorFrameSource(simulator, device_id="ARM-TEST"),
        config=CameraServiceConfig(device_id="ARM-TEST", screen_roi=(2, 1, 7, 5)),
    )
    service.open()

    frames = service.read_frames(3)
    roi = service.capture_screen_roi()
    service.close()

    assert [frame.frame_index for frame in frames] == [1, 2, 3]
    assert roi.width == 5
    assert roi.height == 4
    assert simulator.get_history()[-1].action == "close"


def test_debug_screenshot_contains_device_and_time(tmp_path: Path) -> None:
    simulator = CameraSimulator(CameraSimulatorConfig(width=4, height=4))
    simulator.open()
    frame = simulator.capture_frame()

    path = save_debug_ppm(frame, tmp_path, device_id="ARM-001")

    assert "ARM-001" in path.name
    assert f"f{frame.frame_index}" in path.name
    content = path.read_bytes()
    assert b"device_id=ARM-001" in content
    assert frame.data in content


def test_camera_service_reconnects_after_disconnect(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level("INFO")
    simulator = CameraSimulator(CameraSimulatorConfig(width=4, height=4))
    service = CameraService(
        source=SimulatorFrameSource(simulator),
        config=CameraServiceConfig(device_id="ARM-TEST", screen_roi=(0, 0, 4, 4)),
    )
    service.open()
    service.close()

    frame = service.read_frame()

    assert frame.width == 4
    assert any("reconnected" in record.message for record in caplog.records)
