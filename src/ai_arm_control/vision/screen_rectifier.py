"""Perspective rectification for RGB24 camera frames."""

from __future__ import annotations

from pathlib import Path

from ai_arm_control.calibration.homography import HomographyCalibration, Point2D
from ai_arm_control.simulators.camera import CameraFrame
from ai_arm_control.vision.screen_roi import save_debug_ppm


class ScreenRectifier:
    def __init__(self, calibration: HomographyCalibration) -> None:
        self.calibration = calibration

    def rectify(self, frame: CameraFrame) -> CameraFrame:
        width = self.calibration.output_width
        height = self.calibration.output_height
        output = bytearray(width * height * frame.channels)
        for y in range(height):
            for x in range(width):
                source = self.calibration.inverse_matrix.apply(Point2D(float(x), float(y)))
                pixel = _sample_nearest(frame, source.x, source.y)
                offset = (y * width + x) * frame.channels
                output[offset : offset + frame.channels] = pixel
        return CameraFrame(
            camera_name=frame.camera_name,
            width=width,
            height=height,
            channels=frame.channels,
            pixel_format=frame.pixel_format,
            data=bytes(output),
            frame_index=frame.frame_index,
            captured_at=frame.captured_at,
            metadata={
                **dict(frame.metadata),
                "rectified": True,
                "source_width": frame.width,
                "source_height": frame.height,
            },
        )

    def save_preview(self, frame: CameraFrame, output_dir: str | Path, *, device_id: str) -> Path:
        return save_debug_ppm(
            self.rectify(frame),
            output_dir,
            device_id=device_id,
            prefix="rectified",
        )


def _sample_nearest(frame: CameraFrame, x: float, y: float) -> bytes:
    sample_x = min(max(int(round(x)), 0), frame.width - 1)
    sample_y = min(max(int(round(y)), 0), frame.height - 1)
    offset = (sample_y * frame.width + sample_x) * frame.channels
    return frame.data[offset : offset + frame.channels]
