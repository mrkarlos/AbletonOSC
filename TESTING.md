# Testing

AbletonOSC's test suite has two tiers, with different prerequisites. Pick the
right one based on what the code under test actually touches.

## Unit tests (`tests_unit/`)

Pure Python, no Ableton Live required. These test logic that doesn't depend on
Live's object model or a real OSC round-trip — e.g. `osc_server.py`'s socket
error handling, address parsing, or parameter serialization.

Run with:

```bash
pytest tests_unit/
```

No prerequisites beyond `pip3 install pytest`. Safe to run anywhere, including
a future CI pipeline, since nothing here opens a connection to a running Live
instance.

`tests_unit/` is a separate top-level directory, independent of the `tests/`
package below — deliberately so, because `tests/__init__.py` performs
Live-oriented setup (creating an `AbletonOSCClient` and sending
`/live/api/reload`) at *import time*. Anything that imports the `tests`
package pulls that in, so unit tests live outside it entirely rather than
trying to skip or guard that setup from within.

## Integration tests (`tests/`)

Require a running Ableton Live instance with AbletonOSC loaded, since they
exercise real Live API objects (tracks, clips, devices, etc.) via actual OSC
messages sent to a live process.

Prerequisites:

- Live must be configured with default audio input and output devices.
- Live must be started with a blank default set.
- In `Preferences > Record, Warp & Launch`, `Count-In` must be set to `None`
  (for recording test clips).
- AbletonOSC must be selected as the Control Surface in Live's MIDI
  preferences.

Run with:

```bash
pytest tests/
```

Importing the `tests` package sends `/live/api/reload` as a side effect, so
each test run picks up the latest handler code without restarting Live.

Importing the `tests` package also checks the song shape over OSC (track
count, and that track 0 / device 0 is a Looper) and aborts the run
immediately with a clear message if it doesn't match, rather than letting an
unprepped set surface as a wall of unrelated failures. This can only check
what's visible over OSC — it can't verify the Count-In or default audio
device prerequisites above, since those aren't exposed via the Live API.

## Which tier does a new test belong in?

- Does it call into `Live.*` objects, or assert on the result of a real OSC
  round-trip against a running Live instance? → **integration** (`tests/`).
- Does it test pure-Python logic that doesn't need Live at all — error
  handling, a helper function, message building/parsing? → **unit**
  (`tests_unit/`).

When in doubt: if the test would fail simply because Live isn't running, it's
an integration test.

## Running everything

With Live running and configured per the prerequisites above, `pytest` from
the repo root runs both tiers together.
