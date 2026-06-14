"""Frame source abstractions.

No class in this module enumerates or opens a real USB camera by default.
`TestVideoFrameSource` reads deterministic JSON frame sequences for offline
integration tests and command-line previews.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from ai_arm_control.simulators.camera import CameraFrame, CameraSimulator


class FrameSourceError(RuntimeError):
    """Raised when a frame source cannot provide frames."""


class FrameSource(Protocol):
    device_id: str
    source_name: str

    def open(self) -> None: ...

    def close(self) -> None: ...

    def is_open(self) -> bool: ...

    def read_frame(self) -> CameraFrame: ...


class SimulatorFrameSource:
    def __init__(self, simulator: CameraSimulator, *, device_id: str = "SIM-CAMERA") -> None:
        self.simulator = simulator
        self.device_id = device_id
        self.source_name = simulator.config.camera_name

    def open(self) -> None:
        self.simulator.open()

    def close(self) -> None:
        self.simulator.close()

    def is_open(self) -> bool:
        return self.simulator.is_open()

    def read_frame(self) -> CameraFrame:
        return self.simulator.capture_frame()


@dataclass(frozen=True, slots=True)
class EncodedFrame:
    data: bytes
    width: int
    height: int
    channels: int


class TestVideoFrameSource:
    """Offline frame source backed by a JSON file.

    File shape:
    `{ "device_id": "...", "source_name": "...", "width": 4, "height": 4,
       "frames": [{"fill": [r, g, b]}, {"data_hex": "..."}] }`
    """

    __test__ = False

    def __init__(self, path: str | Path, *, loop: bool = True) -> None:
        self.path = Path(path)
        self.loop = loop
        self._is_open = False
        self._next_index = 0
        self._frames: list[EncodedFrame] = []
        self.device_id = "TEST-VIDEO"
        self.source_name = str(self.path)

    def open(self) -> None:
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except OSError as exc:
            raise FrameSourceError(f"cannot read test video: {self.path}") from exc
        except json.JSONDecodeError as exc:
            raise FrameSourceError(f"invalid test video JSON: {self.path}") from exc
        self.device_id = str(payload.get("device_id", "TEST-VIDEO"))
        self.source_name = str(payload.get("source_name", self.path.name))
        width = _positive_int("width", payload.get("width"))
        height = _positive_int("height", payload.get("height"))
        channels = _positive_int("channels", payload.get("channels", 3))
        if channels != 3:
            raise FrameSourceError("test video supports RGB24 frames only")
        frames = payload.get("frames")
        if not isinstance(frames, list) or not frames:
            raise FrameSourceError("test video requires at least one frame")
        self._frames = [_decode_frame(item, width, height, channels) for item in frames]
        self._next_index = 0
        self._is_open = True

    def close(self) -> None:
        self._is_open = False

    def is_open(self) -> bool:
        return self._is_open

    def read_frame(self) -> CameraFrame:
        if not self._is_open:
            raise FrameSourceError("test video source is not open")
        if self._next_index >= len(self._frames):
            if not self.loop:
                raise FrameSourceError("test video reached end of stream")
            self._next_index = 0
        encoded = self._frames[self._next_index]
        self._next_index += 1
        return CameraFrame(
            camera_name=self.source_name,
            width=encoded.width,
            height=encoded.height,
            channels=encoded.channels,
            pixel_format="RGB24",
            data=encoded.data,
            frame_index=self._next_index,
            captured_at=_utc_now_text(),
            metadata={"source": "test_video", "path": str(self.path)},
        )


def _decode_frame(item: object, width: int, height: int, channels: int) -> EncodedFrame:
    if not isinstance(item, dict):
        raise FrameSourceError("each test video frame expects a mapping")
    byte_length = width * height * channels
    if "data_hex" in item:
        data = bytes.fromhex(str(item["data_hex"]))
        if len(data) != byte_length:
            raise FrameSourceError("data_hex length does not match frame dimensions")
        return EncodedFrame(data=data, width=width, height=height, channels=channels)
    fill = item.get("fill")
    if (
        not isinstance(fill, list)
        or len(fill) != 3
        or any(not isinstance(value, int) for value in fill)
    ):
        raise FrameSourceError("test video frame requires fill [r, g, b] or data_hex")
    if any(value < 0 or value > 255 for value in fill):
        raise FrameSourceError("fill values must be between 0 and 255")
    return EncodedFrame(data=bytes(fill) * (width * height), width=width, height=height, channels=3)


def _positive_int(name: str, value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise FrameSourceError(f"{name} must be a positive integer")
    return value


def _utc_now_text() -> str:
    from ai_arm_control.models.types import utc_now

    return utc_now().isoformat()
