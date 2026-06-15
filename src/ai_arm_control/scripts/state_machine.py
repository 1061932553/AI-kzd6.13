"""Script runner state machine."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class ScriptRunState(StrEnum):
    IDLE = "IDLE"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    CANCELLING = "CANCELLING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


_ALLOWED_TRANSITIONS = {
    ScriptRunState.IDLE: {ScriptRunState.RUNNING, ScriptRunState.FAILED},
    ScriptRunState.RUNNING: {
        ScriptRunState.PAUSED,
        ScriptRunState.CANCELLING,
        ScriptRunState.COMPLETED,
        ScriptRunState.FAILED,
    },
    ScriptRunState.PAUSED: {
        ScriptRunState.RUNNING,
        ScriptRunState.CANCELLING,
        ScriptRunState.FAILED,
    },
    ScriptRunState.CANCELLING: {ScriptRunState.FAILED},
    ScriptRunState.COMPLETED: set(),
    ScriptRunState.FAILED: set(),
}


class ScriptStateError(RuntimeError):
    """Raised when a runner state transition is invalid."""


@dataclass(slots=True)
class ScriptStateMachine:
    state: ScriptRunState = ScriptRunState.IDLE

    def transition(self, new_state: ScriptRunState) -> None:
        if new_state is self.state:
            return
        if new_state not in _ALLOWED_TRANSITIONS[self.state]:
            raise ScriptStateError(
                f"cannot transition from {self.state.value} to {new_state.value}"
            )
        self.state = new_state

    @property
    def is_terminal(self) -> bool:
        return self.state in {ScriptRunState.COMPLETED, ScriptRunState.FAILED}
