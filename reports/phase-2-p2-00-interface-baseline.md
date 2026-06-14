# P2-00 第二阶段接口冻结与测试基线报告

执行日期：2026-06-14

## 范围

- 冻结机械臂适配器公开方法。
- 确认模拟配置和真实配置形态暴露相同接口。
- 创建第二阶段测试目录：`tests/unit/`、`tests/hardware/`、`tests/fixtures/`。
- 创建标准测试图片和标准标定文件。
- 建立真实设备测试开关。
- 创建硬件测试示例配置。

## 交付物

- `docs/phase2/interface_contract.md`
- `tests/unit/test_arm_interface_contract.py`
- `tests/hardware/test_hardware_switch.py`
- `tests/fixtures/standard_calibration_v2.json`
- `tests/fixtures/standard_screen.ppm`
- `config/hardware.example.yaml`

## 测试结果

- `python -m pytest tests\unit\test_arm_interface_contract.py`：通过，`5 passed`。
- `python -m pytest`：通过，`165 passed, 1 skipped`。
- `python -m ruff check .`：通过，`All checks passed!`。

## 安全结果

- 默认测试未访问 `127.0.0.1:8082`。
- 默认测试未打开 COM 串口。
- 默认测试未访问 USB 摄像头。
- 默认测试未运行第三方 EXE、DLL、BAT、安装程序或服务程序。
- 默认测试未发送真实机械臂命令。
- `tests/hardware/` 默认跳过，必须设置 `AI_ARM_CONTROL_ENABLE_HARDWARE_TESTS=1` 才会执行。

## 风险

- `config/hardware.example.yaml` 只是模板，不代表真实硬件授权。
- 真实适配器接口形态已冻结，但真实设备动作仍需后续任务包在安全边界内单独验收。
- 当前任务包不包含标定、摄像头、动作脚本或人工模式。
