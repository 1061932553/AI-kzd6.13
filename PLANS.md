# 阶段一任务状态

更新时间：2026-06-13

阶段一执行原则：一次只执行一个任务包。当前已完成 P1-00 至 P1-09。阶段一已完成，后续真实适配器必须另开任务并等待明确指令。

| 任务包 | 状态 | 目标 | 依赖 | 交付物 | 验收条件 | 风险 | 是否允许访问真实硬件 |
|---|---|---|---|---|---|---|---|
| P1-00 项目资料基线 | 已完成 | 盘点仓库、分类资料、整理事实和待验证问题、建立任务状态记录 | 当前仓库文件和 `references/` 只读资料 | `docs/facts.md`、`docs/open-questions.md`、`docs/reference-inventory.md`、`PLANS.md` | 文档存在；事实不包含未经验证推测；列出严禁修改/执行文件；P1-00 至 P1-09 均有状态记录 | 参考资料可能不完整；旧配置不等于当前硬件状态 | 否 |
| P1-01 项目规则和架构契约 | 已完成 | 统一后续所有 Codex 任务的开发规则，定义总体架构、目录职责、依赖方向、禁止事项、完成标准和公共接口草案 | P1-00 | `AGENTS.md`、`PLANS.md`、`docs/architecture.md`、`docs/coding-rules.md`、`docs/definition-of-done.md` | 业务层不能直接调用 JxbService；所有设备动作必须经过统一接口；真实硬件模式默认关闭；第三方参考文件只读；公共接口修改必须有记录 | 规则不清会导致后续实现误触真实设备 | 否 |
| P1-02 Python项目骨架 | 已完成 | 建立可以安装、启动和测试的空 Python 项目 | P1-01 | `pyproject.toml`、`README.md`、`src/ai_arm_control/`、`tests/` | `python -m ai_arm_control --help`、`pytest`、`ruff check .` 可运行；目录结构符合契约；不实现机械臂控制 | 过早引入复杂依赖；与后续模拟器边界不一致 | 否 |
| P1-03 公共数据模型 | 已完成 | 统一所有模块使用的数据格式 | P1-01、P1-02 | `src/ai_arm_control/models/types.py`、`src/ai_arm_control/models/__init__.py`、`tests/test_models.py` | 模型没有 HTTP 和串口逻辑；模型可以序列化；非法字段会被拒绝；状态和模式不能使用随意字符串；具有完整单元测试 | 模型过窄会影响后续扩展；模型过宽会增加维护成本 | 否 |
| P1-04 配置系统和旧JSON导入 | 已完成 | 禁止在代码中硬编码设备参数，读取、校验并转换主配置和旧 JSON | P1-03 | `src/ai_arm_control/config/settings.py`、`configs/app.example.json`、`tests/test_config.py` | 不使用旧文件中的历史资源号作为新连接资源号；COM、URL、坐标范围均可配置；配置错误时程序拒绝启动；原始 JSON 不被修改；旧格式和新格式转换有测试 | 旧 JSON 语义不完整；字段含义可能需人工确认 | 否 |
| P1-05 日志、异常和命令追踪 | 已完成 | 以后出现问题时可以快速定位 | P1-03 | `src/ai_arm_control/core/exceptions.py`、`src/ai_arm_control/core/tracing.py`、`src/ai_arm_control/logging/setup.py`、`tests/test_logging_tracing.py` | 禁止裸 except；异常不能被静默吞掉；日志支持轮转；控制台和文件均有日志；敏感信息不能进入日志；同一命令全流程使用同一个 ID | 日志不足会影响诊断；日志过量会增加噪声 | 否 |
| P1-06 JxbService模拟器 | 已完成 | 在完全不连接真实机械臂的情况下开发后续控制模块 | P1-01、P1-03、P1-05 | `src/ai_arm_control/simulators/jxb_service.py`、`tests/test_jxb_simulator.py` | 业务代码只修改 URL 即可切换模拟和真实服务；每个故障可以通过配置稳定复现；模拟器不会访问真实 COM；模拟器不会启动真实 JxbService；请求历史可以供测试断言使用 | 模拟行为与真实服务差异待验证 | 否 |
| P1-07 自动化测试场景 | 已完成 | 为阶段二提供稳定测试基线 | P1-02 至 P1-06 | `tests/test_stage1_scenarios.py`、`src/ai_arm_control/state_machine/machine.py` | 测试之间相互隔离；测试顺序不影响结果；不使用真实设备；每种异常都有明确预期；全部测试可通过一条命令运行 | 测试数据不足会掩盖协议问题 | 否 |
| P1-08 诊断CLI和开发工具 | 已完成 | 在完整 UI 开发前提供统一调试入口 | P1-04 至 P1-07 | `src/ai_arm_control/diagnostics/armctl.py`、`tests/test_armctl_cli.py`、`README.md` | 默认使用模拟环境；不存在连接真实硬件的默认命令；输出内容清晰；错误时返回非零退出码；README 有完整使用示例 | CLI 若无安全开关可能误触真实资源 | 否 |
| P1-09 阶段一集成门禁 | 已完成 | 确认阶段一整体稳定，再开始 JxbService 真实适配器 | P1-00 至 P1-08 | `reports/phase-1-report.md`、`reports/test-results.md`、`reports/known-risks.md` | `pytest` 全部通过；`ruff check .` 通过；CLI 正常启动；模拟器全部场景通过；无真实硬件访问；无未说明的临时实现 | 真实服务行为与模拟器差异待验证 | 否 |
| P1-GAP 摄像头模拟器补齐 | 已完成 | 补齐阶段一原始清单中的离线摄像头模拟器 | P1-09 | `src/ai_arm_control/simulators/camera.py`、`tests/test_camera_simulator.py`、`reports/phase-1-camera-simulator-gap-closure.md` | 纯内存生成 RGB24 帧；支持打开/关闭、帧序号、屏幕区域裁剪、历史记录；不访问真实摄像头 | 模拟画面不代表真实摄像头成像效果 | 否 |

## 当前停止点

P1-09 完成后立即停止。不得自动开始真实 JxbService 适配器。

## 公共接口修改记录

| 日期 | 任务包 | 接口名 | 修改内容 | 原因 | 影响范围 |
|---|---|---|---|---|---|
| 2026-06-13 | P1-01 | `StandardDeviceAPI` | 建立草案：`get_status`、`execute`、`load_calibration`、`health_check` | 统一所有设备动作入口，禁止业务层直接调用 JxbService | P1-03 数据模型、P1-06 模拟器、P1-07 测试 |
| 2026-06-13 | P1-01 | `DeviceCommand` | 建立命令草案字段：命令 ID、设备 ID、命令类型、参数、安全模式、来源、创建时间 | 为命令调度和追踪提供公共输入模型 | P1-03 数据模型、P1-05 命令追踪 |
| 2026-06-13 | P1-01 | `CommandResult` | 建立结果草案字段：命令 ID、状态、适配器、开始/结束时间、错误信息、追踪 ID、诊断信息 | 为统一执行结果、异常和日志提供输出模型 | P1-03 数据模型、P1-05 日志异常 |
| 2026-06-13 | P1-01 | `DeviceStatus` | 建立状态草案字段和模式候选值：`SIMULATED`、`AUTO`、`MANUAL`、`SWITCHING`、`OFFLINE`、`FAULT` | 支持模拟优先、设备锁和人工/自动模式边界 | P1-03 数据模型、P1-06 模拟器 |
| 2026-06-13 | P1-03 | `DeviceConfig` | 落地设备配置模型：设备 ID、名称、连接信息、安全限制、模式、启用状态和元数据 | 统一配置系统、模拟器和设备注册的数据格式 | P1-04 配置系统、P1-06 模拟器 |
| 2026-06-13 | P1-03 | `ArmCommand` | 将 P1-01 `DeviceCommand` 草案落地为 `ArmCommand`：命令 ID、设备 ID、命令类型、参数、模式、追踪 ID、创建时间 | 统一设备动作输入模型，保持动作仍需经过统一接口 | P1-05 命令追踪、P1-06 模拟器 |
| 2026-06-13 | P1-03 | `CommandResult` | 落地结果模型：命令 ID、设备 ID、状态、成功标记、错误信息、追踪 ID、时间和数据 | 统一命令执行结果、日志和异常输出 | P1-05 日志异常、P1-07 测试 |
| 2026-06-13 | P1-03 | `DeviceState` | 落地枚举状态：`OFFLINE`、`CONNECTING`、`IDLE`、`EXECUTING`、`SWITCHING`、`MANUAL`、`RECOVERING`、`FAULT`、`STOPPED` | 禁止状态使用随意字符串 | P1-05 追踪、P1-06 模拟器、P1-08 CLI |
| 2026-06-13 | P1-03 | `OperationMode` | 落地枚举模式：`SIMULATED`、`AUTO`、`MANUAL`、`MAINTENANCE`、`DISABLED` | 禁止模式使用随意字符串，保持真实硬件默认关闭 | P1-04 配置系统、P1-06 模拟器 |
| 2026-06-13 | P1-03 | `SafetyLimits` | 落地安全限制模型，默认 `allow_real_hardware=False` | 明确真实硬件模式默认关闭 | P1-04 配置系统、P1-08 诊断 CLI |
| 2026-06-13 | P1-03 | `ConnectionInfo` | 落地连接信息模型，仅记录连接描述，不实现 HTTP 或串口逻辑 | 为后续配置和适配器提供纯数据契约 | P1-04 配置系统、P1-06 模拟器 |
| 2026-06-13 | P1-03 | `ErrorInfo` | 落地错误信息模型：错误码、消息、可恢复标记和详情 | 为异常、日志和命令结果提供统一错误格式 | P1-05 日志异常 |
| 2026-06-13 | P1-04 | `AppConfig` | 落地主配置模型：版本、环境、设备列表和元数据 | 统一配置加载入口，避免硬编码设备参数 | P1-06 模拟器、P1-08 CLI |
| 2026-06-13 | P1-04 | `StandardizedDeviceConfig` | 落地标准化设备配置：公共设备模型、硬件描述、标定配置和原始旧数据副本 | 统一旧格式和新格式转换输出 | P1-06 模拟器、P1-07 测试 |
| 2026-06-13 | P1-04 | `HardwareConfig` | 落地 COM、服务 URL、摄像头名称、USB 唯一标识等可配置硬件字段 | 禁止在代码中硬编码设备参数 | P1-08 诊断 CLI |
| 2026-06-13 | P1-04 | `CalibrationConfig` | 落地屏幕区域、触控笔下降距离、可控区和机械臂极限范围等标定字段 | 支持旧 `1.json` 标准化转换 | P1-06 模拟器、P1-07 测试 |
| 2026-06-13 | P1-04 | `RawLegacyData` | 保存旧 `config.json` 和 `1.json` 原始数据副本 | 确保可追溯且不修改原始 JSON | P1-08 诊断 CLI |
| 2026-06-13 | P1-05 | `AIArmControlError` | 建立统一异常基类，包含稳定 `error_code`、消息、详情和 `to_dict()` | 统一错误分类，避免异常静默吞掉 | P1-06 模拟器、P1-08 CLI |
| 2026-06-13 | P1-05 | `ConfigurationError` | 建立配置错误统一异常，并让 `ConfigError` 继承该异常 | 将配置系统纳入统一异常体系 | P1-04 配置系统、P1-08 CLI |
| 2026-06-13 | P1-05 | `CommandTrace` | 落地命令追踪字段：命令 ID、设备 ID、动作类型、时间、耗时、状态、模式、结果和错误码 | 支持同一命令全流程同一 ID，并便于故障定位 | P1-06 模拟器、P1-07 测试 |
| 2026-06-13 | P1-05 | `CommandTraceResult` | 落地追踪结果枚举：`PENDING`、`RUNNING`、`SUCCEEDED`、`FAILED`、`TIMEOUT`、`BLOCKED` | 禁止追踪结果使用随意字符串 | P1-06 模拟器、P1-08 CLI |
| 2026-06-13 | P1-05 | `setup_logging` | 建立控制台和轮转文件日志初始化，并默认脱敏 | 支持排障日志且避免敏感信息进入日志 | P1-08 诊断 CLI、P1-09 门禁 |
| 2026-06-13 | P1-06 | `JxbServiceSimulator` | 落地纯内存模拟器：打开虚拟 COM、返回虚拟资源号、接收 XY/Z、关闭资源、保存位置、查询历史和服务重启 | 支持后续控制模块在不连接真实机械臂的情况下开发测试 | P1-07 自动化测试、P1-08 CLI |
| 2026-06-13 | P1-06 | `JxbSimulatorConfig` | 落地模拟器配置：虚拟资源号、故障模式、占用端口、随机种子和随机故障概率 | 每个故障可通过配置稳定复现 | P1-07 自动化测试 |
| 2026-06-13 | P1-06 | `JxbFaultMode` | 落地故障枚举：`NONE`、`TIMEOUT`、`INVALID_RESOURCE`、`PORT_BUSY`、`SERVICE_RESTART`、`RANDOM_FAULT` | 禁止故障模式使用随意字符串 | P1-07 自动化测试 |
| 2026-06-13 | P1-06 | `JxbServiceClient` | 建立 URL scheme 切换边界：`simulator://` 走内存模拟器，HTTP(S) 在 P1-06 中拒绝真实访问 | 让业务代码未来只修改 URL 即可切换模拟和真实服务 | P1-07 自动化测试、P1-08 CLI |
| 2026-06-13 | P1-07 | `DeviceStateMachine` | 落地离线状态机：状态转换校验和自动命令准入检查 | 覆盖非法状态转换、人工模式拒绝自动任务等阶段二前置测试场景 | P1-08 CLI、P1-09 门禁 |
| 2026-06-13 | P1-07 | `CalibrationConfig` | 增强坐标范围校验：可控区和屏幕区域必须满足左不大于右、上不大于下 | 覆盖非法坐标范围测试场景 | P1-08 CLI、P1-09 门禁 |
| 2026-06-13 | P1-07 | `SafetyLimits` | 增强坐标限制校验：`min_x <= max_x`、`min_y <= max_y` | 防止非法坐标范围进入后续控制流程 | P1-08 CLI、P1-09 门禁 |
| 2026-06-13 | P1-07 | `JxbServiceSimulator` | 调整服务重启后的资源号生成：重启后新打开资源不得复用旧资源号 | 覆盖程序重启后不复用旧资源号测试场景 | P1-08 CLI、P1-09 门禁 |
| 2026-06-13 | P1-08 | `armctl` | 新增诊断 CLI：`config-check`、`show-device`、`simulator-start`、`simulator-status`、`simulator-reset`、`run-self-test` | 在 UI 完成前提供统一离线调试入口 | P1-09 门禁 |
| 2026-06-13 | P1-08 | `pyproject.toml` scripts | 注册 `armctl = ai_arm_control.diagnostics.armctl:main` | 让诊断命令可以作为标准控制台脚本运行 | P1-09 门禁 |
| 2026-06-14 | P1-GAP | `CameraSimulator` | 新增纯内存摄像头模拟器：`open`、`close`、`capture_frame`、`capture_screen_region`、`get_history` | 补齐阶段一原始清单中的摄像头模拟器，并为阶段三离线裁剪和标定提供输入 | 阶段三摄像头与标定 |
| 2026-06-14 | P1-GAP | `CameraFrame` / `crop_frame` | 新增 RGB24 帧模型和矩形裁剪函数 | 支持手机屏幕区域裁剪和离线图像坐标测试 | 阶段三摄像头画面、屏幕区域裁剪 |

## 阶段二当前任务包记录

任务包：P2-11 实机低风险验收第5步首段。

状态：第5步自动/人工切换按修订规则通过，服务重启恢复仍阻塞。多区域 100 次点击已完成；服务重启恢复因仓库规则禁止启动/停止 JxbService 且当前 Codex 进程非管理员提升态而未执行；自动/人工切换低风险资源周期观察到资源号数字复用 `1688`，按新规则以本地 lease/generation 增加判定，通过。

范围：服务重启恢复只做规则判定，不执行真实服务重启；自动/人工切换只做资源释放和重新获取，不发动作、不运行人工软件、不自动重试。

交付物：

- `reports/phase-2-p2-11-step1-connection.json`：第1步连接测试机器可读结果。
- `reports/phase-2-p2-11-step1-connection.md`：第1步连接测试报告。
- `reports/phase-2-p2-11-step1-blocker-analysis.md`：第1步阻塞分析和后续采集要求。
- `reports/jxbservice-readonly-check-after-p2-11-step1.json`：第1步后的只读复查结果。
- `reports/phase-2-p2-11-step1-recapture.json`：第1步重采集机器可读结果，包含 `exc.details`。
- `reports/phase-2-p2-11-step1-recapture.md`：第1步重采集报告。
- `reports/jxbservice-readonly-check-after-p2-11-step1-recapture.json`：重采集后的只读复查结果。
- `reports/phase-2-p2-11-com4-zero-diagnosis.md`：关闭人工软件后的 COM4 返回 `"0"` 排查结论和用户侧处理方案。
- `reports/jxbservice-readonly-check-after-fix.json`：修复后第1步前置只读检查。
- `reports/p2-11-gate-after-fix.json`：修复后第1步前置 gate。
- `reports/phase-2-p2-11-step1-after-fix.json`：修复后第1步连接生命周期机器可读结果。
- `reports/phase-2-p2-11-step1-after-fix.md`：修复后第1步连接生命周期报告。
- `reports/jxbservice-readonly-check-after-p2-11-step1-after-fix.json`：修复后第1步后的只读复查结果。
- `reports/jxbservice-readonly-check-before-p2-11-step1-retest.json`：本轮重测前只读检查。
- `reports/phase-2-p2-11-step1-retest.json`：本轮第1步连接重测机器可读结果。
- `reports/phase-2-p2-11-step1-retest.md`：本轮第1步连接重测报告。
- `reports/phase-2-p2-11-step1-regression-diagnosis.md`：第1步从历史通过回退到 `"0"` 的只读复查结论。
- `reports/jxbservice-readonly-check-after-p2-11-step1-retest.json`：本轮重测后只读复查结果。
- `reports/jxbservice-readonly-check-before-p2-11-step1-service-path-fix.json`：服务路径修正后第1步前置只读检查。
- `reports/p2-11-gate-before-step1-service-path-fix.json`：服务路径修正后第1步前置 gate。
- `reports/phase-2-p2-11-step1-service-path-fix.json`：服务路径修正后第1步连接生命周期机器可读结果。
- `reports/phase-2-p2-11-step1-service-path-fix.md`：服务路径修正后第1步连接生命周期报告。
- `reports/jxbservice-readonly-check-after-p2-11-step1-service-path-fix.json`：服务路径修正后第1步后置只读复查。
- `reports/phase-2-p2-11-step1-retest-latest.json`：本轮第1步最新重测机器可读结果。
- `reports/phase-2-p2-11-step1-retest-latest.md`：本轮第1步最新重测报告。
- `reports/jxbservice-readonly-check-after-p2-11-step1-retest-latest.json`：本轮第1步最新重测后只读复查。
- `reports/phase-2-p2-11-step2-small-xy.json`：第2步小范围 XY 机器可读结果。
- `reports/phase-2-p2-11-step2-small-xy.md`：第2步小范围 XY 报告。
- `reports/jxbservice-readonly-check-after-p2-11-step2-small-xy.json`：第2步后置只读复查。
- `configs/jxbservice.readonly.json`：收紧实机低风险验收安全限位，X/Y 为 `0..140`，Z 元数据为 `0..7`。
- `reports/jxbservice-readonly-check-before-p2-11-step3-small-z.json`：第3步前置只读检查。
- `reports/phase-2-p2-11-step3-small-z.json`：第3步小范围 Z 机器可读结果。
- `reports/phase-2-p2-11-step3-small-z.md`：第3步小范围 Z 报告。
- `reports/jxbservice-readonly-check-after-p2-11-step3-small-z.json`：第3步后置只读复查。
- `reports/phase-2-p2-11-step3-small-z-repeat3.json`：第3步重复 3 次观察机器可读结果。
- `reports/phase-2-p2-11-step3-small-z-repeat3.md`：第3步重复 3 次观察报告。
- `reports/jxbservice-readonly-check-after-p2-11-step3-small-z-repeat3.json`：重复观察后置只读复查。
- `reports/phase-2-p2-11-step3-z2-observation.json`：第3步 `Z2 -> Z0` 单次观察机器可读结果。
- `reports/phase-2-p2-11-step3-z2-observation.md`：第3步 `Z2 -> Z0` 单次观察报告。
- `reports/jxbservice-readonly-check-after-p2-11-step3-z2-observation.json`：`Z2` 观察后置只读复查。
- `reports/phase-2-p2-11-step4-single-click.json`：第4步单次点击机器可读结果。
- `reports/phase-2-p2-11-step4-single-click.md`：第4步单次点击报告。
- `reports/jxbservice-readonly-check-after-p2-11-step4-single-click.json`：第4步后置只读复查。
- `reports/phase-2-p2-11-step5-reset-5clicks.json`：第5步复位后 5 次点击机器可读结果。
- `reports/phase-2-p2-11-step5-reset-5clicks.md`：第5步复位后 5 次点击报告。
- `reports/jxbservice-readonly-check-after-p2-11-step5-reset-5clicks.json`：第5步首段后置只读复查。
- `reports/phase-2-p2-11-step5-20clicks.json`：第5步 20 次点击机器可读结果。
- `reports/phase-2-p2-11-step5-20clicks.md`：第5步 20 次点击报告。
- `reports/jxbservice-readonly-check-after-p2-11-step5-20clicks.json`：第5步 20 次点击后置只读复查。
- `reports/phase-2-p2-11-step5-multiarea-100clicks.json`：第5步多区域 100 次点击机器可读结果。
- `reports/phase-2-p2-11-step5-multiarea-100clicks.md`：第5步多区域 100 次点击报告。
- `reports/jxbservice-readonly-check-after-p2-11-step5-multiarea-100clicks.json`：第5步多区域 100 次点击后置只读复查。
- `reports/jxbservice-readonly-check-before-p2-11-step5-recovery-mode.json`：服务重启恢复/模式切换前置只读检查。
- `reports/phase-2-p2-11-step5-mode-switch-resource-cycle.json`：自动/人工切换低风险资源周期机器可读结果。
- `reports/jxbservice-readonly-check-after-p2-11-step5-mode-switch-resource-cycle.json`：自动/人工切换后置只读复查。
- `reports/phase-2-p2-11-step5-recovery-mode-switch.md`：服务重启恢复与自动/人工切换报告。
- `reports/phase-2-p2-11-service-restart-permission-check.md`：服务重启恢复权限检查报告。
- `src/ai_arm_control/modes/mode_switch.py`：自动/人工切换改为记录并校验连接 generation，而不是要求资源号数字变化。
- `src/ai_arm_control/recovery/watchdog.py`：连接恢复改为记录并校验连接 generation，而不是要求资源号数字变化。
- `tests/test_mode_switch.py`：覆盖资源号数字复用但 generation 增加时自动恢复通过。
- `tests/test_watchdog_recovery.py`：覆盖资源号数字复用但 generation 增加时恢复通过。
- `docs/phase-2-mode-switching.md`：更新自动/人工切换资源生命周期规则。
- `docs/phase-2-watchdog-recovery.md`：更新恢复资源生命周期规则。
- `reports/phase-2-p2-11-resource-lease-generation-update.md`：资源号复用规则修订报告。
- `reports/phase-2-p2-11-subproject-handoff-resource-lease-generation.md`：给阶段二机械臂适配器子项目的交接说明。
- `src/ai_arm_control/clients/jxb_service.py`：增强资源号解析失败时的响应摘要。
- `tests/test_jxb_http_client.py`：新增非整数资源号响应摘要测试。
- `PLANS.md`：记录第1步从阻塞到通过的状态变化。

验收结果：

- 授权连接测试：打开 COM 请求执行 1 次，返回内容无法解析为整数资源号，未得到有效资源号。
- 授权重采集：打开 COM 请求执行 1 次，`exc.details.raw_response` 为 `"0"`，未得到有效资源号。
- 解析修正：客户端支持 JSON 字符串正整数资源号，但继续拒绝 `"0"` 和非正数资源号。
- 修复后授权重测：打开 COM 请求执行 1 次，获得资源号 `1172`，关闭资源请求执行 1 次，关闭资源原始返回 `"1"`。
- 用户确认控制软件路径为 `C:\Users\s1061\Desktop\AI-Multi-Device-Control\references\main软件发客户-20260531\main`，已记录到 `configs/jxbservice.readonly.json` 的 `metadata.control_software_path`。
- 本轮授权重测：控制软件路径只读存在性检查通过；打开 COM 请求执行 1 次，HTTP `200 OK`，返回 `"0"`，未得到有效资源号，未执行关闭资源。
- 只读复查：Windows 服务 `JxbService` 当前实际注册路径仍为 `C:\Users\s1061\Desktop\AI控制端\main\WindowsService1.exe`，与项目记录的控制软件路径不一致。
- 只读复查：曾枚举到 `main.exe` 进程来自项目记录的控制软件路径，随后未持续出现；是否短暂占用 `COM4` 待验证。
- 服务路径修正后复查：`JxbService` 实际服务路径已为 `C:\Users\s1061\Desktop\AI-Multi-Device-Control\references\main软件发客户-20260531\main\WindowsService1.exe`。
- 服务路径修正后授权重测：打开 COM 请求执行 1 次，获得资源号 `1476`，关闭资源请求执行 1 次，关闭资源原始返回 `"1"`。
- 最新授权重测：打开 COM 请求执行 1 次，获得资源号 `1500`，关闭资源请求执行 1 次，关闭资源原始返回 `"1"`。
- 第2步授权小范围 XY：打开 COM 请求执行 1 次，获得资源号 `1212`，发送 `X50Y50` 1 次，关闭资源请求执行 1 次。
- 安全限位更新：X/Y 收紧为 `0..140`；Z 元数据限位为 `0..7`。
- 第3步授权小范围 Z：打开 COM 请求执行 1 次，获得资源号 `1536`，发送 `Z1` 1 次，发送 `Z0` 1 次，关闭资源请求执行 1 次。
- 第3步重复观察：打开 COM 请求执行 1 次，获得资源号 `1448`，执行 3 次 `Z1 -> Z0`，共 6 条 Z 指令，关闭资源请求执行 1 次。
- 第3步 Z2 单次观察：打开 COM 请求执行 1 次，获得资源号 `1548`，执行 `Z2 -> Z0`，关闭资源请求执行 1 次。
- 第4步单次点击：打开 COM 请求执行 1 次，获得资源号 `1564`，执行 `X50Y50 -> Z2 -> Z0 -> X50Y50`，关闭资源请求执行 1 次。
- 第5步首段：打开 COM 请求执行 1 次，获得资源号 `1544`，执行 `X0Y0Z0` 复位 1 次，再执行 5 次 `X50Y50 -> Z2 -> Z0`，关闭资源请求执行 1 次。
- 第5步 20 次点击：打开 COM 请求执行 1 次，获得资源号 `1592`，执行 20 次 `X50Y50 -> Z2 -> Z0`，关闭资源请求执行 1 次。
- 第5步多区域 100 次点击：打开 COM 请求执行 1 次，获得资源号 `1632`，循环点位 `X50Y50`、`X80Y50`、`X80Y80`、`X50Y80`、`X65Y65`，执行 100 次移动点击抬起，关闭资源请求执行 1 次。
- 服务重启恢复：未执行真实停止/启动；仓库规则禁止启动 JxbService 和管理员权限操作。
- 服务重启恢复权限检查：`JxbService` 当前 `Running` 且 `CanStop=true`，但当前 Codex 进程不是管理员提升态，`net session` 返回 `Access is denied`。
- 自动/人工切换资源周期：初始自动打开资源号 `1688`，本地 generation `1`；转人工关闭资源后，回自动重新打开仍得到 `1688`，本地 generation `2`，最终已关闭资源；按新规则通过。
- 资源生命周期规则修订：真实 JxbService 允许复用资源号数字；本地程序必须通过新的 lease/generation 区分每次重新打开 COM。
- 自动/人工切换代码修订：回自动时不再要求 `current_resource_id != previous_resource_id`，改为要求 `current_generation > previous_generation`。
- 恢复代码修订：重连时不再要求资源号数字变化，改为要求连接 generation 变化。
- 点击命令：0 次。
- 回零命令：0 次。
- 自动重试：0 次。
- `python -m ai_arm_control.diagnostics.armctl readonly-check --config configs\jxbservice.readonly.json --output reports\jxbservice-readonly-check-after-p2-11-step1.json`：完成，服务仍在线。
- `python -m ai_arm_control.diagnostics.armctl readonly-check --config configs\jxbservice.readonly.json --output reports\jxbservice-readonly-check-after-p2-11-step1-recapture.json`：完成，服务仍在线。
- `python -m ai_arm_control.diagnostics.armctl readonly-check --config configs\jxbservice.readonly.json --output reports\jxbservice-readonly-check-after-fix.json`：完成，服务在线。
- `python -m ai_arm_control.diagnostics.armctl p2-11-gate --readonly-report reports\jxbservice-readonly-check-after-fix.json --output reports\p2-11-gate-after-fix.json`：完成，`READY`。
- 修复后第1步连接生命周期脚本：完成，打开 `COM4` 一次、关闭资源一次、未发动作。
- `python -m ai_arm_control.diagnostics.armctl readonly-check --config configs\jxbservice.readonly.json --output reports\jxbservice-readonly-check-after-p2-11-step1-after-fix.json`：完成，服务仍在线。

风险：

- 早先打开 COM 返回 `"0"`，其语义待验证；不得直接解释为成功。
- `"0"` 可识别为 JSON 字符串数字，但不是有效资源号。
- 最新重测从历史通过状态回到 `"0"`，疑似环境状态、服务运行目录、COM 占用或人工软件互斥问题，待验证。
- 第1步只证明连接生命周期通过，不代表运动指令、点击、回零或摄像头链路通过。
- 第2步只确认服务返回了 HTTP 响应，不代表物理移动完成；需要人工观察确认。
- Z 是否全程保持抬起，需要人工观察确认。
- 第3步只确认服务返回了 HTTP 响应，不代表物理 Z 动作完成；需要人工观察确认。
- `Z1` 实际下降距离和 `Z0` 抬起效果待人工确认。
- 第4步只确认单次点击序列收到 HTTP 响应，不代表物理点击成功；需要人工观察确认。
- 第5步首段只确认 5 次点击序列收到 HTTP 响应，不代表每次物理点击成功；需要人工观察确认。
- 第5步 20 次点击只确认 20 次点击序列收到 HTTP 响应，不代表每次物理点击成功；需要人工观察确认。
- 第5步多区域 100 次点击只确认 100 次点击序列收到 HTTP 响应，不代表每次物理点击成功；需要人工观察确认。
- 服务重启恢复实测在当前仓库规则下阻塞，不能由 Codex 执行真实服务重启。
- 即使服务 ACL 允许管理员控制，当前进程未提升，不能执行服务停止/启动。
- 真实 JxbService 允许同一 COM 关闭后重开返回相同 resource_id；后续代码必须以 generation/lease 区分连接生命周期，不能仅用 resource_id 数字变化判断新连接。
- JxbService 当前运行目录或服务注册路径是否缺少 COM4 对应完整运行资料，待验证。

## 公共接口修改记录补充

| 日期 | 任务包 | 接口名 | 修改内容 | 原因 | 影响范围 |
|---|---|---|---|---|---|
| 2026-06-13 | P2-01 | `probe_jxbservice.py` CLI | 新增独立探索脚本参数：`--dry-run`、`--simulator`、`--live`、`--allow-motion`、`--output` | 在业务代码之外记录协议请求计划和模拟样本，避免边开发边猜测服务行为 | `scripts/`、`reports/`、后续 P2-02 待验证输入 |
| 2026-06-13 | P2-02 | `JxbServiceClient` HTTP | 新增纯 HTTP 客户端：`health_check`、`open_port`、`send_command`、`close_resource` | 隔离 JxbService HTTP 通信层，避免业务代码直接拼接请求 | 后续 P2-03 资源号管理器、P2-06 标准动作层 |
| 2026-06-13 | P2-02 | `JxbServiceClientConfig` | 新增 `base_url`、`connect_timeout_s`、`read_timeout_s` | 统一 HTTP 基础 URL 和超时配置 | HTTP 客户端测试、后续配置接入 |
| 2026-06-13 | P2-03 | `ArmConnectionManager` | 新增 `connect`、`disconnect`、`reconnect`、`invalidate`、`is_connected`、`get_resource_id` 和 `snapshot` | 统一管理 COM、资源号和连接生命周期，避免业务层直接持有可写资源号 | 后续 P2-04 状态机安全门、P2-06 标准动作层 |
| 2026-06-13 | P2-03 | `ArmConnectionInfo` | 新增连接快照字段：COM、资源号、连接时间、代次、最后请求时间、状态和失效原因 | 为诊断、恢复和资源生命周期测试提供只读快照 | 后续诊断 CLI、异常恢复 |
| 2026-06-14 | P2-04 | `DeviceStateMachine` | 收紧允许转换为 P2-04 指定路径，移除未授权的 `STOPPED` 自动转出和额外故障跳转 | 确保所有状态转换在进入动作层前可预测且可审计 | 状态机测试、后续安全门和动作层 |
| 2026-06-14 | P2-04 | `SafetyGate` | 新增 `validate(command, context)`，检查状态、模式、坐标、单次移动距离、Z 下降、真实硬件授权和未完成命令 | 在 HTTP 层之前统一拒绝不安全动作 | 后续 P2-05 队列、P2-06 标准动作层 |
| 2026-06-14 | P2-04 | `SafetyGateConfig` / `SafetyGateContext` | 新增安全门配置和运行上下文 | 将安全限制、当前状态和运行时上下文显式传入安全门 | 安全门测试、后续动作准入 |
| 2026-06-14 | P2-05 | `ActionQueue` | 新增单设备单消费者 FIFO 队列：`submit`、`get`、`current_task`、`stop_accepting`、`clear_pending`、`wait_until_idle`、`shutdown`、`records` | 保证同一台机械臂底层指令严格串行，支持关闭和诊断查询 | 后续 P2-06 标准动作层、P2-08 异常恢复 |
| 2026-06-14 | P2-05 | `QueuedCommandStatus` | 新增命令状态：`PENDING`、`QUEUED`、`RUNNING`、`SUCCEEDED`、`FAILED`、`CANCELLED`、`UNKNOWN_RESULT` | 统一队列命令生命周期和未知结果表达 | 队列测试、后续诊断 CLI |
| 2026-06-14 | P2-05 | `CommandQueueRecord` | 新增队列记录：命令、序号、状态、排队/开始/结束时间、结果和错误信息 | 支持 FIFO 可审计、当前任务查询和最终状态检查 | 后续报告、恢复和诊断 |
| 2026-06-14 | P2-06 | `StandardArmActionLayer` | 新增标准动作：`move_xy`、`move_z`、`move_xyz`、`press`、`release`、`click`、`home`、`safe_home` | 在连接、HTTP、安全门和队列之上提供统一动作入口 | 后续 P2-07 模式切换、P2-09 诊断 CLI |
| 2026-06-14 | P2-06 | `StandardArmActionConfig` | 新增动作时间和位置配置：等待时间、按压保持、Z 上下位置、Home 位置、等待超时和队列配置 | 保证动作时间全部配置化 | 标准动作层测试、后续配置接入 |
| 2026-06-14 | P2-06 | `StandardArmActionResult` / `StandardArmSubAction` | 新增动作结果和子步骤记录，包含状态、子步骤、最终状态和位置快照 | 支持点击失败后的已完成步骤记录和诊断 | 后续报告、异常恢复 |
| 2026-06-14 | P2-07 | `ModeSwitchManager` | 新增 `switch_to_manual` 和 `switch_to_auto` | 统一自动/人工互斥切换流程 | 后续 P2-08 异常恢复、P2-09 诊断 CLI |
| 2026-06-14 | P2-07 | `ModeSwitchRecord` | 新增切换审计记录：操作人、时间、原因、前后状态、前后模式、资源释放、未完成命令和资源号 | 满足模式切换可追溯要求 | 报告、诊断 CLI |
| 2026-06-14 | P2-07 | `ActionQueue.submit(system=True)` | 新增系统维护命令通道，停止接收普通任务后仍允许切换流程自己的抬笔和 safe_home 经队列执行 | 保证切换清理动作不绕过串行队列，同时拒绝新普通动作 | 模式切换、后续恢复流程 |
| 2026-06-14 | P2-08 | `WatchdogRecoveryManager` | 新增 `check`、`recover_connection`、`handle_invalid_resource`、`graceful_shutdown`、`startup_recovery` 和请求结果记录 | 统一服务、连接、队列和程序异常恢复策略 | 后续 P2-09 诊断 CLI、P2-12 集成门禁 |
| 2026-06-14 | P2-08 | `RuntimeResourceLease` | 新增运行期资源标记文件读写和清理 | 支持正常退出资源释放和异常退出后启动检测 | 恢复测试、后续诊断报告 |
| 2026-06-14 | P2-08 | `WatchdogReport` | 新增恢复报告字段：状态、动作、检查时间、服务在线、连接有效、失败计数、资源号、状态和详情 | 支持恢复审计和诊断输出 | 后续 P2-09 诊断 CLI |
| 2026-06-14 | P2-09 | `armctl` | 新增 `service-check`、`connect`、`status`、`move`、`z`、`click`、`home`、`disconnect`、`mode manual`、`mode auto`、`self-test` | 完整 UI 前提供统一、安全的调试入口 | README、CLI 测试、后续验收工具 |
| 2026-06-14 | P2-09 | `armctl` 三重保护 | 新增配置 `live_hardware_enabled`、`--live`、`--confirm-motion` 三重检查；缺任意一项输出 dry-run | 防止误触真实硬件动作 | 所有动作 CLI |
| 2026-06-14 | P2-10 | `armctl readonly-check` | 新增只读检查命令，输出 `reports/jxbservice-readonly-check.json` | 第一次接触真实环境时只验证服务存在，不打开 COM 或发送动作 | P2-10 报告、后续 P2-11 准入判断 |
| 2026-06-14 | P2-10 | `configs/jxbservice.readonly.json` | 新增只读真实环境配置：URL 指向 `127.0.0.1:8082`，COM 为 `COM4`，真实硬件动作授权关闭 | 修正真实环境配置侧前置条件，同时保持只读安全边界 | P2-10 只读检查 |
| 2026-06-14 | P2-11 | `evaluate_p2_11_gate` | 新增离线准入判断：读取 P2-10 报告，输出 `READY` 或 `BLOCKED`、阻塞原因和安全标记 | 将 P2-11 前置条件失败明确表达为项目内门禁结果，避免误进入真实动作阶段 | P2-11 gate、诊断 CLI、报告 |
| 2026-06-14 | P2-11 | `armctl p2-11-gate` | 新增命令，默认读取 `reports/jxbservice-readonly-check.json` 并写入 `reports/p2-11-gate.json` | 让子项目用单条命令判断能否进入 P2-11，不重复访问真实环境 | P2-11 准入判断 |
| 2026-06-14 | P2-10 | `armctl readonly-check` | 调整默认行为：只检查 TCP 监听和服务状态，HTTP path 需显式 `--check-http-path` | 空参数 HTTP 请求会进入服务动作处理器并触发服务端 DLL 异常，不能作为默认只读检查 | P2-10 报告、P2-11 gate |
| 2026-06-14 | P2-11 | `JxbServiceClient.open_port` | 非整数资源号异常 details 新增 `response_summary`，包含长度、repr 预览、hex 预览和整数判断 | P2-11 第1步失败报告未保存 raw response，后续需要足够证据分析真实返回格式 | HTTP 客户端、P2-11 第1步重采集 |
| 2026-06-14 | P2-11 | `summarize_response_text` | 新增响应文本摘要工具 | 统一记录服务返回值，不把不明确返回解释为成功 | HTTP 客户端测试、后续诊断报告 |
| 2026-06-14 | P2-11 | `parse_resource_id_response` | 新增资源号解析函数，支持裸正整数和 JSON 字符串正整数，拒绝 `0`、负数和非整数 | 真实服务返回 `"0"`，需要明确区分“可解析格式”和“无效资源号” | HTTP 客户端、连接管理 |
| 2026-06-14 | P2-11 | `ModeSwitchRecord` | 新增 `previous_generation`、`current_generation`，自动/人工切换不再要求资源号数字变化，改为要求本地连接 generation 更新 | 真实 JxbService 关闭后重新打开同一 COM 可能复用资源号数字，资源生命周期应以本地 lease/generation 判断 | 模式切换、P2-11 自动/人工切换验收 |
| 2026-06-14 | P2-11 | `WatchdogRecoveryManager.recover_connection` | 恢复报告 details 新增 `previous_generation`、`current_generation`，重连不再要求资源号数字变化，改为要求 generation 更新 | 避免真实服务复用资源号时误判恢复失败，同时仍禁止复用旧本地连接 lease | 异常恢复、服务重启恢复验收 |
## P2-12 阶段二集成门禁

状态：部分完成。

执行日期：2026-06-14。

范围：仅执行模拟测试、静态检查、干运行协议探针、模拟 CLI 检查和报告审计。本轮未访问 `127.0.0.1:8082`，未打开 COM，未发送真实机械臂动作，未运行第三方 EXE/DLL/BAT，未进行管理员权限操作。

结果：

- `python -m pytest`：通过，`150 passed in 7.71s`。
- `python -m ruff check .`：通过，`All checks passed!`。
- `python scripts\probe_jxbservice.py --dry-run --output reports\phase-2-p2-12-probe-dry-run.json`：通过，未访问真实服务、未打开 COM、未发送动作。
- `python -m ai_arm_control.diagnostics.armctl self-test`：通过，模拟器模式。
- `python -m ai_arm_control.diagnostics.armctl config-check --config configs\app.example.json`：通过，`live_hardware_enabled=false`。

门禁结论：

- 阶段二离线软件门禁通过。
- P2-11 实机低风险连接、XY、Z、单次点击、重复点击、多区域 100 次点击和自动/人工资源周期报告已记录。
- 服务重启恢复仍未执行；原因是当前仓库规则禁止启动/停止 JxbService，且当前 Codex 进程不是管理员提升态。因此 P2-12 不能记录为无条件全量通过。

交付物：

- `reports/phase-2-report.md`
- `reports/phase-2-test-results.md`
- `reports/hardware-test-results.md`
- `reports/phase-2-known-risks.md`
- `reports/phase-2-p2-12-probe-dry-run.json`

接口与规则记录：

- 不新增阶段二公共接口。
- 资源生命周期继续采用 P2-11 修订规则：真实 JxbService 可复用同一个数字 `resource_id`；本地必须以新的 lease/generation 区分连接生命周期，且回自动或重连时 `current_generation > previous_generation`。

## 阶段三入口记录

状态：可以进入阶段三，但尚未开始阶段三任务包实现。

进入条件：

- 阶段一项目骨架已完成，并已补齐摄像头模拟器。
- 阶段二机械臂适配器离线软件门禁通过。
- P2-11 低风险硬件验收已覆盖连接、XY、Z、单次点击、重复点击、多区域 100 次点击和自动/人工资源周期。
- 服务重启恢复仍作为已知阻塞项记录，不阻塞摄像头与标定开发。

阶段三建议第一个任务包：

- P3-01 摄像头与标定离线基础。

建议范围：

- 使用 `CameraSimulator` 作为默认输入源。
- 定义摄像头帧接口和真实摄像头禁用边界。
- 导入现有两个 JSON。
- 实现手机屏幕区域裁剪。
- 实现图像坐标到机械臂坐标转换的离线模型。
- 建立九点点击测试的数据结构和误差统计，不直接发送真实点击。

安全边界：

- 默认不访问 USB 摄像头。
- 默认不打开 COM。
- 默认不发送机械臂动作。
- 真实摄像头采集和真实九点点击必须单独授权。

## 第二开发阶段：标定精度＋脚本动作闭环

### P2-00 第二阶段接口冻结与测试基线

状态：已完成。

执行日期：2026-06-14。

分支：`phase2/p2-00-interface-baseline`。

范围：

- 冻结机械臂适配器公开方法：`connect()`、`disconnect()`、`home()`、`move_xy(x, y)`、`pen_down(z)`、`pen_up()`、`stop()`、`get_status()`。
- 确认模拟配置和真实配置形态暴露相同接口。
- 确认配置文件位置：`configs/app.example.json` 和 `config/hardware.example.yaml`。
- 创建第二阶段测试目录：`tests/unit/`、`tests/hardware/`、`tests/fixtures/`。
- 创建标准测试图片和测试标定文件。
- 建立真实设备测试开关：`AI_ARM_CONTROL_ENABLE_HARDWARE_TESTS=1`。

安全边界：

- 未访问 `127.0.0.1:8082`。
- 未打开 COM 串口。
- 未访问 USB 摄像头。
- 未运行第三方 EXE、DLL、BAT、安装程序或服务程序。
- 未发送真实机械臂命令。
- `tests/hardware/` 默认跳过，必须显式设置环境变量才会执行。

交付物：

- `docs/phase2/interface_contract.md`
- `tests/unit/test_arm_interface_contract.py`
- `tests/hardware/test_hardware_switch.py`
- `tests/fixtures/standard_calibration_v2.json`
- `tests/fixtures/standard_screen.ppm`
- `config/hardware.example.yaml`
- `reports/phase-2-p2-00-interface-baseline.md`

检查命令：

- `python -m pytest tests\unit\test_arm_interface_contract.py`：通过，`5 passed`。
- `python -m pytest`：通过，`165 passed, 1 skipped`。
- `python -m ruff check .`：通过。

验收结果：

- 模拟适配器和真实配置形态适配器实现相同冻结接口。
- 默认测试不触发真实机械臂。
- 硬件测试必须显式设置环境变量。
- 原有阶段一、阶段二测试全部通过。

不包含：

- 标定。
- 摄像头。
- 动作脚本。
- 人工模式。

### P2-01 旧标定 JSON 导入与标准数据模型

状态：已完成。

执行日期：2026-06-14。

分支：`phase2/p2-01-legacy-calibration-import`。

范围：

- 解析旧标定 JSON 中的图像分辨率、手机屏幕区域、触控笔下降距离、机械臂活动极限、设备编号和服务地址。
- 解析旧 `config.json` 中的摄像头和机械臂绑定信息。
- 支持中文字段名称和部分英文别名。
- 处理字段缺失、字段类型错误和超出范围。
- 输出 `schema_version: "2.0"` 标准标定 JSON。

安全边界：

- 未修改 `references/`。
- 未访问 `127.0.0.1:8082`。
- 未打开 COM 串口。
- 未访问 USB 摄像头。
- 未运行第三方 EXE、DLL、BAT、安装程序或服务程序。
- 未发送真实机械臂命令。

交付物：

- `src/ai_arm_control/calibration/models.py`
- `src/ai_arm_control/calibration/legacy_importer.py`
- `src/ai_arm_control/calibration/validator.py`
- `src/calibration/models.py`
- `src/calibration/legacy_importer.py`
- `src/calibration/validator.py`
- `tests/unit/test_legacy_importer.py`
- `docs/calibration_schema.md`
- `tools/import_legacy_calibration.py`
- `reports/phase-2-p2-01-legacy-calibration-import.md`

检查命令：

- `python -m pytest tests\unit\test_legacy_importer.py`：通过，`9 passed`。
- `python -m tools.import_legacy_calibration references\main软件发客户-20260531\main\me_config\USBVID_1A86&PID_75235&2B28DE69&0&8USBVID_1A86&PID_75235&2B28DE69&0&8\1.json`：通过，输出标准 JSON。
- `python -m pytest`：通过，`174 passed, 1 skipped`。
- `python -m ruff check .`：通过。

验收结果：

- 正确旧文件可以成功导入。
- 错误文件给出明确错误信息。
- 原始文件不被修改。
- 导入后生成标准 JSON。
- 相同输入产生相同输出。

不包含：

- 坐标转换。
- 误差补偿。
- 实机点击。

### P2-CAL-01 旧标定 JSON 导入

状态：已完成。

执行日期：2026-06-14。

范围：

- 新增标准标定数据结构 `StandardCalibrationV2`，对应 `schema_version: "2.0"`。
- 新增旧 `config.json` 和旧标定 JSON 的只读导入函数。
- 将旧摄像头分辨率、手机屏幕区域、机械臂活动极限和点击下降高度转换为新标定格式。
- 保留 COM、摄像头名称、USB 唯一标识和本地服务地址为硬件绑定信息，但不作为运行时连接授权。
- 标记旧标定值仅为初始值，自动脚本精度仍待验证。

安全边界：

- 未修改 `references/`。
- 未访问 `127.0.0.1:8082`。
- 未打开 COM 串口。
- 未访问 USB 摄像头。
- 未运行第三方 EXE、DLL、BAT、安装程序或服务程序。
- 未发送真实机械臂命令。

交付物：

- `src/ai_arm_control/calibration/__init__.py`
- `src/ai_arm_control/calibration/legacy_importer.py`
- `tests/test_calibration_legacy_importer.py`

验收结果：

- 旧标定 JSON 可转换为：`schema_version`、`device_id`、`camera_size`、`screen_roi`、`arm_limits`、`press_z`、`mapping_matrix`、`correction_grid`、`average_error`、`maximum_error`。
- `mapping_matrix` 和 `correction_grid` 初始为空。
- `average_error` 和 `maximum_error` 初始为 `null`。
- 旧文件读取后不被修改。
- 非法屏幕区域会被拒绝。

检查命令：

- `python -m pytest tests\test_calibration_legacy_importer.py tests\test_config.py`
- `python -m ruff check src\ai_arm_control\calibration tests\test_calibration_legacy_importer.py`

风险：

- 旧 JSON 中的屏幕区域、下降高度、COM、摄像头绑定关系均来自参考资料或旧软件输出，只能作为初始值，实际精度待验证。
- 当前任务包未实现四点透视矫正、16 点标定、误差补偿、动作执行器或手机标定测试网页。
- 旧文件中不同机位的摄像头名称与用户描述可能不完全一致，真实绑定关系待验证。

未完成事项：

- P2-CAL-02 手机标定测试网页。
- P2-CAL-03 四点透视矫正。
- P2-CAL-04 16 点标定和局部补偿网格。

## 公共接口修改记录补充

| 日期 | 任务包 | 接口名 | 修改内容 | 原因 | 影响范围 |
|---|---|---|---|---|---|
| 2026-06-14 | P2-00 | `StandardDeviceAPI` | 冻结并补齐直接设备接口：`connect`、`disconnect`、`home`、`move_xy`、`pen_down`、`pen_up`、`stop`、`get_status` | 为后续坐标映射、标定、脚本动作闭环提供统一入口 | 机械臂适配器、单元测试、后续动作执行器 |
| 2026-06-14 | P2-00 | `JxbArmAdapter` | 新增冻结接口的便捷方法，内部仍通过 `execute()` 和现有安全校验执行 | 让模拟配置和真实配置形态共享同一公开接口，不绕过安全边界 | 适配器调用方、诊断和后续任务 |
| 2026-06-14 | P2-01 | `StandardCalibrationV2` | 拆分为独立 `models.py`，新增标准标定模型校验和稳定 `to_dict()` 输出 | 冻结旧标定导入后的内部统一数据格式 | 标定导入、后续坐标映射、误差报告 |
| 2026-06-14 | P2-01 | `HardwareBinding` | 新增硬件绑定模型，保存服务地址、COM、摄像头名称和 USB 唯一标识，不触发连接 | 将旧绑定信息作为只读导入元数据保留 | 配置迁移、诊断报告 |
| 2026-06-14 | P2-01 | `load_legacy_calibration` / `import_legacy_calibration` | 支持标定文件单独导入、可选旧设备配置、中文字段名和英文别名 | 满足离线 CLI 和不同版本旧 JSON 导入需求 | 标定 CLI、单元测试、后续标定流程 |
| 2026-06-14 | P2-01 | `tools.import_legacy_calibration` | 新增离线导入 CLI，默认输出标准标定 JSON，可选 `--full` 输出绑定和待验证信息 | 提供可重复验证命令，不访问真实硬件 | 开发验证、报告生成 |
| 2026-06-14 | P2-CAL-01 | `StandardCalibrationV2` | 新增标定 schema v2 数据结构：`schema_version`、`device_id`、`camera_size`、`screen_roi`、`arm_limits`、`press_z`、`mapping_matrix`、`correction_grid`、`average_error`、`maximum_error` | 将旧标定数据转换为后续坐标映射、误差补偿和脚本动作闭环的统一输入 | 后续标定、坐标转换、动作执行、报告输出 |
| 2026-06-14 | P2-CAL-01 | `import_legacy_calibration` / `load_legacy_calibration` | 新增旧 JSON 只读导入接口，返回标准标定数据、硬件绑定信息和待验证标记 | 旧 JSON 不能作为运行时配置直接改写，必须转换为项目标准模型 | 标定导入、配置迁移、离线测试 |
