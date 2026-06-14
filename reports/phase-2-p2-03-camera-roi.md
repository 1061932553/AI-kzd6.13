# P2-03 摄像头采集与屏幕区域提取报告

执行日期：2026-06-14

## 范围

- 根据帧源配置打开离线帧源。
- 获取单帧和连续读取。
- 断线后自动重连并记录日志。
- 检测帧分辨率。
- 按配置裁剪手机屏幕 ROI。
- 保存包含时间和设备编号的 PPM 调试截图。
- 使用测试视频源代替真实摄像头。

## 交付物

- `src/ai_arm_control/vision/frame_source.py`
- `src/ai_arm_control/vision/camera_service.py`
- `src/ai_arm_control/vision/screen_roi.py`
- `src/vision/frame_source.py`
- `src/vision/camera_service.py`
- `src/vision/screen_roi.py`
- `tests/unit/test_screen_roi.py`
- `tests/integration/test_video_source.py`
- `tools/camera_preview.py`
- `test_video.mp4`
- `docs/camera_service.md`

## 验证结果

- `python -m pytest tests\unit\test_screen_roi.py`：通过，`5 passed`。
- `python -m pytest tests\integration\test_video_source.py`：通过，`1 passed`。
- `python -m tools.camera_preview --source test_video.mp4`：通过，生成 PPM 调试截图路径。
- `python -m pytest`：通过，`197 passed, 1 skipped`。
- `python -m ruff check .`：通过，`All checks passed!`。

## 安全结果

- 未修改 `references/`。
- 未访问 `127.0.0.1:8082`。
- 未打开 COM 串口。
- 未访问 USB 摄像头或任何真实摄像头采集流。
- 未运行第三方 EXE、DLL、BAT、安装程序或服务程序。
- 未发送真实机械臂命令。

## 风险

- `TestVideoFrameSource` 是项目内 JSON 测试视频容器，不是通用 MP4 解码器。
- 当前不包含找图、标定计算或 PySide6 完整界面。
- 真实摄像头采集仍需后续单独授权和独立任务包。
