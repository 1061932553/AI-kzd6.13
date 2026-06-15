"""AUTO/MANUAL mode manager with lock ownership and safe handoff sequence."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Protocol

from ai_arm_control.modes.device_lock import DeviceLock
from ai_arm_control.modes.manual_app import ManualAppController


class ControlMode(StrEnum):
    AUTO = "AUTO"
    MANUAL = "MANUAL"
    SWITCHING = "SWITCHING"
    OFFLINE = "OFFLINE"
    FAULT = "FAULT"


class AutoScriptController(Protocol):
    def stop_accepting_new_scripts(self) -> None: ...

    def wait_current_action_done(self) -> bool: ...

    def stop_script(self) -> None: ...

    def reject_new_actions(self) -> None: ...

    def allow_new_actions(self) -> None: ...


class ModeDeviceController(Protocol):
    def pen_up(self) -> object: ...

    def safe_home(self) -> object: ...

    def disconnect(self) -> object: ...

    def connect(self) -> object: ...

    def load_calibration(self) -> object: ...

    def home(self) -> object: ...

    def self_check_center(self) -> object: ...


@dataclass(frozen=True, slots=True)
class ModeTransitionRecord:
    from_mode: ControlMode
    to_mode: ControlMode
    status: str
    steps: list[str]
    error: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "from_mode": self.from_mode.value,
            "to_mode": self.to_mode.value,
            "status": self.status,
            "steps": list(self.steps),
            "error": self.error,
        }


@dataclass(slots=True)
class ModeManager:
    device_id: str
    script_controller: AutoScriptController
    device_controller: ModeDeviceController
    manual_app: ManualAppController
    device_lock: DeviceLock = field(init=False)
    mode: ControlMode = ControlMode.OFFLINE
    history: list[ModeTransitionRecord] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.device_lock = DeviceLock(self.device_id)

    def start_auto(self) -> ModeTransitionRecord:
        previous = self.mode
        steps: list[str] = []
        self.mode = ControlMode.SWITCHING
        try:
            self.device_lock.acquire("AUTO")
            steps.append("lock_auto")
            if not self.manual_app.is_closed():
                raise RuntimeError("manual app is still running")
            steps.append("manual_app_closed")
            self.device_controller.connect()
            steps.append("connect")
            self.device_controller.load_calibration()
            steps.append("load_calibration")
            self.device_controller.home()
            steps.append("home")
            self.device_controller.self_check_center()
            steps.append("self_check_center")
            self.script_controller.allow_new_actions()
            steps.append("allow_new_actions")
            self.mode = ControlMode.AUTO
            return self._record(previous, self.mode, "SUCCEEDED", steps)
        except Exception as exc:
            self.mode = ControlMode.FAULT
            self.script_controller.reject_new_actions()
            try:
                self.device_lock.release("AUTO")
            except Exception:
                pass
            return self._record(previous, self.mode, "FAILED", steps, error=str(exc))

    def enter_manual(self, *, launch_manual_app: bool = True) -> ModeTransitionRecord:
        previous = self.mode
        steps: list[str] = []
        self.mode = ControlMode.SWITCHING
        try:
            self.device_lock.require_owner("AUTO")
            steps.append("lock_verified_auto")
            self.script_controller.stop_accepting_new_scripts()
            steps.append("stop_accepting_new_scripts")
            if not self.script_controller.wait_current_action_done():
                raise RuntimeError("timed out waiting current action")
            steps.append("wait_current_action_done")
            self.script_controller.stop_script()
            steps.append("stop_script")
            self.script_controller.reject_new_actions()
            steps.append("reject_new_actions")
            self.device_controller.pen_up()
            steps.append("pen_up")
            self.device_controller.safe_home()
            steps.append("safe_home")
            self.device_controller.disconnect()
            steps.append("disconnect")
            self.device_lock.release("AUTO")
            steps.append("release_auto_lock")
            self.device_lock.acquire("MANUAL")
            steps.append("lock_manual")
            if launch_manual_app:
                self.manual_app.start()
                steps.append("start_manual_app")
            self.mode = ControlMode.MANUAL
            return self._record(previous, self.mode, "SUCCEEDED", steps)
        except Exception as exc:
            self.mode = ControlMode.FAULT
            self.script_controller.reject_new_actions()
            try:
                self.device_controller.pen_up()
            except Exception:
                pass
            return self._record(previous, self.mode, "FAILED", steps, error=str(exc))

    def return_auto(self) -> ModeTransitionRecord:
        previous = self.mode
        steps: list[str] = []
        self.mode = ControlMode.SWITCHING
        try:
            self.device_lock.require_owner("MANUAL")
            steps.append("lock_verified_manual")
            if not self.manual_app.is_closed():
                raise RuntimeError("manual app is still running")
            steps.append("manual_app_closed")
            self.device_lock.release("MANUAL")
            steps.append("release_manual_lock")
            self.device_lock.acquire("AUTO")
            steps.append("lock_auto")
            self.device_controller.connect()
            steps.append("connect")
            self.device_controller.load_calibration()
            steps.append("load_calibration")
            self.device_controller.home()
            steps.append("home")
            self.device_controller.self_check_center()
            steps.append("self_check_center")
            self.script_controller.allow_new_actions()
            steps.append("allow_new_actions")
            self.mode = ControlMode.AUTO
            return self._record(previous, self.mode, "SUCCEEDED", steps)
        except Exception as exc:
            self.mode = ControlMode.FAULT
            self.script_controller.reject_new_actions()
            return self._record(previous, self.mode, "FAILED", steps, error=str(exc))

    def require_auto_owner(self) -> None:
        if self.mode is not ControlMode.AUTO:
            raise RuntimeError(f"automatic action rejected while mode is {self.mode.value}")
        self.device_lock.require_owner("AUTO")

    def _record(
        self,
        from_mode: ControlMode,
        to_mode: ControlMode,
        status: str,
        steps: list[str],
        *,
        error: str | None = None,
    ) -> ModeTransitionRecord:
        record = ModeTransitionRecord(from_mode, to_mode, status, list(steps), error)
        self.history.append(record)
        return record
