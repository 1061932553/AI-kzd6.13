# P2-07 Touch Action Primitives

P2-07 adds script-callable touch primitives for `tap`, `long_press`, and `multi_tap`.

## Flow

Each tap-shaped action follows the same sequence:

```text
normalized coordinate
-> optional correction grid
-> coordinate mapper
-> arm boundary validation
-> move_xy
-> settle wait
-> pen_down
-> down delay
-> hold
-> pen_up
-> up delay
```

`long_press` reuses the tap flow with a caller-provided hold duration. `multi_tap` repeats the tap flow and waits a configurable interval between taps.

## Safety

- The action layer receives a `TouchArmAPI` dependency and does not open COM ports or HTTP services.
- Coordinate conversion happens before the first move.
- Out-of-range normalized coordinates are rejected by the coordinate model.
- Correction-grid out-of-bounds coordinates fail before `move_xy`.
- If a step fails, the action attempts `pen_up` and returns a structured failure result.

## Result Shape

Every action returns `TouchActionResult`:

- `action`
- `status`
- `logs`
- `error`

Logs contain ordered step names, status, and step detail. Unit tests assert the sequence without real hardware.
