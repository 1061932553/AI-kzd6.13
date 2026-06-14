"""Sequential script runner with pause, resume, cancel, retry, and history."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from itertools import count
from typing import Any

from ai_arm_control.actions import (
    SwipeAction,
    SwipeConfig,
    TouchActionStatus,
    execute_long_press,
    execute_multi_tap,
    execute_tap,
)
from ai_arm_control.coordinates.models import NormalizedPoint
from ai_arm_control.scripts.context import ScriptExecutionContext
from ai_arm_control.scripts.history import ScriptRunHistory
from ai_arm_control.scripts.schema import JsonObject, ScriptAction, ScriptStep, TouchScript
from ai_arm_control.scripts.state_machine import ScriptRunState, ScriptStateMachine

_RUN_IDS = count(1)
_DEVICE_LOCK = threading.Lock()
_ACTIVE_DEVICES: set[str] = set()


class ScriptRunnerError(RuntimeError):
    """Raised when a script cannot be run safely."""


@dataclass(frozen=True, slots=True)
class ScriptRunResult:
    run_id: str
    state: ScriptRunState
    history: ScriptRunHistory
    error: str | None = None

    @property
    def succeeded(self) -> bool:
        return self.state is ScriptRunState.COMPLETED

    def to_dict(self) -> JsonObject:
        return {
            "run_id": self.run_id,
            "state": self.state.value,
            "error": self.error,
            "history": self.history.to_dict(),
        }


class ScriptRunner:
    def __init__(
        self,
        *,
        script: TouchScript,
        context: ScriptExecutionContext,
        run_id: str | None = None,
    ) -> None:
        self.script = script
        self.context = context
        self.run_id = run_id or f"script-run-{next(_RUN_IDS):06d}"
        self.state_machine = ScriptStateMachine()
        self.history = ScriptRunHistory(run_id=self.run_id, device_id=context.device_id)
        self._pause_requested = threading.Event()
        self._resume_requested = threading.Event()
        self._cancel_requested = threading.Event()
        self._state_lock = threading.Lock()
        self._running_thread_id: int | None = None
        self._stop_requested = False
        self._resume_requested.set()

    @property
    def state(self) -> ScriptRunState:
        return self.state_machine.state

    @property
    def current_step_path(self) -> tuple[int, ...] | None:
        return self.history.current_step_path

    def pause(self) -> None:
        self._pause_requested.set()
        self._resume_requested.clear()

    def resume(self) -> None:
        self._pause_requested.clear()
        self._resume_requested.set()
        with self._state_lock:
            if self.state_machine.state is ScriptRunState.PAUSED:
                self._transition(ScriptRunState.RUNNING)

    def cancel(self) -> None:
        self._cancel_requested.set()
        self._resume_requested.set()
        with self._state_lock:
            if self.state_machine.state in {ScriptRunState.RUNNING, ScriptRunState.PAUSED}:
                self._transition(ScriptRunState.CANCELLING)

    def run(self) -> ScriptRunResult:
        if not _try_acquire_device(self.context.device_id):
            error = f"device {self.context.device_id} already has an active script"
            self.history.error = error
            self._transition(ScriptRunState.FAILED)
            self.context.history_store.save(self.history)
            return ScriptRunResult(self.run_id, self.state, self.history, error=error)
        try:
            self._running_thread_id = threading.get_ident()
            self._transition(ScriptRunState.RUNNING)
            for step in self.script.steps:
                if not self._before_next_step():
                    break
                if not self._execute_with_retry(step):
                    break
                if self._stop_requested:
                    break
            if self.state_machine.state is ScriptRunState.RUNNING:
                self._transition(ScriptRunState.COMPLETED)
        except Exception as exc:
            self.history.error = str(exc)
            if self.state_machine.state is not ScriptRunState.FAILED:
                self._transition(ScriptRunState.FAILED)
        finally:
            _release_device(self.context.device_id)
            self.context.history_store.save(self.history)
            self._running_thread_id = None
        return ScriptRunResult(
            self.run_id,
            self.state_machine.state,
            self.history,
            error=self.history.error,
        )

    def _before_next_step(self) -> bool:
        if self._cancel_requested.is_set():
            self.history.error = "script cancelled"
            self._transition(ScriptRunState.FAILED)
            return False
        if self._pause_requested.is_set():
            self._transition(ScriptRunState.PAUSED)
            self.context.history_store.save(self.history)
            self._resume_requested.wait()
            if self._cancel_requested.is_set():
                self.history.error = "script cancelled"
                self._transition(ScriptRunState.FAILED)
                return False
            self._transition(ScriptRunState.RUNNING)
        return True

    def _execute_with_retry(self, step: ScriptStep) -> bool:
        attempts = int(step.data.get("retry", 0)) + 1
        for attempt in range(1, attempts + 1):
            if self._cancel_requested.is_set():
                self.history.error = "script cancelled"
                self._transition(ScriptRunState.FAILED)
                return False
            record_index = self.history.record_start(step.index_path, step.action.value, attempt)
            self.context.history_store.save(self.history)
            started = time.monotonic()
            try:
                detail = self._execute_step(step)
                elapsed_ms = int((time.monotonic() - started) * 1000)
                timeout_error = self._timeout_error(step, elapsed_ms)
                if timeout_error is not None:
                    raise ScriptRunnerError(timeout_error)
            except Exception as exc:
                self.history.record_end(record_index, status="FAILED", error=str(exc))
                self.context.history_store.save(self.history)
                if attempt < attempts:
                    continue
                self.history.error = str(exc)
                self._transition(ScriptRunState.FAILED)
                return False
            self.history.record_end(record_index, status="SUCCEEDED", detail=detail)
            self.context.history_store.save(self.history)
            return True
        return False

    def _execute_step(self, step: ScriptStep) -> JsonObject:
        data = step.data
        match step.action:
            case ScriptAction.TAP:
                result = execute_tap(
                    NormalizedPoint(data["x"], data["y"]),
                    mapper=self.context.mapper,
                    arm=self.context.arm,
                    config=self.context.touch_config,
                    correction_grid=self.context.correction_grid,
                    sleeper=self.context.sleeper,
                )
                return self._detail_from_action_result(result)
            case ScriptAction.LONG_PRESS:
                result = execute_long_press(
                    NormalizedPoint(data["x"], data["y"]),
                    duration_ms=int(data["duration_ms"]),
                    mapper=self.context.mapper,
                    arm=self.context.arm,
                    config=self.context.touch_config,
                    correction_grid=self.context.correction_grid,
                    sleeper=self.context.sleeper,
                )
                return self._detail_from_action_result(result)
            case ScriptAction.MULTI_TAP:
                result = execute_multi_tap(
                    NormalizedPoint(data["x"], data["y"]),
                    count=int(data["count"]),
                    mapper=self.context.mapper,
                    arm=self.context.arm,
                    config=self.context.touch_config,
                    interval_ms=data.get("interval_ms"),
                    hold_ms=data.get("hold_ms"),
                    correction_grid=self.context.correction_grid,
                    sleeper=self.context.sleeper,
                )
                return self._detail_from_action_result(result)
            case ScriptAction.SWIPE:
                result = self._execute_swipe(data)
                return self._detail_from_action_result(result)
            case ScriptAction.WAIT:
                duration_ms = int(data["duration_ms"])
                self.context.sleeper.sleep_ms(duration_ms)
                return {"duration_ms": duration_ms}
            case ScriptAction.HOME:
                return self._execute_home()
            case ScriptAction.REPEAT:
                for _ in range(int(data["count"])):
                    for child in data["steps"]:
                        if not self._before_next_step():
                            raise ScriptRunnerError("script cancelled")
                        if not self._execute_with_retry(child):
                            raise ScriptRunnerError(self.history.error or "repeat child failed")
                return {"count": int(data["count"]), "child_steps": len(data["steps"])}
            case ScriptAction.STOP:
                self._stop_requested = True
                return {"stopped": True}
        raise ScriptRunnerError(f"unsupported action: {step.action}")

    def _execute_swipe(self, data: JsonObject):
        action = SwipeAction(
            mapper=self.context.mapper,
            arm=self.context.arm,
            touch_config=self.context.touch_config,
            swipe_config=SwipeConfig(
                duration_ms=int(data["duration_ms"]),
                point_count=int(data.get("points", 30)),
                start_delay_ms=int(data.get("start_delay_ms", 80)),
                end_hold_ms=int(data.get("end_hold_ms", 80)),
            ),
            correction_grid=self.context.correction_grid,
            sleeper=self.context.sleeper,
        )
        if "path" in data:
            return action.execute_polyline(
                [NormalizedPoint(point[0], point[1]) for point in data["path"]]
            )
        return action.execute_line(
            NormalizedPoint(data["start"][0], data["start"][1]),
            NormalizedPoint(data["end"][0], data["end"][1]),
        )

    def _execute_home(self) -> JsonObject:
        if self.context.home_action is not None:
            result = self.context.home_action()
            return {"home_result": result}
        home = getattr(self.context.arm, "home", None)
        if home is None:
            raise ScriptRunnerError("home action is not configured")
        result = home()
        return {"home_result": result}

    def _timeout_error(self, step: ScriptStep, elapsed_ms: int) -> str | None:
        timeout_ms = step.data.get("timeout_ms")
        if timeout_ms is None:
            return None
        if elapsed_ms > int(timeout_ms):
            return f"step timed out after {elapsed_ms}ms; timeout_ms={timeout_ms}"
        return None

    @staticmethod
    def _detail_from_action_result(result: Any) -> JsonObject:
        if getattr(result, "status", None) is TouchActionStatus.FAILED:
            raise ScriptRunnerError(getattr(result, "error", "action failed") or "action failed")
        to_dict = getattr(result, "to_dict", None)
        return to_dict() if callable(to_dict) else {"result": result}

    def _transition(self, state: ScriptRunState) -> None:
        self.state_machine.transition(state)
        self.history.set_state(state)
        self.context.history_store.save(self.history)


def _try_acquire_device(device_id: str) -> bool:
    with _DEVICE_LOCK:
        if device_id in _ACTIVE_DEVICES:
            return False
        _ACTIVE_DEVICES.add(device_id)
        return True


def _release_device(device_id: str) -> None:
    with _DEVICE_LOCK:
        _ACTIVE_DEVICES.discard(device_id)
