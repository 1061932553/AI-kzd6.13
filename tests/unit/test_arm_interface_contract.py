from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from ai_arm_control.adapters import JxbArmAdapter, JxbArmAdapterOptions
from ai_arm_control.config import HardwareConfig, load_app_config
from ai_arm_control.models import DeviceState
from ai_arm_control.simulators import JxbServiceClient, JxbServiceSimulator, JxbSimulatorConfig

FROZEN_INTERFACE = {
    "connect",
    "disconnect",
    "home",
    "move_xy",
    "pen_down",
    "pen_up",
    "stop",
    "get_status",
}


def build_adapter(*, real_config_shape: bool = False) -> tuple[JxbArmAdapter, JxbServiceSimulator]:
    config = load_app_config("configs/app.example.json", env={}).devices[0]
    if real_config_shape:
        config = replace(
            config,
            hardware=HardwareConfig(
                com_port="COM_NEVER_OPEN",
                service_url="http://example.invalid",
                camera_name="USB Camera Disabled",
            ),
            device=replace(
                config.device,
                connection=replace(config.device.connection, is_simulated=False),
            ),
        )
    simulator = JxbServiceSimulator(JxbSimulatorConfig(virtual_resource_id=1001))
    return (
        JxbArmAdapter(
            config,
            client=JxbServiceClient("simulator://jxb", simulator=simulator),
            options=JxbArmAdapterOptions(command_interval_ms=0, click_up_z=0),
        ),
        simulator,
    )


def test_simulated_and_real_config_adapters_expose_same_frozen_interface() -> None:
    simulated, _ = build_adapter()
    real_shape, _ = build_adapter(real_config_shape=True)

    for method_name in FROZEN_INTERFACE:
        assert callable(getattr(simulated, method_name))
        assert callable(getattr(real_shape, method_name))


def test_frozen_interface_uses_simulator_and_records_expected_primitives() -> None:
    adapter, simulator = build_adapter()

    assert adapter.connect().success is True
    assert adapter.move_xy(10, 20).success is True
    assert adapter.pen_down(5).success is True
    assert adapter.pen_up().success is True
    assert adapter.home().success is True
    assert adapter.disconnect().success is True

    assert [record.action for record in simulator.get_history()] == [
        "open_virtual_com",
        "send_xy",
        "send_z",
        "send_z",
        "send_z",
        "send_xy",
        "close_resource",
    ]


def test_stop_is_local_and_does_not_send_hardware_command() -> None:
    adapter, simulator = build_adapter()

    result = adapter.stop()

    assert result.success is True
    assert adapter.get_status().state is DeviceState.STOPPED
    assert simulator.get_history() == []


def test_real_config_shape_is_blocked_by_default_even_with_interface_methods() -> None:
    adapter, simulator = build_adapter(real_config_shape=True)

    result = adapter.connect()

    assert result.success is False
    assert result.error is not None
    assert result.error.code == "SAFETY_VIOLATION_ERROR"
    assert simulator.get_history() == []


def test_phase2_baseline_fixture_files_exist() -> None:
    assert Path("tests/fixtures/standard_calibration_v2.json").is_file()
    assert Path("tests/fixtures/standard_screen.ppm").is_file()
    assert Path("config/hardware.example.yaml").is_file()
