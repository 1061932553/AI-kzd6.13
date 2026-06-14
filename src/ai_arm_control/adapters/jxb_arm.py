"""JxbService arm adapter with queueing, safety checks, and reconnects.

The adapter is safe-by-default: simulator URLs work in offline tests, while
HTTP(S) JxbService URLs are blocked unless the device configuration explicitly
allows real hardware. Even when enabled, network behavior remains behind the
JxbServiceClient boundary and is not exercised by default commands.
"""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from itertools import count
from typing import Any

from ai_arm_control.config import StandardizedDeviceConfig
from ai_arm_control.contracts import StandardDeviceAPI
from ai_arm_control.core import (
    AIArmControlError,
    DeviceConnectionError,
    InvalidResourceError,
    SafetyViolationError,
    ServiceUnavailableError,
)
from ai_arm_control.models import (
    ArmCommand,
    CommandResult,
    DeviceState,
    DeviceStateInfo,
    ErrorInfo,
    OperationMode,
)
from ai_arm_control.models.types import JsonObject, utc_now
from ai_arm_control.simulators import JxbServiceClient


@dataclass(frozen=True, slots=True, kw_only=True)
class JxbArmAdapterOptions:
    command_interval_ms: int = 50
    reconnect_attempts: int = 1
    home_x: int = 0
    home_y: int = 0
    home_z: int = 0
    click_up_z: int = 0

    def __post_init__(self) -> None:
        if self.command_interval_ms < 0:
            raise ValueError("command_interval_ms cannot be negative")
        if self.reconnect_attempts < 0:
            raise ValueError("reconnect_attempts cannot be negative")


class JxbArmAdapter(StandardDeviceAPI):
    """Synchronous JxbService arm adapter used by CLI/tests before UI exists."""

    def __init__(
        self,
        config: StandardizedDeviceConfig,
        *,
        client: JxbServiceClient | None = None,
        options: JxbArmAdapterOptions | None = None,
    ) -> None:
        self.config = config
        self.options = options or JxbArmAdapterOptions()
        service_url = config.hardware.service_url or "simulator://jxb"
        self.client = client or JxbServiceClient(service_url)
        self._queue: deque[ArmCommand] = deque()
        self._resource_id: int | None = None
        self._state = DeviceState.OFFLINE
        self._calibration: object | None = None
        self._last_action_at = 0.0
        self._interface_command_ids = count(1)

    @property
    def resource_id(self) -> int | None:
        return self._resource_id

    @property
    def queue_size(self) -> int:
        return len(self._queue)

    def get_status(self) -> DeviceStateInfo:
        return DeviceStateInfo(
            device_id=self.config.device.device_id,
            state=self._state,
            mode=self.config.device.mode,
            metadata={"resource_id": self._resource_id, "queue_size": len(self._queue)},
        )

    def health_check(self) -> bool:
        return self.config.device.enabled and self._state not in {
            DeviceState.FAULT,
            DeviceState.MANUAL,
            DeviceState.STOPPED,
        }

    def load_calibration(self, calibration: object) -> None:
        self._calibration = calibration

    def connect(self) -> CommandResult:
        return self.execute(self._interface_command("connect"))

    def disconnect(self) -> CommandResult:
        return self.execute(self._interface_command("close"))

    def home(self) -> CommandResult:
        return self.execute(self._interface_command("home"))

    def move_xy(self, x: int, y: int) -> CommandResult:
        return self.execute(self._interface_command("move_xy", x=x, y=y))

    def pen_down(self, z: int) -> CommandResult:
        return self.execute(self._interface_command("move_z", z=z))

    def pen_up(self) -> CommandResult:
        return self.execute(self._interface_command("move_z", z=self.options.click_up_z))

    def stop(self) -> CommandResult:
        started_at = utc_now()
        self._queue.clear()
        self._state = DeviceState.STOPPED
        return CommandResult(
            command_id=self._next_interface_command_id("stop"),
            device_id=self.config.device.device_id,
            state=self._state,
            success=True,
            started_at=started_at,
            finished_at=utc_now(),
            data={"queue_size": 0},
        )

    def execute(self, command: ArmCommand) -> CommandResult:
        self._queue.append(command)
        result: CommandResult | None = None
        while self._queue:
            result = self._execute_one(self._queue.popleft())
            if not result.success:
                self._queue.clear()
                return result
        if result is None:
            raise RuntimeError("command queue unexpectedly produced no result")
        return result

    def close(self) -> None:
        if self._resource_id is None:
            self._state = DeviceState.OFFLINE
            return
        self.client.close(self._resource_id)
        self._resource_id = None
        self._state = DeviceState.OFFLINE

    def _execute_one(self, command: ArmCommand) -> CommandResult:
        started_at = utc_now()
        try:
            self._validate_command(command)
            self._state = DeviceState.EXECUTING
            data = self._dispatch(command)
        except AIArmControlError as exc:
            self._state = DeviceState.FAULT
            return self._failure_result(command, exc, started_at)
        except ValueError as exc:
            self._state = DeviceState.FAULT
            error = SafetyViolationError(str(exc))
            return self._failure_result(command, error, started_at)
        if command.command_type != "close":
            self._state = DeviceState.IDLE
        return CommandResult(
            command_id=command.command_id,
            device_id=command.device_id,
            state=self._state,
            success=True,
            trace_id=command.trace_id,
            started_at=started_at,
            finished_at=utc_now(),
            data=data,
        )

    def _validate_command(self, command: ArmCommand) -> None:
        if command.device_id != self.config.device.device_id:
            raise SafetyViolationError(
                "command targets a different device",
                {"command_device_id": command.device_id, "device_id": self.config.device.device_id},
            )
        if not self.config.device.enabled:
            raise SafetyViolationError("device is disabled")
        if (
            self.config.device.mode is OperationMode.MANUAL
            and command.mode is not OperationMode.MANUAL
        ):
            self._state = DeviceState.MANUAL
            raise SafetyViolationError("automatic command blocked while device is in manual mode")
        if command.command_type in {"move_xy", "click"}:
            x, y = self._extract_xy(command.parameters)
            self._validate_xy(x, y)

    def _dispatch(self, command: ArmCommand) -> JsonObject:
        match command.command_type:
            case "connect":
                self._connect()
                return {"resource_id": self._resource_id}
            case "move_xy":
                x, y = self._extract_xy(command.parameters)
                self._send_with_reconnect(
                    lambda resource_id: self.client.send_xy(resource_id, x, y)
                )
                return {"resource_id": self._resource_id, "x": x, "y": y}
            case "move_z":
                z = self._require_int(command.parameters, "z")
                self._send_with_reconnect(lambda resource_id: self.client.send_z(resource_id, z))
                return {"resource_id": self._resource_id, "z": z}
            case "click":
                return self._click(command.parameters)
            case "home":
                return self._home(command.parameters)
            case "close":
                self.close()
                return {"resource_id": None}
            case _:
                raise SafetyViolationError(
                    "unsupported arm command",
                    {"command_type": command.command_type},
                )

    def _connect(self) -> None:
        if self._resource_id is not None:
            return
        self._assert_real_hardware_allowed()
        port = self.config.hardware.com_port
        if not port:
            raise DeviceConnectionError("COM port is not configured")
        self._state = DeviceState.CONNECTING
        self._respect_interval()
        response = self.client.open_com(port)
        if response.resource_id is None:
            raise InvalidResourceError("JxbService did not return a resource id")
        self._resource_id = response.resource_id

    def _send_with_reconnect(self, operation: Any) -> None:
        self._connect()
        attempts_left = self.options.reconnect_attempts + 1
        while attempts_left:
            attempts_left -= 1
            try:
                self._respect_interval()
                assert self._resource_id is not None
                operation(self._resource_id)
                return
            except (InvalidResourceError, ServiceUnavailableError):
                self._resource_id = None
                if attempts_left <= 0:
                    raise
                self._state = DeviceState.RECOVERING
                self._connect()

    def _click(self, parameters: JsonObject) -> JsonObject:
        x, y = self._extract_xy(parameters)
        down_z = self._require_int(parameters, "z")
        up_z = int(parameters.get("up_z", self.options.click_up_z))
        self._send_with_reconnect(lambda resource_id: self.client.send_xy(resource_id, x, y))
        self._send_with_reconnect(lambda resource_id: self.client.send_z(resource_id, down_z))
        self._send_with_reconnect(lambda resource_id: self.client.send_z(resource_id, up_z))
        return {"resource_id": self._resource_id, "x": x, "y": y, "z": up_z}

    def _home(self, parameters: JsonObject) -> JsonObject:
        x = int(parameters.get("x", self.options.home_x))
        y = int(parameters.get("y", self.options.home_y))
        z = int(parameters.get("z", self.options.home_z))
        self._validate_xy(x, y)
        self._send_with_reconnect(lambda resource_id: self.client.send_z(resource_id, z))
        self._send_with_reconnect(lambda resource_id: self.client.send_xy(resource_id, x, y))
        return {"resource_id": self._resource_id, "x": x, "y": y, "z": z}

    def _assert_real_hardware_allowed(self) -> None:
        service_url = self.config.hardware.service_url or ""
        is_simulated = (
            service_url.startswith("simulator://") or self.config.device.connection.is_simulated
        )
        if not is_simulated and not self.config.device.safety_limits.allow_real_hardware:
            raise SafetyViolationError("real hardware is disabled by safety limits")

    def _validate_xy(self, x: int, y: int) -> None:
        limits = self.config.device.safety_limits
        if limits.min_x is not None and x < limits.min_x:
            raise SafetyViolationError("x is below safety limit", {"x": x, "min_x": limits.min_x})
        if limits.max_x is not None and x > limits.max_x:
            raise SafetyViolationError("x is above safety limit", {"x": x, "max_x": limits.max_x})
        if limits.min_y is not None and y < limits.min_y:
            raise SafetyViolationError("y is below safety limit", {"y": y, "min_y": limits.min_y})
        if limits.max_y is not None and y > limits.max_y:
            raise SafetyViolationError("y is above safety limit", {"y": y, "max_y": limits.max_y})

    def _respect_interval(self) -> None:
        interval = self.options.command_interval_ms / 1000
        elapsed = time.monotonic() - self._last_action_at
        if interval > 0 and elapsed < interval:
            time.sleep(interval - elapsed)
        self._last_action_at = time.monotonic()

    def _failure_result(
        self,
        command: ArmCommand,
        error: AIArmControlError,
        started_at: datetime,
    ) -> CommandResult:
        return CommandResult(
            command_id=command.command_id,
            device_id=command.device_id,
            state=self._state,
            success=False,
            error=ErrorInfo(
                code=error.error_code,
                message=error.message,
                recoverable=error.error_code
                in {"INVALID_RESOURCE_ERROR", "SERVICE_UNAVAILABLE_ERROR"},
                details=error.details,
            ),
            trace_id=command.trace_id,
            started_at=started_at,
            finished_at=utc_now(),
        )

    @staticmethod
    def _extract_xy(parameters: JsonObject) -> tuple[int, int]:
        return (
            JxbArmAdapter._require_int(parameters, "x"),
            JxbArmAdapter._require_int(parameters, "y"),
        )

    def _interface_command(self, command_type: str, **parameters: int) -> ArmCommand:
        return ArmCommand(
            command_id=self._next_interface_command_id(command_type),
            device_id=self.config.device.device_id,
            command_type=command_type,
            parameters=parameters,
            mode=self.config.device.mode,
        )

    def _next_interface_command_id(self, command_type: str) -> str:
        return f"adapter-{command_type}-{next(self._interface_command_ids):06d}"

    @staticmethod
    def _require_int(parameters: JsonObject, key: str) -> int:
        if key not in parameters:
            raise SafetyViolationError("missing command parameter", {"parameter": key})
        value = parameters[key]
        if isinstance(value, bool) or not isinstance(value, int):
            raise SafetyViolationError("command parameter must be an integer", {"parameter": key})
        return value
