# P2-11 Basic Image Tap

Status: completed locally.

Scope:

- Added single-template RGB24 matching.
- Added optional search rectangle and confidence threshold.
- Returned match coordinate, center, confidence, and candidate count.
- Selected the highest confidence target.
- Converted target center to normalized coordinates.
- Routed successful matches through the existing `execute_tap`.
- Prevented clicks when no template is found.
- Saved failed frames as PPM screenshots when configured.
- Added offline debugger CLI and deterministic fixtures.

Safety boundary:

- Did not modify `references/`.
- Did not access `127.0.0.1:8082`.
- Did not open COM ports.
- Did not access USB cameras.
- Did not run EXE, DLL, BAT, installers, services, or admin operations.
- Did not send real arm actions.

Verification:

- `python -m pytest tests\unit\test_template_matcher.py`: passed, `5 passed`.
- `python -m pytest tests\integration\test_tap_image_simulator.py`: passed, `2 passed`.
- `python -m tools.template_debugger --image tests\fixtures\screen.png --template tests\fixtures\confirm.png`: passed and found center `[12.0, 9.5]` with confidence `1.0`.
- `python -m ruff check .`: passed.
- `python -m pytest`: passed, `267 passed, 3 skipped`.

Not included:

- OCR.
- AI target detection.
- Multiple-template logic.
- Page flow judgment.
