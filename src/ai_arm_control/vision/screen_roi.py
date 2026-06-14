"""Screen ROI extraction and debug image saving."""

from __future__ import annotations

from pathlib import Path

from ai_arm_control.simulators.camera import CameraFrame, crop_frame


class ScreenROIExtractor:
    def __init__(self, roi: tuple[int, int, int, int]) -> None:
        self.roi = roi

    def extract(self, frame: CameraFrame) -> CameraFrame:
        return crop_frame(frame, self.roi)


def save_debug_ppm(
    frame: CameraFrame,
    output_dir: str | Path,
    *,
    device_id: str,
    prefix: str = "screen_roi",
) -> Path:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    safe_time = frame.captured_at.replace(":", "").replace("-", "").replace(".", "")
    filename = f"{prefix}_{device_id}_{safe_time}_f{frame.frame_index}.ppm"
    path = output / filename
    header = f"P6\n# device_id={device_id} captured_at={frame.captured_at}\n"
    header += f"{frame.width} {frame.height}\n255\n"
    path.write_bytes(header.encode("ascii") + frame.data)
    return path
