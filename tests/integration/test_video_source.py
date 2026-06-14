from __future__ import annotations

import json
from pathlib import Path

from ai_arm_control.vision import CameraService, CameraServiceConfig, TestVideoFrameSource


def test_test_video_source_reads_frames_and_loops(tmp_path: Path) -> None:
    video = tmp_path / "test_video.mp4"
    write_test_video(video)
    source = TestVideoFrameSource(video, loop=True)
    service = CameraService(
        source=source,
        config=CameraServiceConfig(device_id="ARM-VIDEO", screen_roi=(1, 1, 3, 3)),
    )
    service.open()

    frames = service.read_frames(3)
    roi = service.capture_screen_roi()
    service.close()

    assert [frame.data[:3] for frame in frames] == [
        bytes([10, 20, 30]),
        bytes([40, 50, 60]),
        bytes([10, 20, 30]),
    ]
    assert roi.width == 2
    assert roi.height == 2


def write_test_video(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "device_id": "ARM-VIDEO",
                "source_name": "test-video",
                "width": 4,
                "height": 4,
                "channels": 3,
                "frames": [
                    {"fill": [10, 20, 30]},
                    {"fill": [40, 50, 60]},
                ],
            }
        ),
        encoding="utf-8",
    )
