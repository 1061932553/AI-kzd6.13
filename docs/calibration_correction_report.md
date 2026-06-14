# P2-06 Correction Grid and Calibration Report

P2-06 builds a local correction model from a completed P2-05 16-point session.

## Error Convention

For each point:

- `x_error = actual.x - target.x`
- `y_error = actual.y - target.y`
- `total_error = sqrt(x_error^2 + y_error^2)`

The correction grid stores measured error. When applying compensation, the command point is:

```text
corrected = target - interpolated_error
```

The corrected point is then sent into the existing coordinate mapper. P2-06 does not execute actions.

## Grid Behavior

- The grid requires exactly 16 completed samples arranged as 4 rows by 4 columns.
- Bilinear interpolation is used inside the sampled grid bounds.
- Points outside the sampled grid are rejected by default.
- Callers may explicitly request clamp behavior for diagnostics or safe degradation.

## Report Output

`python -m tools.generate_calibration_report tests/fixtures/calibration_session.json`

The command writes versioned JSON under `reports/calibration/` and updates `current.json`. The report contains:

- calibration version;
- before-compensation average, maximum, and P95 error;
- after-compensation average, maximum, and P95 error;
- serialized correction grid;
- raw per-point error samples.

The report store keeps version files so `rollback_to_previous()` can restore `current.json` to the previous version.
