# P2-05 16 Point Calibration Data Collection

Status: completed locally.

## Scope

- Added 4x4 normalized calibration grid generation.
- Added calibration session state for one-point-at-a-time execution.
- Added pause, resume, cancel, save/load, and raw event preservation.
- Added manual touch capture and local web touch callback storage.
- Added a simulator-only CLI for repeatable offline verification.

## Safety Boundary

- No `references/` files were modified.
- No JxbService access was performed.
- No `127.0.0.1:8082` access was performed.
- No COM port was opened.
- No USB camera was accessed.
- No EXE, DLL, BAT, installer, or service was run.
- No real arm command was sent.

## Verification

- `python -m pytest tests\unit\test_grid_generator.py`: passed, `11 passed`.
- `python -m tools.run_16_point_calibration --device simulator`: passed, generated a completed 16-point session JSON under `reports\calibration_sessions\`.
- `python -m tools.run_16_point_calibration --device ARM-001 --hardware`: blocked before action because `--confirm-hardware` was not provided.
- `python -m pytest`: passed, `215 passed, 1 skipped`.
- `python -m ruff check .`: passed.

## Not Included

- Error compensation calculation.
- Click success rate report.
- Formal script execution.
- Real hardware calibration execution.
