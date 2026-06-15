"""Vision services for offline camera and ROI workflows."""

from ai_arm_control.vision.camera_service import CameraService, CameraServiceConfig
from ai_arm_control.vision.frame_source import (
    FrameSource,
    FrameSourceError,
    SimulatorFrameSource,
    TestVideoFrameSource,
)
from ai_arm_control.vision.screen_rectifier import ScreenRectifier
from ai_arm_control.vision.screen_roi import ScreenROIExtractor, save_debug_ppm
from ai_arm_control.vision.template_matcher import (
    TemplateImage,
    TemplateMatch,
    TemplateMatcher,
    TemplateMatchResult,
    load_rgb_frame,
    load_template_image,
)

__all__ = [
    "CameraService",
    "CameraServiceConfig",
    "FrameSource",
    "FrameSourceError",
    "ScreenRectifier",
    "ScreenROIExtractor",
    "SimulatorFrameSource",
    "TestVideoFrameSource",
    "TemplateImage",
    "TemplateMatch",
    "TemplateMatcher",
    "TemplateMatchResult",
    "load_rgb_frame",
    "load_template_image",
    "save_debug_ppm",
]
