# P2-01 旧标定 JSON 导入与标准数据模型报告

执行日期：2026-06-14

## 范围

- 解析旧标定 JSON 中的图像分辨率、手机屏幕区域、触控笔下降距离、机械臂活动极限、设备编号和服务地址。
- 解析旧 `config.json` 中的摄像头和机械臂绑定信息。
- 支持中文字段名和部分英文别名。
- 处理字段缺失、字段类型错误和超出范围。
- 输出 `schema_version: "2.0"` 标准标定 JSON。

## 交付物

- `src/ai_arm_control/calibration/models.py`
- `src/ai_arm_control/calibration/legacy_importer.py`
- `src/ai_arm_control/calibration/validator.py`
- `src/calibration/models.py`
- `src/calibration/legacy_importer.py`
- `src/calibration/validator.py`
- `tests/unit/test_legacy_importer.py`
- `docs/calibration_schema.md`
- `tools/import_legacy_calibration.py`

## 验证结果

- `python -m pytest tests\unit\test_legacy_importer.py`：通过，`9 passed`。
- `python -m tools.import_legacy_calibration references\main软件发客户-20260531\main\me_config\USBVID_1A86&PID_75235&2B28DE69&0&8USBVID_1A86&PID_75235&2B28DE69&0&8\1.json`：通过，输出标准 JSON。
- `python -m pytest`：通过，`174 passed, 1 skipped`。
- `python -m ruff check .`：通过，`All checks passed!`。

## 安全结果

- 未修改 `references/`。
- 未访问 `127.0.0.1:8082`。
- 未打开 COM 串口。
- 未访问 USB 摄像头。
- 未运行第三方 EXE、DLL、BAT、安装程序或服务程序。
- 未发送真实机械臂命令。

## 风险

- 旧标定值只作为初始导入数据，精度仍待验证。
- `mapping_matrix`、`correction_grid`、误差统计字段仍由后续标定任务生成。
- 本任务包不包含坐标转换、误差补偿或实机点击。
