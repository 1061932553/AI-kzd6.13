# P2-08 Swipe Trajectory Executor

P2-08 adds offline swipe trajectory generation and execution.

## Supported Paths

- Straight line from normalized start to normalized end.
- Multi-point polyline paths.
- Linear and ease-in-out interpolation.

## Execution Flow

```text
generate trajectory
-> validate timing
-> map every point to arm XY
-> move to start
-> start delay
-> pen down
-> timed move through trajectory points
-> end hold
-> pen up
```

All trajectory points are converted through the existing coordinate mapper before the pen goes down. If mapping fails, the swipe returns a structured failure and attempts `pen_up`.

## Cancellation And Failure

`SwipeCancelToken` is checked before the start move and before every trajectory move. A cancellation stops later trajectory points and attempts `pen_up`.

Any exception during movement also attempts `pen_up` and returns a failed `TouchActionResult`.

## Tuning

`python -m tools.swipe_tuning --duration-ms 600 --points 30`

The tool prints an offline JSON trajectory. It does not connect to hardware.
