"""Image-based tap action built on template matching and normal tap."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ai_arm_control.actions.models import TouchActionConfig, TouchArmAPI, TouchSleeper
from ai_arm_control.actions.result import TouchActionLogEntry, TouchActionResult, TouchActionStatus
from ai_arm_control.actions.tap import SystemSleeper, execute_tap
from ai_arm_control.coordinates.mapper import CoordinateMapper
from ai_arm_control.coordinates.models import NormalizedPoint
from ai_arm_control.simulators.camera import CameraFrame
from ai_arm_control.vision.screen_roi import save_debug_ppm
from ai_arm_control.vision.template_matcher import (
    TemplateImage,
    TemplateMatcher,
    TemplateMatchResult,
)


@dataclass(frozen=True, slots=True)
class TapImageConfig:
    confidence: float = 0.85
    retry: int = 0
    timeout_ms: int = 5_000
    search_rect: tuple[int, int, int, int] | None = None
    failure_screenshot_dir: Path | None = None

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")
        if self.retry < 0:
            raise ValueError("retry cannot be negative")
        if self.timeout_ms <= 0:
            raise ValueError("timeout_ms must be positive")


class FrameProvider:
    def capture_frame(self) -> CameraFrame:
        raise NotImplementedError


class StaticFrameProvider(FrameProvider):
    def __init__(self, frame: CameraFrame) -> None:
        self.frame = frame

    def capture_frame(self) -> CameraFrame:
        return self.frame


def execute_tap_image(
    *,
    frame_provider: FrameProvider,
    template: TemplateImage | CameraFrame,
    mapper: CoordinateMapper,
    arm: TouchArmAPI,
    config: TapImageConfig | None = None,
    touch_config: TouchActionConfig | None = None,
    sleeper: TouchSleeper | None = None,
) -> TouchActionResult:
    tap_config = config or TapImageConfig()
    delay = sleeper or SystemSleeper()
    logs: list[TouchActionLogEntry] = []
    matcher = TemplateMatcher(confidence_threshold=tap_config.confidence)
    attempts = tap_config.retry + 1
    last_result: TemplateMatchResult | None = None
    last_frame: CameraFrame | None = None
    for attempt in range(1, attempts + 1):
        frame = frame_provider.capture_frame()
        last_frame = frame
        match_result = matcher.match(frame, template, search_rect=tap_config.search_rect)
        last_result = match_result
        _log(
            logs,
            "template_match",
            TouchActionStatus.SUCCEEDED,
            {"attempt": attempt, **match_result.to_dict()},
        )
        if match_result.found and match_result.match is not None:
            normalized = _match_center_to_normalized(match_result.match.center, frame)
            _log(
                logs,
                "target_normalized",
                TouchActionStatus.SUCCEEDED,
                {"x": normalized.x, "y": normalized.y},
            )
            tap_result = execute_tap(
                normalized,
                mapper=mapper,
                arm=arm,
                config=touch_config,
                sleeper=delay,
            )
            logs.extend(tap_result.logs)
            if tap_result.succeeded:
                return TouchActionResult("tap_image", TouchActionStatus.SUCCEEDED, logs)
            return TouchActionResult(
                "tap_image",
                TouchActionStatus.FAILED,
                logs,
                error=tap_result.error,
            )
    screenshot = _save_failure(last_frame, tap_config.failure_screenshot_dir)
    detail = {
        "last_match": last_result.to_dict() if last_result else None,
        "failure_screenshot": str(screenshot) if screenshot else None,
    }
    _log(logs, "template_not_found", TouchActionStatus.FAILED, detail)
    return TouchActionResult(
        "tap_image",
        TouchActionStatus.FAILED,
        logs,
        error="template not found",
    )


def _match_center_to_normalized(center: tuple[float, float], frame: CameraFrame) -> NormalizedPoint:
    return NormalizedPoint(center[0] / frame.width, center[1] / frame.height)


def _save_failure(frame: CameraFrame | None, directory: Path | None) -> Path | None:
    if frame is None or directory is None:
        return None
    return save_debug_ppm(
        frame,
        directory,
        device_id=str(frame.metadata.get("device_id", "UNKNOWN")),
        prefix="tap_image_failed",
    )


def _log(
    logs: list[TouchActionLogEntry],
    step: str,
    status: TouchActionStatus,
    detail: dict[str, object] | None = None,
) -> None:
    logs.append(TouchActionLogEntry(step=step, status=status, detail=detail or {}))
