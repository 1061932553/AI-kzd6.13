"""Persistent script run history."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ai_arm_control.scripts.state_machine import ScriptRunState

JsonObject = dict[str, Any]


def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


@dataclass(frozen=True, slots=True)
class ScriptStepRecord:
    step_path: tuple[int, ...]
    action: str
    attempt: int
    started_at: str
    finished_at: str | None = None
    status: str = "RUNNING"
    error: str | None = None
    detail: JsonObject = field(default_factory=dict)

    def to_dict(self) -> JsonObject:
        return {
            "step_path": list(self.step_path),
            "action": self.action,
            "attempt": self.attempt,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "status": self.status,
            "error": self.error,
            "detail": dict(self.detail),
        }

    @classmethod
    def from_dict(cls, data: JsonObject) -> ScriptStepRecord:
        return cls(
            step_path=tuple(data["step_path"]),
            action=data["action"],
            attempt=int(data["attempt"]),
            started_at=data["started_at"],
            finished_at=data.get("finished_at"),
            status=data.get("status", "RUNNING"),
            error=data.get("error"),
            detail=dict(data.get("detail", {})),
        )


@dataclass(slots=True)
class ScriptRunHistory:
    run_id: str
    device_id: str
    state: ScriptRunState = ScriptRunState.IDLE
    current_step_path: tuple[int, ...] | None = None
    started_at: str = field(default_factory=utc_now_iso)
    finished_at: str | None = None
    records: list[ScriptStepRecord] = field(default_factory=list)
    error: str | None = None

    def record_start(self, step_path: tuple[int, ...], action: str, attempt: int) -> int:
        self.current_step_path = step_path
        self.records.append(
            ScriptStepRecord(
                step_path=step_path,
                action=action,
                attempt=attempt,
                started_at=utc_now_iso(),
            )
        )
        return len(self.records) - 1

    def record_end(
        self,
        record_index: int,
        *,
        status: str,
        error: str | None = None,
        detail: JsonObject | None = None,
    ) -> None:
        record = self.records[record_index]
        self.records[record_index] = ScriptStepRecord(
            step_path=record.step_path,
            action=record.action,
            attempt=record.attempt,
            started_at=record.started_at,
            finished_at=utc_now_iso(),
            status=status,
            error=error,
            detail=detail or {},
        )

    def set_state(self, state: ScriptRunState) -> None:
        self.state = state
        if state in {ScriptRunState.COMPLETED, ScriptRunState.FAILED}:
            self.finished_at = utc_now_iso()

    def to_dict(self) -> JsonObject:
        return {
            "run_id": self.run_id,
            "device_id": self.device_id,
            "state": self.state.value,
            "current_step_path": (
                list(self.current_step_path) if self.current_step_path is not None else None
            ),
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "error": self.error,
            "records": [record.to_dict() for record in self.records],
        }

    @classmethod
    def from_dict(cls, data: JsonObject) -> ScriptRunHistory:
        state = ScriptRunState(data.get("state", ScriptRunState.IDLE.value))
        current = data.get("current_step_path")
        return cls(
            run_id=data["run_id"],
            device_id=data["device_id"],
            state=state,
            current_step_path=tuple(current) if current is not None else None,
            started_at=data["started_at"],
            finished_at=data.get("finished_at"),
            records=[ScriptStepRecord.from_dict(item) for item in data.get("records", [])],
            error=data.get("error"),
        )


class ScriptHistoryStore:
    def save(self, history: ScriptRunHistory) -> None:
        raise NotImplementedError

    def load(self, run_id: str) -> ScriptRunHistory | None:
        raise NotImplementedError


class InMemoryScriptHistoryStore(ScriptHistoryStore):
    def __init__(self) -> None:
        self.saved: dict[str, ScriptRunHistory] = {}

    def save(self, history: ScriptRunHistory) -> None:
        self.saved[history.run_id] = ScriptRunHistory.from_dict(history.to_dict())

    def load(self, run_id: str) -> ScriptRunHistory | None:
        history = self.saved.get(run_id)
        return None if history is None else ScriptRunHistory.from_dict(history.to_dict())


class JsonScriptHistoryStore(ScriptHistoryStore):
    def __init__(self, directory: str | Path) -> None:
        self.directory = Path(directory)

    def save(self, history: ScriptRunHistory) -> None:
        self.directory.mkdir(parents=True, exist_ok=True)
        path = self.directory / f"{history.run_id}.json"
        path.write_text(
            json.dumps(history.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def load(self, run_id: str) -> ScriptRunHistory | None:
        path = self.directory / f"{run_id}.json"
        if not path.exists():
            return None
        return ScriptRunHistory.from_dict(json.loads(path.read_text(encoding="utf-8")))
