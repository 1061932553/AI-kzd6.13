# P2-05 16 Point Calibration Session

This package adds the offline-first collection layer for 4x4 screen calibration.

## Scope

- Generate 16 deterministic normalized screen targets.
- Send one calibration point per session step.
- Support pause, resume, cancel, and JSON save/load.
- Preserve raw action and touch events in append-only session data.
- Capture actual touch coordinates from manual input or the local phone web callback.
- Keep hardware mode disabled unless an explicit second confirmation is provided.

## Safety

`python -m tools.run_16_point_calibration --device simulator` uses an in-process simulator executor. It does not open COM ports, cameras, JxbService, EXE, DLL, BAT, or any third-party service.

`--hardware` exits before any action unless `--confirm-hardware` is also provided. The real hardware runner is intentionally not enabled in this offline task package.

## Session Output

The simulator command writes JSON files under `reports/calibration_sessions/`. Each file stores:

- session id, device id, status, created/updated timestamps;
- all 16 point records;
- target normalized coordinates;
- actual normalized touch coordinates when captured;
- raw events for action send and touch capture history.

Generated session files are runtime evidence and should be reviewed before committing.
