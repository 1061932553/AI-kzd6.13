# P2-09 Script Format and Static Validation

P2-09 defines the first offline script format. Validation never connects to
hardware, never opens COM ports, never accesses JxbService, and never executes
arm actions.

## Version

Scripts must be JSON objects with:

```json
{
  "script_version": "1.0",
  "steps": []
}
```

The validator rejects unknown root fields except optional `metadata`.

## Supported Actions

- `tap`: requires normalized `x` and `y`.
- `long_press`: requires `x`, `y`, and `duration_ms` from 500 to 5000.
- `multi_tap`: requires `x`, `y`, and `count` from 1 to 20.
- `swipe`: requires either `start`/`end` or `path`, plus `duration_ms`.
- `wait`: requires `duration_ms`.
- `home`: no extra fields.
- `repeat`: requires bounded `count` and nested `steps`.
- `stop`: no extra fields.

All coordinates are screen-normalized values from `0.0` to `1.0`. Scripts do
not store arm absolute coordinates or camera pixels.

## Safety Limits

- Maximum top-level steps: 500.
- Maximum repeat count: 100.
- Maximum repeat depth: 5.
- Maximum expanded steps: 5000.
- Unknown fields are rejected.
- Infinite loops are impossible in schema v1 because `repeat.count` is required
  and bounded.

## Validation

```powershell
python -m tools.validate_script examples/scripts/basic_actions.json
python -m pytest tests\unit\test_script_validator.py
```

The validator returns structured issues with path, field, and step index. A
valid script only means the JSON is statically safe to hand to a future runner;
it does not mean any action was executed.
