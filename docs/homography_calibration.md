# P2-04 手机屏幕四角与透视矫正

## 目标

将摄像头画面中的倾斜手机屏幕四边形转换为标准矩形画面。

本任务包只做离线四角、单应性矩阵和透视矫正计算，不连接机械臂，不访问真实摄像头。

## 四角顺序

四角必须按以下顺序提供：

```text
top-left, top-right, bottom-right, bottom-left
```

顺序错误、退化四边形、输出尺寸非法都会被拒绝。

## 标定数据

`HomographyCalibration` 保存：

- `source_corners`
- `output_size`
- `matrix`
- `inverse_matrix`
- `maximum_reprojection_error`

标定矩阵可保存为 JSON 并重新加载。

## 离线预览

```powershell
python -m tools.calibrate_corners tests\fixtures\phone_tilted.jpg
```

`tests/fixtures/phone_tilted.jpg` 是项目内 JSON RGB 测试图容器，不是通用 JPEG 解码输入。该命令会生成：

- `reports/homography_calibration.json`
- `reports/debug_screenshots/rectified_*.ppm`

这些是调试输出，默认不纳入提交。

## 安全边界

- 不访问 `127.0.0.1:8082`。
- 不打开 COM。
- 不访问 USB 摄像头。
- 不运行 `references/` 中的 EXE、DLL 或 BAT。
- 不发送机械臂动作。

## 验证命令

```powershell
python -m pytest tests\unit\test_homography.py
python -m tools.calibrate_corners tests\fixtures\phone_tilted.jpg
```
