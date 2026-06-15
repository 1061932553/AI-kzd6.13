"""Manual control application configuration and launch boundary."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


class ManualAppError(RuntimeError):
    """Raised when the manual app boundary rejects an operation."""


DEFAULT_MANUAL_APP_DIRECTORY = (
    "C:\\Users\\s1061\\Desktop\\AI-Multi-Device-Control\\references"
    "\\main\u8f6f\u4ef6\u53d1\u5ba2\u6237-20260531\\main"
)


class ManualAppLauncher(Protocol):
    def start(self, app_directory: Path, executable: str) -> None: ...

    def is_running(self) -> bool: ...


@dataclass(frozen=True, slots=True)
class ManualControlConfig:
    enabled: bool = True
    app_directory: Path = Path(DEFAULT_MANUAL_APP_DIRECTORY)
    executable: str = ""

    @classmethod
    def from_dict(cls, data: object) -> ManualControlConfig:
        if not isinstance(data, dict):
            raise ManualAppError("manual_control config must be a mapping")
        allowed = {"enabled", "app_directory", "executable"}
        unknown = set(data) - allowed
        if unknown:
            fields = ", ".join(sorted(unknown))
            raise ManualAppError(f"unknown manual_control field(s): {fields}")
        return cls(
            enabled=bool(data.get("enabled", True)),
            app_directory=Path(data.get("app_directory", DEFAULT_MANUAL_APP_DIRECTORY)),
            executable=str(data.get("executable", "")),
        )


class ManualAppController:
    """Boundary for manual software.

    The default controller never launches a process by itself. Tests and future
    hardware workflows must inject a launcher explicitly.
    """

    def __init__(
        self,
        config: ManualControlConfig,
        *,
        launcher: ManualAppLauncher | None = None,
    ) -> None:
        self.config = config
        self.launcher = launcher

    def start(self) -> None:
        if not self.config.enabled:
            raise ManualAppError("manual control is disabled")
        if self.launcher is None:
            raise ManualAppError("manual app launcher is not configured")
        self.launcher.start(self.config.app_directory, self.config.executable)

    def is_closed(self) -> bool:
        if self.launcher is None:
            return True
        return not self.launcher.is_running()
