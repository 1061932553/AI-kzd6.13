"""Runtime dependencies for script execution."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from ai_arm_control.actions.models import TouchActionConfig, TouchArmAPI, TouchSleeper
from ai_arm_control.actions.tap import SystemSleeper
from ai_arm_control.calibration.correction_grid import CorrectionGrid
from ai_arm_control.coordinates.mapper import CoordinateMapper
from ai_arm_control.scripts.history import InMemoryScriptHistoryStore, ScriptHistoryStore


@dataclass(slots=True)
class ScriptExecutionContext:
    device_id: str
    mapper: CoordinateMapper
    arm: TouchArmAPI
    touch_config: TouchActionConfig = field(default_factory=TouchActionConfig)
    sleeper: TouchSleeper = field(default_factory=SystemSleeper)
    history_store: ScriptHistoryStore = field(default_factory=InMemoryScriptHistoryStore)
    correction_grid: CorrectionGrid | None = None
    home_action: Callable[[], object] | None = None
