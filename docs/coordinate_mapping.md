# P2-02 坐标模型与基础映射核心

## 目标

建立统一坐标系统，完成脚本归一化坐标到机械臂 XY 坐标的离线基础转换。

本任务包只做纯计算，不依赖摄像头、机械臂、UI 或动作执行器。

## 坐标类型

- `CameraPixel`：摄像头原始像素。当前阶段与屏幕 ROI 坐标共用像素平面，不做透视矫正。
- `ScreenPixel`：手机屏幕 ROI 所在像素平面中的点。
- `NormalizedPoint`：脚本坐标，范围为 `[0.0, 1.0]`。
- `ArmXY`：机械臂 XY 坐标。

## 映射流程

```text
NormalizedPoint
  -> ScreenPixel through screen_roi
  -> ArmXY through arm_bounds
```

`CoordinateMapper` 支持：

- 归一化坐标校验。
- 屏幕 ROI 转换。
- 机械臂坐标转换。
- X/Y 方向翻转。
- 边界限制。
- 越界拒绝。
- 机械臂 XY 与归一化坐标往返转换。

## 安全规则

- 非数字、负数、`NaN`、`bool` 和超过 `[0.0, 1.0]` 的归一化坐标会被拒绝。
- 屏幕像素超出 `screen_roi` 会被拒绝。
- 机械臂坐标超出 `arm_bounds` 会被拒绝。
- 本模块不会调用 `StandardDeviceAPI`，不会发送任何机械臂动作。

## 验证命令

```powershell
python -m pytest tests\unit\test_coordinate_mapper.py
```

测试覆盖左上、中心、右下、越界坐标、负数坐标、非数字输入、翻转和往返转换。
