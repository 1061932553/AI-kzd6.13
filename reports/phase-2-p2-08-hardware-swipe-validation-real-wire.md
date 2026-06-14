# P2-08 Hardware Swipe Validation - Real Wire Commands

- Status: completed_transport_success
- Wire commands: `X{x}Y{y}` and `Z{z}`
- Previous report invalidated: it used `MOVE_XY` / `MOVE_Z`, and the user observed no physical motion.
- Device: ARM-001 / COM4 / JxbService HTTP
- Attempts: 120
- Succeeded: 120
- Failed: 0
- Safety: JxbArmAdapter, allow_real_hardware=True, XY bounds 0..140 / 0..140, Z 0..2 used, stop on first failure
- Physical motion: pending user observation confirmation
- Phone recognition: pending validation; no phone touch callback was captured

| Scenario | Attempted | Succeeded |
| --- | ---: | ---: |
| up | 20 | 20 |
| down | 20 | 20 |
| left | 20 | 20 |
| right | 20 | 20 |
| short | 20 | 20 |
| long | 20 | 20 |
