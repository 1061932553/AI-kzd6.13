# Phase 2 Acceptance

## Scope

P2-12 closes the offline integration gate for phase 2 mode switching. It adds a
single in-process ownership lock and a mode manager for these states:

- `AUTO`
- `MANUAL`
- `SWITCHING`
- `OFFLINE`
- `FAULT`

The default implementation does not launch the legacy manual-control software.
Launching that software requires an injected `ManualAppLauncher` and explicit
hardware authorization outside the offline test suite.

## Manual Control Configuration

The manual-control path is configuration, not implicit launch permission:

```yaml
manual_control:
  enabled: true
  app_directory: "C:\\Users\\s1061\\Desktop\\AI-Multi-Device-Control\\references\\main软件发客户-20260531\\main"
  executable: ""
```

`executable` remains empty until the real executable name is confirmed.

## AUTO To MANUAL Sequence

The offline mode manager performs the safe handoff in this order:

1. Verify the `AUTO` lock owner.
2. Stop accepting new scripts.
3. Wait for the current atomic action to finish.
4. Stop the active script.
5. Reject new automatic actions.
6. Raise the pen.
7. Return to a safe home position.
8. Disconnect the automatic device controller.
9. Release the `AUTO` lock.
10. Acquire the `MANUAL` lock.
11. Start the manual app only through an injected launcher.

If a step fails, the manager enters `FAULT`, rejects new actions, and attempts a
safe `pen_up`.

## MANUAL To AUTO Sequence

The offline mode manager restores automatic control in this order:

1. Verify the `MANUAL` lock owner.
2. Confirm the manual app is closed.
3. Release the `MANUAL` lock.
4. Acquire the `AUTO` lock.
5. Reconnect the device controller.
6. Load calibration.
7. Home the device.
8. Run the center self-check.
9. Allow new automatic actions.

Automatic action admission must call `require_auto_owner()` so actions are
rejected unless the mode is `AUTO` and the lock owner is `AUTO`.

## Offline Acceptance Result

The following checks are covered by the P2-12 offline tests:

- Automatic and manual mode never own the device lock at the same time.
- Automatic actions are rejected in `MANUAL`, `SWITCHING`, `OFFLINE`, and
  `FAULT`.
- AUTO to MANUAL waits for the current action and stops scripts before releasing
  the automatic lock.
- MANUAL to AUTO refuses to proceed while the manual app is still running.
- Re-entering AUTO reconnects, loads calibration, homes, and runs the center
  self-check.
- Manual app launch is configuration-driven and disabled by default without an
  injected launcher.

## Real-Device Acceptance Pending

The following final acceptance items still require explicit real-hardware
authorization and operator observation:

- Click: 16 points, 20 clicks per point, success rate at least 98%, no out of
  bounds actions.
- Long press: 500 ms, 1 s, and 2 s, 20 runs each.
- Multi tap: 2, 3, and 5 taps, 20 groups each.
- Swipe: up, down, left, right, short, and long swipes, 20 runs each.
- Image tap: correct template, wrong template, partial occlusion, brightness
  changes, and absent target.
- Mode switching: AUTO to MANUAL, MANUAL to AUTO, manual app abnormal exit, arm
  disconnect, and camera disconnect.

These items are not marked as passed by P2-12 offline integration.
