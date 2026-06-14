# P2-10 Script Runner and State Machine

P2-10 executes scripts that have already passed P2-09 static validation. The
runner is sequential and uses injected action dependencies; it does not create
hardware clients, open COM ports, access JxbService, or read cameras.

## States

- `IDLE`
- `RUNNING`
- `PAUSED`
- `CANCELLING`
- `COMPLETED`
- `FAILED`

`pause()` takes effect before the next step, so it does not interrupt an
in-flight primitive. `cancel()` prevents following steps and records the run as
`FAILED` with `script cancelled`.

## Execution

Supported actions:

- `tap`
- `long_press`
- `multi_tap`
- `swipe`
- `wait`
- `home`
- `repeat`
- `stop`

Every step records start and finish history. Failed actions retry up to the
step's bounded `retry` value. When retries are exhausted, the run enters
`FAILED` and no later step is executed.

## Persistence

`ScriptRunHistory` stores:

- run id
- device id
- state
- current step path
- started and finished times
- per-step attempts
- per-step status and errors

`JsonScriptHistoryStore` writes one JSON file per run and can reload the latest
record after a process restart. This is a state record only; P2-10 does not
resume physical execution after power loss.

## Device Mutual Exclusion

The runner keeps one active run per `device_id` in the current process. A second
runner targeting the same device fails before executing any step.

## Verification

```powershell
python -m pytest tests\unit\test_script_runner.py
python -m pytest tests\integration\test_script_runner_simulator.py
```
