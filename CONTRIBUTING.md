# Contributing

## Tests

See [TESTING.md](TESTING.md) for the full testing approach, including the
distinction between unit tests (no Live required) and integration tests
(require a running Live instance) and how to run each.

## Live reloading

AbletonOSC supports dynamic reloading of the handler code modules so that it's not necessary to restart Live each time the code is modified.

To reload the codebase, send an OSC message to `/live/reload`. 

## Logging

Logging can be performed from any of the AbletonOSCHandler classes via the `self.logger` property.

AbletonOSC logs internal events to `logs/abletonosc.log` relative to the AbletonOSC directory.

## Debugging compile-time issues

To view the Live boot log:

```
LOG_DIR="$HOME/Library/Application Support/Ableton/Live Reports/Usage"
LOG_FILE=$(ls -atr "$LOG_DIR"/*.log | tail -1)
echo "Log path: $LOG_FILE"
tail -5000f "$LOG_FILE" | grep AbletonOSC
```
