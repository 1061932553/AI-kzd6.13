# P2-08 Hardware Swipe Validation - Invalidated

- Status: invalidated_no_physical_motion
- Reason: this run used simulator-style `MOVE_XY` / `MOVE_Z` wire commands. The user observed that the real device did not move, so the transport success below must not be treated as hardware motion success.
- Superseded by: `reports/phase-2-p2-08-hardware-swipe-validation-real-wire.md`
- Device: ARM-001 / COM4 / JxbService HTTP
- Started: 2026-06-14T17:07:02.747961+00:00
- Finished: 2026-06-14T17:10:24.626409+00:00
- Attempts: 120
- Transport responses marked succeeded: 120
- Physical motion: failed by user observation
- Safety: JxbArmAdapter, allow_real_hardware=True, XY bounds 0..366 / 0..160, stop on first failure
- Mapping: P2-02 base mapping, no correction grid, no camera access
- Phone recognition: pending validation; no phone touch callback or manual observation log was captured.

| Scenario | Attempted | Succeeded |
| --- | ---: | ---: |
| up | 20 | 20 |
| down | 20 | 20 |
| left | 20 | 20 |
| right | 20 | 20 |
| short | 20 | 20 |
| long | 20 | 20 |
