# P2-01 标定数据 schema v2

## 目标

旧软件生成的标定 JSON 只能作为初始输入。新项目内部统一使用 `schema_version: "2.0"` 的标准标定模型，后续坐标转换、误差补偿和脚本动作都必须基于该模型。

本任务包只做离线读取、校验和转换，不包含坐标转换、误差补偿或实机点击。

## 标准输出

```json
{
  "schema_version": "2.0",
  "device_id": "ARM-001",
  "camera_size": [540, 960],
  "screen_roi": [64, 32, 482, 911],
  "arm_limits": {
    "x_min": 0,
    "x_max": 366,
    "y_min": 0,
    "y_max": 160
  },
  "press_z": 7.0
}
```

内部模型还保留后续阶段字段：`mapping_matrix`、`correction_grid`、`average_error`、`maximum_error`。这些字段初始为空或 `null`，不能代表已完成精度验证。

## 旧字段映射

| 标准字段 | 旧字段 |
|---|---|
| `camera_size[0]` | `图像分辨率宽度像素_` |
| `camera_size[1]` | `图像分辨率高度像素_` |
| `screen_roi` | `手机屏幕像素区域` |
| `press_z` | `触控笔下降距离_[0]` |
| `arm_limits.x_max` | `触控笔宽高极限位置[0]` |
| `arm_limits.y_max` | `触控笔宽高极限位置[1]` |
| `device_id` | `机位_`，格式化为 `ARM-001` |
| `hardware_binding.service_url` | `url地址` |

同时支持英文别名：`camera_width`、`camera_height`、`screen_roi`、`press_z_range`、`arm_limit_range`、`service_url`。

## 校验规则

- 必填字段缺失时返回明确字段名。
- 数值字段不能是字符串、布尔值或对象。
- `camera_size` 必须为正数。
- `screen_roi` 必须是 4 个数，且必须位于 `camera_size` 内。
- `arm_limits` 必须为正范围。
- `press_z` 必须大于 0。
- 原始 JSON 只读，不会被修改。

## 离线验证

```powershell
python -m pytest tests\unit\test_legacy_importer.py
python -m tools.import_legacy_calibration <legacy-calibration-json>
```

如需完整绑定信息和待验证标记：

```powershell
python -m tools.import_legacy_calibration <legacy-calibration-json> --device-config <legacy-config-json> --full
```
