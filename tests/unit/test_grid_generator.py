from __future__ import annotations

import json
import threading
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer

import pytest

from ai_arm_control.calibration.grid_generator import CalibrationGridError, generate_4x4_grid
from ai_arm_control.calibration.session import (
    CalibrationPointStatus,
    CalibrationSession,
    CalibrationSessionError,
    CalibrationSessionStatus,
)
from ai_arm_control.calibration.touch_capture import ManualTouchCapture, TouchCaptureStore
from ai_arm_control.calibration_web.server import create_touch_handler
from ai_arm_control.coordinates import (
    Bounds2D,
    CoordinateError,
    CoordinateMapper,
    CoordinateMapperConfig,
    ScreenROI,
)


class FakePointExecutor:
    def __init__(self) -> None:
        self.calls: list[tuple[str, float, float]] = []

    def tap_point(self, point, arm_x: float, arm_y: float) -> dict[str, object]:  # noqa: ANN001
        self.calls.append((point.point_id, arm_x, arm_y))
        return {"point_id": point.point_id, "status": "sent", "arm_x": arm_x, "arm_y": arm_y}


def build_mapper() -> CoordinateMapper:
    return CoordinateMapper(
        CoordinateMapperConfig(
            screen_roi=ScreenROI.from_sequence([64, 32, 482, 911]),
            arm_bounds=Bounds2D(min_x=0, max_x=366, min_y=0, max_y=160),
        )
    )


def test_generate_4x4_grid_returns_16_unique_row_major_points() -> None:
    points = generate_4x4_grid()

    assert len(points) == 16
    assert [point.point_id for point in points] == [f"P{index:02d}" for index in range(1, 17)]
    assert len({point.point_id for point in points}) == 16
    assert points[0].row == 0
    assert points[0].column == 0
    assert points[-1].row == 3
    assert points[-1].column == 3
    assert points[0].target.x == pytest.approx(0.1)
    assert points[-1].target.y == pytest.approx(0.9)


@pytest.mark.parametrize("margin", [-0.01, 0.5, 0.75])
def test_generate_4x4_grid_rejects_invalid_margin(margin: float) -> None:
    with pytest.raises(CalibrationGridError):
        generate_4x4_grid(margin=margin)


def test_session_executes_only_one_point_per_call_and_records_manual_touch() -> None:
    session = CalibrationSession.create_4x4(device_id="simulator")
    executor = FakePointExecutor()
    capture = ManualTouchCapture()

    session.start()
    record = session.execute_next(mapper=build_mapper(), executor=executor)

    assert len(executor.calls) == 1
    assert record.point.point_id == "P01"
    assert record.status is CalibrationPointStatus.ACTION_SENT

    sample = capture.capture(point_id="P01", target=record.point.target, x=0.11, y=0.12)
    completed = session.record_touch(sample)

    assert completed.status is CalibrationPointStatus.COMPLETED
    assert completed.actual is not None
    assert completed.actual.x == pytest.approx(0.11)
    assert session.next_pending().point.point_id == "P02"  # type: ignore[union-attr]
    assert [event["event"] for event in session.raw_events].count("touch_recorded") == 1


def test_cancel_prevents_sending_additional_points() -> None:
    session = CalibrationSession.create_4x4(device_id="simulator")
    executor = FakePointExecutor()

    session.start()
    session.cancel()

    with pytest.raises(CalibrationSessionError, match="must be running"):
        session.execute_next(mapper=build_mapper(), executor=executor)
    assert executor.calls == []
    assert session.status is CalibrationSessionStatus.CANCELLED


def test_pause_and_resume_control_execution() -> None:
    session = CalibrationSession.create_4x4(device_id="simulator")
    executor = FakePointExecutor()

    session.start()
    session.pause()
    with pytest.raises(CalibrationSessionError, match="must be running"):
        session.execute_next(mapper=build_mapper(), executor=executor)

    session.resume()
    session.execute_next(mapper=build_mapper(), executor=executor)

    assert len(executor.calls) == 1
    assert session.status is CalibrationSessionStatus.RUNNING


def test_session_save_load_resumes_from_unfinished_point(tmp_path) -> None:  # noqa: ANN001
    session = CalibrationSession.create_4x4(device_id="simulator")
    executor = FakePointExecutor()
    capture = ManualTouchCapture()
    session.start()
    record = session.execute_next(mapper=build_mapper(), executor=executor)
    session.record_touch(capture.capture(point_id="P01", target=record.point.target, x=0.1, y=0.1))

    path = tmp_path / "session.json"
    session.save_json(path)

    loaded = CalibrationSession.load_json(path)

    assert loaded.next_pending().point.point_id == "P02"  # type: ignore[union-attr]
    assert loaded.raw_events


def test_touch_store_records_web_touch() -> None:
    point = generate_4x4_grid()[0]
    store = TouchCaptureStore()

    sample = store.record_web_touch(point_id=point.point_id, target=point.target, x=0.2, y=0.3)

    assert sample.source == "web"
    assert store.get("P01") == sample


def test_manual_touch_rejects_out_of_range_actual_point() -> None:
    point = generate_4x4_grid()[0]

    with pytest.raises(CoordinateError):
        ManualTouchCapture().capture(point_id=point.point_id, target=point.target, x=-0.1, y=0.3)


def test_web_touch_handler_accepts_browser_callback() -> None:
    point = generate_4x4_grid()[0]
    store = TouchCaptureStore()
    handler = create_touch_handler(store, {point.point_id: point})
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever)
    thread.start()
    try:
        payload = json.dumps({"point_id": "P01", "x": 0.2, "y": 0.3}).encode("utf-8")
        connection = HTTPConnection("127.0.0.1", server.server_address[1], timeout=2)
        connection.request(
            "POST",
            "/touch",
            body=payload,
            headers={"Content-Type": "application/json"},
        )
        response = connection.getresponse()
        body = json.loads(response.read().decode("utf-8"))
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

    assert response.status == 200
    assert body["ok"] is True
    assert store.get("P01").actual.x == pytest.approx(0.2)  # type: ignore[union-attr]
