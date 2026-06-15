"""Tiny local calibration web server for browser touch callbacks."""

from __future__ import annotations

import json
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from ai_arm_control.calibration.grid_generator import CalibrationGridPoint
from ai_arm_control.calibration.touch_capture import TouchCaptureStore
from ai_arm_control.coordinates.models import NormalizedPoint

STATIC_DIR = Path(__file__).with_name("static")


@dataclass(slots=True)
class CalibrationWebServer:
    host: str
    port: int
    touch_store: TouchCaptureStore
    targets: dict[str, CalibrationGridPoint]
    httpd: ThreadingHTTPServer | None = None

    def start(self) -> None:
        handler = create_touch_handler(self.touch_store, self.targets)
        self.httpd = ThreadingHTTPServer((self.host, self.port), handler)
        self.httpd.serve_forever()

    def stop(self) -> None:
        if self.httpd is not None:
            self.httpd.shutdown()
            self.httpd.server_close()


def create_touch_handler(
    touch_store: TouchCaptureStore,
    targets: dict[str, CalibrationGridPoint],
) -> type[BaseHTTPRequestHandler]:
    class CalibrationTouchHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            if self.path not in ("/", "/calibration"):
                self.send_error(404)
                return
            body = (STATIC_DIR / "index.html").read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self) -> None:  # noqa: N802
            if self.path != "/touch":
                self.send_error(404)
                return
            try:
                payload = self._read_json()
                point_id = str(payload["point_id"])
                target = (
                    targets[point_id].target
                    if point_id in targets
                    else NormalizedPoint(payload["target_x"], payload["target_y"])
                )
                sample = touch_store.record_web_touch(
                    point_id=point_id,
                    target=target,
                    x=payload["x"],
                    y=payload["y"],
                )
            except Exception as exc:  # pragma: no cover
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"ok": False, "error": str(exc)}).encode("utf-8"))
                return
            self._write_json({"ok": True, "sample": sample.to_dict()})

        def log_message(self, format: str, *args: object) -> None:
            return

        def _read_json(self) -> dict[str, object]:
            length = int(self.headers.get("Content-Length", "0"))
            return json.loads(self.rfile.read(length).decode("utf-8"))

        def _write_json(self, payload: dict[str, object]) -> None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    return CalibrationTouchHandler
