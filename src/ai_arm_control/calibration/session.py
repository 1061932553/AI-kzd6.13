"""Offline-first 16-point calibration session state."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Protocol
from uuid import uuid4

from ai_arm_control.calibration.grid_generator import CalibrationGridPoint, generate_4x4_grid
from ai_arm_control.calibration.touch_capture import TouchSample, utc_now_iso
from ai_arm_control.coordinates.mapper import CoordinateMapper
from ai_arm_control.coordinates.models import NormalizedPoint


class CalibrationSessionError(RuntimeError):
    """Raised when a calibration session cannot continue safely."""


class CalibrationSessionStatus(StrEnum):
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class CalibrationPointStatus(StrEnum):
    PENDING = "pending"
    ACTION_SENT = "action_sent"
    COMPLETED = "completed"


class CalibrationPointExecutor(Protocol):
    def tap_point(
        self,
        point: CalibrationGridPoint,
        arm_x: float,
        arm_y: float,
    ) -> dict[str, object]: ...


@dataclass(slots=True)
class CalibrationPointRecord:
    point: CalibrationGridPoint
    status: CalibrationPointStatus = CalibrationPointStatus.PENDING
    actual: NormalizedPoint | None = None
    touch_source: str | None = None
    action_receipts: list[dict[str, object]] = field(default_factory=list)
    updated_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> dict[str, object]:
        return {
            "point": self.point.to_dict(),
            "status": self.status.value,
            "actual": None if self.actual is None else {"x": self.actual.x, "y": self.actual.y},
            "touch_source": self.touch_source,
            "action_receipts": list(self.action_receipts),
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> CalibrationPointRecord:
        actual = data.get("actual")
        actual_data = None if actual is None else _expect_dict(actual, "actual")
        return cls(
            point=CalibrationGridPoint.from_dict(_expect_dict(data.get("point"), "point")),
            status=CalibrationPointStatus(str(data["status"])),
            actual=None
            if actual_data is None
            else NormalizedPoint(actual_data["x"], actual_data["y"]),
            touch_source=None if data.get("touch_source") is None else str(data["touch_source"]),
            action_receipts=list(data.get("action_receipts", [])),
            updated_at=str(data["updated_at"]),
        )


@dataclass(slots=True)
class CalibrationSession:
    device_id: str
    records: list[CalibrationPointRecord]
    session_id: str = field(default_factory=lambda: f"cal-{uuid4().hex[:12]}")
    status: CalibrationSessionStatus = CalibrationSessionStatus.READY
    created_at: str = field(default_factory=utc_now_iso)
    updated_at: str = field(default_factory=utc_now_iso)
    raw_events: list[dict[str, object]] = field(default_factory=list)

    @classmethod
    def create_4x4(cls, *, device_id: str, margin: float = 0.1) -> CalibrationSession:
        return cls(
            device_id=device_id,
            records=[
                CalibrationPointRecord(point=point)
                for point in generate_4x4_grid(margin=margin)
            ],
        )

    def start(self) -> None:
        if self.status is CalibrationSessionStatus.CANCELLED:
            raise CalibrationSessionError("cancelled calibration session cannot be restarted")
        if self.is_complete:
            self.status = CalibrationSessionStatus.COMPLETED
        else:
            self.status = CalibrationSessionStatus.RUNNING
        self._touch("session_started")

    def pause(self) -> None:
        if self.status is CalibrationSessionStatus.RUNNING:
            self.status = CalibrationSessionStatus.PAUSED
            self._touch("session_paused")

    def resume(self) -> None:
        if self.status is CalibrationSessionStatus.PAUSED:
            self.status = CalibrationSessionStatus.RUNNING
            self._touch("session_resumed")

    def cancel(self) -> None:
        self.status = CalibrationSessionStatus.CANCELLED
        self._touch("session_cancelled")

    @property
    def is_complete(self) -> bool:
        return all(record.status is CalibrationPointStatus.COMPLETED for record in self.records)

    def next_pending(self) -> CalibrationPointRecord | None:
        for record in self.records:
            if record.status is not CalibrationPointStatus.COMPLETED:
                return record
        return None

    def execute_next(
        self,
        *,
        mapper: CoordinateMapper,
        executor: CalibrationPointExecutor,
    ) -> CalibrationPointRecord:
        if self.status is not CalibrationSessionStatus.RUNNING:
            raise CalibrationSessionError(
                "calibration session must be running before sending a point"
            )
        record = self.next_pending()
        if record is None:
            self.status = CalibrationSessionStatus.COMPLETED
            self._touch("session_completed")
            raise CalibrationSessionError("calibration session is already complete")

        arm = mapper.normalized_to_arm(record.point.target)
        receipt = executor.tap_point(record.point, arm.x, arm.y)
        record.action_receipts.append(receipt)
        record.status = CalibrationPointStatus.ACTION_SENT
        record.updated_at = utc_now_iso()
        self.raw_events.append(
            {
                "event": "point_action_sent",
                "point_id": record.point.point_id,
                "target": {"x": record.point.target.x, "y": record.point.target.y},
                "arm_xy": {"x": arm.x, "y": arm.y},
                "receipt": receipt,
                "at": utc_now_iso(),
            }
        )
        self.updated_at = utc_now_iso()
        return record

    def record_touch(self, sample: TouchSample) -> CalibrationPointRecord:
        record = self._find_record(sample.point_id)
        record.actual = sample.actual
        record.touch_source = sample.source
        record.status = CalibrationPointStatus.COMPLETED
        record.updated_at = utc_now_iso()
        self.raw_events.append(
            {"event": "touch_recorded", "sample": sample.to_dict(), "at": utc_now_iso()}
        )
        if self.is_complete:
            self.status = CalibrationSessionStatus.COMPLETED
        self.updated_at = utc_now_iso()
        return record

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": "2.0",
            "session_id": self.session_id,
            "device_id": self.device_id,
            "status": self.status.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "records": [record.to_dict() for record in self.records],
            "raw_events": list(self.raw_events),
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> CalibrationSession:
        return cls(
            device_id=str(data["device_id"]),
            records=[
                CalibrationPointRecord.from_dict(_expect_dict(item, "record"))
                for item in _expect_list(data.get("records"), "records")
            ],
            session_id=str(data["session_id"]),
            status=CalibrationSessionStatus(str(data["status"])),
            created_at=str(data["created_at"]),
            updated_at=str(data["updated_at"]),
            raw_events=list(data.get("raw_events", [])),
        )

    def save_json(self, path: str | Path) -> None:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        body = json.dumps(self.to_dict(), ensure_ascii=False, indent=2, sort_keys=True)
        output.write_text(body, encoding="utf-8")

    @classmethod
    def load_json(cls, path: str | Path) -> CalibrationSession:
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))

    def _find_record(self, point_id: str) -> CalibrationPointRecord:
        for record in self.records:
            if record.point.point_id == point_id:
                return record
        raise CalibrationSessionError(f"unknown calibration point: {point_id}")

    def _touch(self, event: str) -> None:
        now = utc_now_iso()
        self.updated_at = now
        self.raw_events.append({"event": event, "at": now})


def _expect_dict(value: object, name: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise CalibrationSessionError(f"{name} must be an object")
    return value


def _expect_list(value: object, name: str) -> list[object]:
    if not isinstance(value, list):
        raise CalibrationSessionError(f"{name} must be a list")
    return value
