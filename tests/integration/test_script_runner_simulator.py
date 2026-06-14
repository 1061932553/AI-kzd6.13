from __future__ import annotations

from ai_arm_control.coordinates import Bounds2D, CoordinateMapper, CoordinateMapperConfig, ScreenROI
from ai_arm_control.scripts import ScriptRunner, parse_script
from ai_arm_control.scripts.context import ScriptExecutionContext
from ai_arm_control.scripts.history import InMemoryScriptHistoryStore
from ai_arm_control.scripts.state_machine import ScriptRunState


class SimulatorArm:
    def __init__(self) -> None:
        self.position = {"x": 0.0, "y": 0.0, "z": 0.0}
        self.calls: list[str] = []

    def move_xy(self, x: float, y: float) -> object:
        self.position["x"] = x
        self.position["y"] = y
        self.calls.append(f"move_xy:{round(x, 3)}:{round(y, 3)}")
        return dict(self.position)

    def pen_down(self, z: float) -> object:
        self.position["z"] = z
        self.calls.append(f"pen_down:{z}")
        return dict(self.position)

    def pen_up(self) -> object:
        self.position["z"] = 0.0
        self.calls.append("pen_up")
        return dict(self.position)

    def home(self) -> object:
        self.position = {"x": 0.0, "y": 0.0, "z": 0.0}
        self.calls.append("home")
        return dict(self.position)


class NoDelaySleeper:
    def sleep_ms(self, duration_ms: int) -> None:
        return None


def test_script_runner_completes_full_script_on_simulated_arm() -> None:
    script = parse_script(
        {
            "script_version": "1.0",
            "steps": [
                {"action": "tap", "x": 0.5, "y": 0.3},
                {"action": "wait", "duration_ms": 1000},
                {"action": "long_press", "x": 0.6, "y": 0.5, "duration_ms": 1500},
                {"action": "multi_tap", "x": 0.4, "y": 0.7, "count": 3},
                {
                    "action": "swipe",
                    "start": [0.5, 0.8],
                    "end": [0.5, 0.2],
                    "duration_ms": 600,
                    "points": 20,
                },
                {
                    "action": "repeat",
                    "count": 2,
                    "steps": [{"action": "tap", "x": 0.2, "y": 0.2}],
                },
                {"action": "home"},
                {"action": "stop"},
                {"action": "tap", "x": 0.9, "y": 0.9},
            ],
        }
    )
    arm = SimulatorArm()
    context = ScriptExecutionContext(
        device_id="SIM-INTEGRATION",
        mapper=CoordinateMapper(
            CoordinateMapperConfig(
                screen_roi=ScreenROI.from_sequence([0, 0, 100, 100]),
                arm_bounds=Bounds2D(0, 100, 0, 100),
            )
        ),
        arm=arm,
        sleeper=NoDelaySleeper(),
        history_store=InMemoryScriptHistoryStore(),
    )

    result = ScriptRunner(script=script, context=context).run()

    assert result.state is ScriptRunState.COMPLETED
    assert result.succeeded
    assert arm.calls[-1] == "home"
    assert result.history.records[-1].action == "stop"
    assert not any(call == "move_xy:90.0:90.0" for call in arm.calls)
