# P2-04 手机屏幕四角与透视矫正报告

执行日期：2026-06-14

## 范围

- 手动四角输入和顺序校验。
- 四角坐标保存和加载。
- 纯 Python 单应性矩阵计算。
- 正向和反向坐标转换。
- RGB24 离线透视矫正。
- 标定数据有效性检查。
- 标定预览图输出。

## 交付物

- `src/ai_arm_control/calibration/homography.py`
- `src/ai_arm_control/calibration/corner_selector.py`
- `src/ai_arm_control/vision/screen_rectifier.py`
- `src/calibration/homography.py`
- `src/calibration/corner_selector.py`
- `src/vision/screen_rectifier.py`
- `tests/unit/test_homography.py`
- `tests/fixtures/phone_tilted.jpg`
- `tools/calibrate_corners.py`
- `docs/homography_calibration.md`

## 验证结果

- `python -m pytest tests\unit\test_homography.py`：通过，`7 passed`。
- `python -m tools.calibrate_corners tests\fixtures\phone_tilted.jpg`：通过，生成标定 JSON 和 PPM 预览图。
- `python -m pytest`：通过，`204 passed, 1 skipped`。
- `python -m ruff check .`：通过，`All checks passed!`。

## 安全结果

- 未修改 `references/`。
- 未访问 `127.0.0.1:8082`。
- 未打开 COM 串口。
- 未访问 USB 摄像头或任何真实摄像头采集流。
- 未运行第三方 EXE、DLL、BAT、安装程序或服务程序。
- 未发送真实机械臂命令。

## 风险

- `tests/fixtures/phone_tilted.jpg` 是项目内 JSON RGB 测试图容器，不是通用 JPEG 解码器输入。
- 当前不包含 16 点点击标定、局部误差补偿或找图点击。
- 当前透视矫正使用最近邻采样，后续如需更平滑预览可增加插值策略。
