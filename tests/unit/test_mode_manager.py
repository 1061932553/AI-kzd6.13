from __future__ import annotations

from pathlib import Path

import pytest

from ai_arm_control.modes import (
    ControlMode,
    DeviceLock,
    DeviceLockError,
    ManualAppController,
    ManualAppError,
    ManualControlConfig,
    ModeManager,
)
from ai_arm_control.modes.manual_app import DEFAULT_MANUAL_APP_DIRECTORY


class FakeScriptController:
    def __init__(self, *, wait_result: bool = True) -> None:
        self.wait_result = wait_result
        self.calls: list[str] = []

    def stop_accepting_new_scripts(self) -> None:
        self.calls.append("stop_accepting_new_scripts")

    def wait_current_action_done(self) -> bool:
        self.calls.append("wait_current_action_done")
        return self.wait_result

    def stop_script(self) -> None:
        self.calls.append("stop_script")

    def reject_new_actions(self) -> None:
        self.calls.append("reject_new_actions")

    def allow_new_actions(self) -> None:
        self.calls.append("allow_new_actions")


class FakeDeviceController:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def pen_up(self) -> object:
        self.calls.append("pen_up")
        return None

    def safe_home(self) -> object:
        self.calls.append("safe_home")
        return None

    def disconnect(self) -> object:
        self.calls.append("disconnect")
        return None

    def connect(self) -> object:
        self.calls.append("connect")
        return None

    def load_calibration(self) -> object:
        self.calls.append("load_calibration")
        return None

    def home(self) -> object:
        self.calls.append("home")
        return None

    def self_check_center(self) -> object:
        self.calls.append("self_check_center")
        return None


class FakeLauncher:
    def __init__(self) -> None:
        self.running = False
        self.starts: list[tuple[Path, str]] = []

    def start(self, app_directory: Path, executable: str) -> None:
        self.starts.append((app_directory, executable))
        self.running = True

    def is_running(self) -> bool:
        return self.running


def build_manager(
    *,
    wait_result: bool = True,
    launcher: FakeLauncher | None = None,
) -> tuple[ModeManager, FakeScriptController, FakeDeviceController, FakeLauncher]:
    script = FakeScriptController(wait_result=wait_result)
    device = FakeDeviceController()
    launcher = launcher or FakeLauncher()
    manual_app = ManualAppController(ManualControlConfig(), launcher=launcher)
    manager = ModeManager(
        "ARM-001",
        script_controller=script,
        device_controller=device,
        manual_app=manual_app,
    )
    return manager, script, device, launcher


def test_device_lock_rejects_second_owner() -> None:
    lock = DeviceLock("ARM-001")
    snapshot = lock.acquire("AUTO")

    assert snapshot.owner == "AUTO"
    with pytest.raises(DeviceLockError, match="already owned"):
        lock.acquire("MANUAL")


def test_manual_control_config_keeps_path_as_configuration_only() -> None:
    config = ManualControlConfig.from_dict({"enabled": True, "executable": ""})

    assert config.app_directory == Path(DEFAULT_MANUAL_APP_DIRECTORY)
    assert "main软件发客户-20260531" in str(config.app_directory)
    assert config.executable == ""


def test_manual_app_requires_injected_launcher() -> None:
    controller = ManualAppController(ManualControlConfig())

    with pytest.raises(ManualAppError, match="launcher is not configured"):
        controller.start()


def test_start_auto_acquires_lock_and_runs_self_check() -> None:
    manager, script, device, _launcher = build_manager()

    record = manager.start_auto()

    assert record.status == "SUCCEEDED"
    assert manager.mode is ControlMode.AUTO
    assert manager.device_lock.snapshot().owner == "AUTO"
    assert device.calls == ["connect", "load_calibration", "home", "self_check_center"]
    assert script.calls == ["allow_new_actions"]


def test_enter_manual_stops_auto_and_releases_device_to_manual() -> None:
    manager, script, device, launcher = build_manager()
    manager.start_auto()
    script.calls.clear()
    device.calls.clear()

    record = manager.enter_manual()

    assert record.status == "SUCCEEDED"
    assert manager.mode is ControlMode.MANUAL
    assert manager.device_lock.snapshot().owner == "MANUAL"
    assert launcher.running is True
    assert script.calls == [
        "stop_accepting_new_scripts",
        "wait_current_action_done",
        "stop_script",
        "reject_new_actions",
    ]
    assert device.calls == ["pen_up", "safe_home", "disconnect"]


def test_auto_actions_are_rejected_in_manual_mode() -> None:
    manager, _script, _device, _launcher = build_manager()
    manager.start_auto()
    manager.enter_manual()

    with pytest.raises(RuntimeError, match="automatic action rejected"):
        manager.require_auto_owner()


def test_return_auto_requires_manual_app_to_be_closed() -> None:
    manager, _script, _device, _launcher = build_manager()
    manager.start_auto()
    manager.enter_manual()

    record = manager.return_auto()

    assert record.status == "FAILED"
    assert manager.mode is ControlMode.FAULT
    assert record.error == "manual app is still running"


def test_return_auto_reconnects_after_manual_app_closed() -> None:
    manager, script, device, launcher = build_manager()
    manager.start_auto()
    manager.enter_manual()
    launcher.running = False
    script.calls.clear()
    device.calls.clear()

    record = manager.return_auto()

    assert record.status == "SUCCEEDED"
    assert manager.mode is ControlMode.AUTO
    assert manager.device_lock.snapshot().owner == "AUTO"
    assert device.calls == ["connect", "load_calibration", "home", "self_check_center"]
    assert script.calls == ["allow_new_actions"]


def test_enter_manual_timeout_enters_fault_and_lifts_pen() -> None:
    manager, script, device, _launcher = build_manager(wait_result=False)
    manager.start_auto()
    script.calls.clear()
    device.calls.clear()

    record = manager.enter_manual()

    assert record.status == "FAILED"
    assert manager.mode is ControlMode.FAULT
    assert record.error == "timed out waiting current action"
    assert "reject_new_actions" in script.calls
    assert device.calls == ["pen_up"]
