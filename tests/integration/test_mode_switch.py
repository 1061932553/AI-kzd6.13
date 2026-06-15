from __future__ import annotations

from pathlib import Path

from ai_arm_control.modes import ManualAppController, ManualControlConfig, ModeManager


class FakeScriptController:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def stop_accepting_new_scripts(self) -> None:
        self.calls.append("stop_accepting_new_scripts")

    def wait_current_action_done(self) -> bool:
        self.calls.append("wait_current_action_done")
        return True

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


def test_auto_manual_auto_mode_switch_simulation() -> None:
    script = FakeScriptController()
    device = FakeDeviceController()
    launcher = FakeLauncher()
    manager = ModeManager(
        "ARM-001",
        script_controller=script,
        device_controller=device,
        manual_app=ManualAppController(ManualControlConfig(), launcher=launcher),
    )

    start = manager.start_auto()
    to_manual = manager.enter_manual()
    launcher.running = False
    to_auto = manager.return_auto()

    assert [start.status, to_manual.status, to_auto.status] == [
        "SUCCEEDED",
        "SUCCEEDED",
        "SUCCEEDED",
    ]
    assert launcher.starts == [
        (Path(ManualControlConfig().app_directory), ManualControlConfig().executable)
    ]
    assert script.calls == [
        "allow_new_actions",
        "stop_accepting_new_scripts",
        "wait_current_action_done",
        "stop_script",
        "reject_new_actions",
        "allow_new_actions",
    ]
    assert device.calls == [
        "connect",
        "load_calibration",
        "home",
        "self_check_center",
        "pen_up",
        "safe_home",
        "disconnect",
        "connect",
        "load_calibration",
        "home",
        "self_check_center",
    ]
    assert [record.to_dict()["status"] for record in manager.history] == [
        "SUCCEEDED",
        "SUCCEEDED",
        "SUCCEEDED",
    ]
