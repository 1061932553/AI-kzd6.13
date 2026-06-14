# P2-02 坐标模型与基础映射核心报告

执行日期：2026-06-14

## 范围

- 新增摄像头原始像素、手机屏幕像素、归一化坐标和机械臂 XY 坐标模型。
- 实现归一化坐标校验。
- 实现屏幕 ROI 转换。
- 实现机械臂 XY 基础映射。
- 支持 X、Y 方向翻转。
- 实现边界限制和越界拒绝。
- 增加往返转换测试。

## 交付物

- `src/ai_arm_control/coordinates/models.py`
- `src/ai_arm_control/coordinates/normalizer.py`
- `src/ai_arm_control/coordinates/mapper.py`
- `src/ai_arm_control/coordinates/bounds.py`
- `src/coordinates/models.py`
- `src/coordinates/normalizer.py`
- `src/coordinates/mapper.py`
- `src/coordinates/bounds.py`
- `tests/unit/test_coordinate_mapper.py`
- `docs/coordinate_mapping.md`

## 验证结果

- `python -m pytest tests\unit\test_coordinate_mapper.py`：通过，`17 passed`。
- `python -m pytest`：通过，`191 passed, 1 skipped`。
- `python -m ruff check .`：通过，`All checks passed!`。

## 安全结果

- 未修改 `references/`。
- 未访问 `127.0.0.1:8082`。
- 未打开 COM 串口。
- 未访问 USB 摄像头。
- 未运行第三方 EXE、DLL、BAT、安装程序或服务程序。
- 未发送真实机械臂命令。

## 风险

- 当前为基础线性映射，不包含透视矫正。
- 当前不包含误差补偿。
- 当前不接动作执行器，因此不代表实机点击精度。
