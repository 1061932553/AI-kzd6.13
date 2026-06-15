"""In-process device ownership lock for automatic/manual mode gates."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from threading import RLock


class DeviceLockError(RuntimeError):
    """Raised when a device lock operation would violate ownership."""


@dataclass(frozen=True, slots=True)
class DeviceLockSnapshot:
    device_id: str
    owner: str | None
    acquired_at: str | None

    @property
    def is_locked(self) -> bool:
        return self.owner is not None


@dataclass(slots=True)
class DeviceLock:
    device_id: str
    _owner: str | None = None
    _acquired_at: str | None = None
    _lock: RLock = field(default_factory=RLock)

    def acquire(self, owner: str) -> DeviceLockSnapshot:
        if not owner:
            raise DeviceLockError("lock owner is required")
        with self._lock:
            if self._owner is not None and self._owner != owner:
                raise DeviceLockError(
                    f"device {self.device_id} is already owned by {self._owner}"
                )
            if self._owner is None:
                self._owner = owner
                self._acquired_at = datetime.now(UTC).isoformat()
            return self.snapshot()

    def release(self, owner: str) -> DeviceLockSnapshot:
        with self._lock:
            if self._owner is None:
                return self.snapshot()
            if self._owner != owner:
                raise DeviceLockError(
                    f"device {self.device_id} is owned by {self._owner}, not {owner}"
                )
            self._owner = None
            self._acquired_at = None
            return self.snapshot()

    def require_owner(self, owner: str) -> None:
        with self._lock:
            if self._owner != owner:
                message = (
                    f"device {self.device_id} requires owner {owner}; "
                    f"current owner is {self._owner}"
                )
                raise DeviceLockError(
                    message
                )

    def snapshot(self) -> DeviceLockSnapshot:
        with self._lock:
            return DeviceLockSnapshot(
                device_id=self.device_id,
                owner=self._owner,
                acquired_at=self._acquired_at,
            )
