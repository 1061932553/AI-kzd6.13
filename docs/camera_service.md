# P2-03 摄像头采集与屏幕区域提取

## 目标

提供稳定的离线帧源读取、摄像头服务封装和手机屏幕 ROI 裁剪能力。

本任务包默认不打开真实 USB 摄像头。`TestVideoFrameSource` 使用本项目定义的 JSON 帧序列文件作为测试视频源，即使文件扩展名为 `.mp4`，也不会调用系统视频解码器或摄像头驱动。

## 模块

- `frame_source.py`：定义 `FrameSource` 协议、模拟器帧源和测试视频帧源。
- `camera_service.py`：封装打开、单帧读取、连续读取、断线重连和 ROI 截取。
- `screen_roi.py`：负责 ROI 裁剪和 PPM 调试截图保存。

## 调试截图

调试截图使用 PPM 格式保存，文件名包含：

- 前缀；
- 设备编号；
- 采集时间；
- 帧序号。

PPM 注释头中也写入 `device_id` 和 `captured_at`，便于离线排查。

## 离线预览

```powershell
python -m tools.camera_preview --source test_video.mp4
```

该命令读取离线测试视频源，裁剪 ROI，并在 `reports/debug_screenshots/` 下保存调试截图。

## 安全边界

- 默认不枚举、不打开 USB 摄像头。
- 默认不访问 `USB Camera2-B` 或任何 USB 摄像头采集流。
- 不访问 `127.0.0.1:8082`。
- 不打开 COM。
- 不发送机械臂动作。

## 验证命令

```powershell
python -m pytest tests\unit\test_screen_roi.py
python -m pytest tests\integration\test_video_source.py
python -m tools.camera_preview --source test_video.mp4
```
