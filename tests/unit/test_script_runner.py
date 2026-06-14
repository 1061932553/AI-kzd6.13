from __future__ import annotations

import threading
import time
from pathlib import Path

from ai_arm_control.coordinates import Bounds2D, CoordinateMapper, CoordinateMapperConfig, ScreenROI
from ai_arm_control.scripts import parse_script
from ai_arm_control.scripts.context import ScriptExecutionContext
from ai_arm_control.scripts.history import InMemoryScriptHistoryStore, JsonScriptHistoryStore
from ai_arm_control.scripts.runner import ScriptRunner
from ai_arm_control.scripts.state_machine import ScriptRunState


class FakeArm:
    def __init__(self, *, fail_moves: int = 0) -> None:
        self.calls: list[tuple[str, tuple[float, ...]]] = []
        self.fail_moves = fail_moves
        self.move_attempts = 0

    def move_xy(self, x: float, y: float) -> object:
        self.move_attempts += 1
        self.calls.append(("move_xy", (x, y)))
        if self.move_attempts <= self.fail_moves:
            raise RuntimeError("simulated move failure")
        return {"ok": True}

    def pen_down(self, z: float) -> object:
        self.calls.append(("pen_down", (z,)))
        return {"ok": True}

    def pen_up(self) -> object:
        self.calls.append(("pen_up", ()))
        return {"ok": True}

    def home(self) -> object:
        self.calls.append(("home", ()))
        return {"ok": True}


class FakeSleeper:
    def __init__(self) -> None:
        self.durations: list[int] = []

    def sleep_ms(self, duration_ms: int) -> None:
        self.durations.append(duration_ms)


class BlockingSleeper(FakeSleeper):
    def __init__(self) -> None:
        super().__init__()
        self.entered = threading.Event()
        self.release = threading.Event()

    def sleep_ms(self, duration_ms: int) -> None:
        self.durations.append(duration_ms)
        self.entered.set()
        self.release.wait(timeout=2)


class SlowSleeper(FakeSleeper):
    def sleep_ms(self, duration_ms: int) -> None:
        self.durations.append(duration_ms)
        time.sleep(0.003)


def mapper() -> CoordinateMapper:
    return CoordinateMapper(
        CoordinateMapperConfig(
            screen_roi=ScreenROI.from_sequence([0, 0, 100, 100]),
            arm_bounds=Bounds2D(0, 100, 0, 100),
        )
    )


def context(
    *,
    arm: FakeArm | None = None,
    sleeper: FakeSleeper | None = None,
    device_id: str = "SIM-001",
    store: InMemoryScriptHistoryStore | JsonScriptHistoryStore | None = None,
) -> ScriptExecutionContext:
    return ScriptExecutionContext(
        device_id=device_id,
        mapper=mapper(),
        arm=arm or FakeArm(),
        sleeper=sleeper or FakeSleeper(),
        history_store=store or InMemoryScriptHistoryStore(),
    )


def script_with_steps(steps: list[dict[str, object]]):
    return parse_script({"script_version": "1.0", "steps": steps})


def test_runner_executes_steps_in_order_and_records_history() -> None:
    arm = FakeArm()
    runner = ScriptRunner(
        script=script_with_steps(
            [
                {"action": "tap", "x": 0.5, "y": 0.5},
                {"action": "wait", "duration_ms": 10},
                {"action": "home"},
            ]
        ),
        context=context(arm=arm),
    )

    result = runner.run()

    assert result.state is ScriptRunState.COMPLETED
    assert result.succeeded
    assert [record.status for record in result.history.records] == [
        "SUCCEEDED",
        "SUCCEEDED",
        "SUCCEEDED",
    ]
    assert arm.calls[-1] == ("home", ())


def test_pause_waits_before_sending_next_action_and_resume_continues() -> None:
    arm = FakeArm()
    sleeper = BlockingSleeper()
    runner = ScriptRunner(
        script=script_with_steps(
            [
                {"action": "tap", "x": 0.1, "y": 0.1},
                {"action": "tap", "x": 0.2, "y": 0.2},
            ]
        ),
        context=context(arm=arm, sleeper=sleeper),
    )
    thread = threading.Thread(target=runner.run)

    thread.start()
    assert sleeper.entered.wait(timeout=2)
    runner.pause()
    sleeper.release.set()
    deadline = time.monotonic() + 2
    while runner.state is not ScriptRunState.PAUSED and time.monotonic() < deadline:
        time.sleep(0.01)

    move_count_while_paused = [call[0] for call in arm.calls].count("move_xy")
    assert runner.state is ScriptRunState.PAUSED
    assert move_count_while_paused == 1

    runner.resume()
    thread.join(timeout=2)

    assert runner.state is ScriptRunState.COMPLETED
    assert [call[0] for call in arm.calls].count("move_xy") == 2


def test_cancel_prevents_following_steps() -> None:
    arm = FakeArm()
    sleeper = BlockingSleeper()
    runner = ScriptRunner(
        script=script_with_steps(
            [
                {"action": "tap", "x": 0.1, "y": 0.1},
                {"action": "tap", "x": 0.2, "y": 0.2},
            ]
        ),
        context=context(arm=arm, sleeper=sleeper),
    )
    thread = threading.Thread(target=runner.run)

    thread.start()
    assert sleeper.entered.wait(timeout=2)
    runner.cancel()
    sleeper.release.set()
    thread.join(timeout=2)

    assert runner.state is ScriptRunState.FAILED
    assert runner.history.error == "script cancelled"
    assert [call[0] for call in arm.calls].count("move_xy") == 1


def test_action_failure_retries_then_succeeds() -> None:
    arm = FakeArm(fail_moves=1)
    runner = ScriptRunner(
        script=script_with_steps([{"action": "tap", "x": 0.5, "y": 0.5, "retry": 1}]),
        context=context(arm=arm),
    )

    result = runner.run()

    assert result.state is ScriptRunState.COMPLETED
    assert [record.status for record in result.history.records] == ["FAILED", "SUCCEEDED"]
    assert [call[0] for call in arm.calls].count("move_xy") == 2


def test_retry_exhaustion_enters_failed() -> None:
    runner = ScriptRunner(
        script=script_with_steps([{"action": "tap", "x": 0.5, "y": 0.5, "retry": 1}]),
        context=context(arm=FakeArm(fail_moves=5)),
    )

    result = runner.run()

    assert result.state is ScriptRunState.FAILED
    assert len(result.history.records) == 2
    assert all(record.status == "FAILED" for record in result.history.records)


def test_timeout_marks_step_failed() -> None:
    runner = ScriptRunner(
        script=script_with_steps([{"action": "tap", "x": 0.5, "y": 0.5, "timeout_ms": 1}]),
        context=context(sleeper=SlowSleeper()),
    )

    result = runner.run()

    assert result.state is ScriptRunState.FAILED
    assert "timed out" in (result.error or "")


def test_same_device_cannot_run_two_scripts_concurrently() -> None:
    sleeper = BlockingSleeper()
    first = ScriptRunner(
        script=script_with_steps([{"action": "wait", "duration_ms": 100}]),
        context=context(device_id="SIM-SHARED", sleeper=sleeper),
    )
    second = ScriptRunner(
        script=script_with_steps([{"action": "home"}]),
        context=context(device_id="SIM-SHARED"),
    )
    thread = threading.Thread(target=first.run)

    thread.start()
    assert sleeper.entered.wait(timeout=2)
    second_result = second.run()
    sleeper.release.set()
    thread.join(timeout=2)

    assert second_result.state is ScriptRunState.FAILED
    assert "already has an active script" in (second_result.error or "")


def test_json_history_store_persists_current_state(tmp_path: Path) -> None:
    store = JsonScriptHistoryStore(tmp_path)
    runner = ScriptRunner(
        script=script_with_steps([{"action": "wait", "duration_ms": 1}]),
        context=context(store=store),
        run_id="persisted-run",
    )

    result = runner.run()
    loaded = store.load("persisted-run")

    assert result.state is ScriptRunState.COMPLETED
    assert loaded is not None
    assert loaded.state is ScriptRunState.COMPLETED
    assert loaded.records[0].finished_at is not None
