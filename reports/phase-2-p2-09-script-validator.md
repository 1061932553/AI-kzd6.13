# P2-09 Script Format, Parser, and Static Validation

Status: completed locally.

Scope:

- Defined script version `1.0`.
- Added static validation for `tap`, `long_press`, `multi_tap`, `swipe`, `wait`,
  `home`, `repeat`, and `stop`.
- Rejected unknown actions, unknown fields, missing required fields, invalid
  coordinate ranges, invalid timing ranges, invalid counts, unsupported script
  versions, excessive top-level steps, excessive repeat expansion, and unbounded
  loops.
- Added offline parser and validation CLI.

Safety boundary:

- Did not modify `references/`.
- Did not access `127.0.0.1:8082`.
- Did not open COM ports.
- Did not access USB cameras.
- Did not run EXE, DLL, BAT, installers, services, or admin operations.
- Did not send real arm actions.

Verification:

- `python -m pytest tests\unit\test_script_validator.py`: passed, `12 passed`.
- `python -m tools.validate_script examples\scripts\basic_actions.json`: passed and reported `valid=true`.
- `python -m tools.validate_script examples\scripts\invalid_actions.json`: failed safely with structured path/field issues.
- `python -m ruff check .`: passed.
- `python -m pytest`: passed, `251 passed, 3 skipped`.

Not included:

- Script execution.
- Scheduling.
- Agent tags.
