# P2-07 Tap, Long Press, and Multi Tap Primitives

Status: completed locally.

## Scope

- Added script-callable `tap`, `long_press`, and `multi_tap` primitives.
- Added configurable timing for settle, down delay, hold, up delay, and tap interval.
- Added structured action result and ordered action logs.
- Added coordinate mapping and optional P2-06 correction-grid application before motion.
- Added failure handling that attempts `pen_up` after any failed step.
- Added hardware test gate that defaults to skip and does not access real hardware.

## Safety Boundary

- No `references/` files were modified.
- No JxbService access was performed.
- No `127.0.0.1:8082` access was performed.
- No COM port was opened.
- No USB camera was accessed.
- No EXE, DLL, BAT, installer, service, or admin operation was run.
- No real arm command was sent.

## Verification

- `python -m pytest tests\unit\test_touch_actions.py`: passed, `7 passed`.
- `python -m pytest tests\hardware\test_touch_actions_hardware.py --hardware`: safe gate skipped, `1 skipped`.
- `python -m ruff check .`: passed.
- `python -m pytest`: passed, `230 passed, 2 skipped`.

## Not Included

- Swipe.
- Script loops.
- Image matching.
- Real hardware validation.
