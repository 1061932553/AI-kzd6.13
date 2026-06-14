# P2-00 第二阶段接口冻结与测试基线

## 冻结接口

第二阶段后续任务统一使用 `StandardDeviceAPI` 作为设备动作入口。公开方法冻结为：

- `connect()`
- `disconnect()`
- `home()`
- `move_xy(x, y)`
- `pen_down(z)`
- `pen_up()`
- `stop()`
- `get_status()`
- `health_check()`
- `execute(command)`
- `load_calibration(calibration)`

`JxbArmAdapter` 同时用于模拟配置和真实配置。默认配置使用模拟器；真实硬件配置必须显式关闭模拟标记并开启硬件授权。

## 安全基线

- 默认单元测试不得访问 `127.0.0.1:8082`。
- 默认单元测试不得打开 COM 串口。
- 默认单元测试不得访问 USB 摄像头。
- 默认单元测试不得发送真实机械臂动作。
- 硬件测试必须显式设置 `AI_ARM_CONTROL_ENABLE_HARDWARE_TESTS=1`。
- 即使启用硬件测试，动作仍必须经过配置和安全边界校验。

## 测试目录

- `tests/unit/`：第二阶段接口与纯离线单元测试。
- `tests/hardware/`：可重复实机测试脚本，默认跳过。
- `tests/fixtures/`：标准测试图片、标准测试标定文件和后续任务共享样本。

## 配置位置

- 示例应用配置：`configs/app.example.json`。
- 硬件测试示例配置：`config/hardware.example.yaml`。

`config/hardware.example.yaml` 仅是模板，不代表真实硬件已授权。真实设备配置应复制到本地私有文件并由人工确认后使用。

## P2-00 验证命令

```powershell
python -m pytest tests/unit/test_arm_interface_contract.py
python -m pytest
python -m ruff check .
```
