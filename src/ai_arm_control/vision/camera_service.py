"""Camera service wrapper for offline frame sources."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from ai_arm_control.simulators.camera import CameraFrame
from ai_arm_control.vision.frame_source import FrameSource, FrameSourceError
from ai_arm_control.vision.screen_roi import ScreenROIExtractor, save_debug_ppm

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class CameraServiceConfig:
    device_id: str
    screen_roi: tuple[int, int, int, int]
    debug_output_dir: Path = Path("reports/debug_screenshots")
    reconnect_attempts: int = 1

    def __post_init__(self) -> None:
        if self.reconnect_attempts < 0:
            raise ValueError("reconnect_attempts cannot be negative")


class CameraService:
    def __init__(self, *, source: FrameSource, config: CameraServiceConfig) -> None:
        self.source = source
        self.config = config
        self.roi = ScreenROIExtractor(config.screen_roi)

    def open(self) -> None:
        self.source.open()
        LOGGER.info("camera source opened", extra={"device_id": self.config.device_id})

    def close(self) -> None:
        self.source.close()
        LOGGER.info("camera source closed", extra={"device_id": self.config.device_id})

    def read_frame(self) -> CameraFrame:
        return self._read_with_reconnect()

    def read_frames(self, count: int) -> list[CameraFrame]:
        if count <= 0:
            raise ValueError("count must be positive")
        return [self.read_frame() for _ in range(count)]

    def capture_screen_roi(self) -> CameraFrame:
        return self.roi.extract(self.read_frame())

    def save_debug_screenshot(self, frame: CameraFrame, *, prefix: str = "screen_roi") -> Path:
        return save_debug_ppm(
            frame,
            self.config.debug_output_dir,
            device_id=self.config.device_id,
            prefix=prefix,
        )

    def _read_with_reconnect(self) -> CameraFrame:
        attempts_left = self.config.reconnect_attempts + 1
        last_error: Exception | None = None
        while attempts_left:
            attempts_left -= 1
            try:
                if not self.source.is_open():
                    self.source.open()
                    LOGGER.info(
                        "camera source reconnected",
                        extra={"device_id": self.config.device_id},
                    )
                return self.source.read_frame()
            except FrameSourceError as exc:
                last_error = exc
                LOGGER.warning(
                    "camera read failed; attempting reconnect",
                    extra={"device_id": self.config.device_id, "attempts_left": attempts_left},
                )
                self.source.close()
        raise FrameSourceError("camera read failed after reconnect attempts") from last_error
