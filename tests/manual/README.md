# Manual integration tests: `.View` namespaces

Plain OSC command scripts for smoke-testing the `application_view`, `song_view`,
`track_view`, `clip_view` and `device_view` namespaces against a real, running Ableton Live
instance, using `run-console.py`. Unlike the automated suite in `tests/`, these don't assert
anything — they're meant to be read by eye, in verbose mode, to catch things a `pytest` run
can't easily surface remotely (e.g. an `AttributeError` deep in Live's log because a
property turns out not to have a real `add_<prop>_listener`, despite the LOM docs saying
it's observable).

## Prerequisites

Same as `TESTING.md`: Live running with the blank default test set (7 tracks — 4 regular +
a Group + the Group's 2 children; a Looper device at track 0/device 0), AbletonOSC selected
as the Control Surface.

## Running

From the repo root, pipe each file into the console in verbose mode:

```
python3 run-console.py -v < tests/manual/application_view.txt
python3 run-console.py -v < tests/manual/song_view.txt
python3 run-console.py -v < tests/manual/track_view.txt
python3 run-console.py -v < tests/manual/clip_view.txt
python3 run-console.py -v < tests/manual/device_view.txt
```

`run-console.py` sends `/live/api/reload` on startup, so each run exercises the latest
handler code with no manual reload step needed.

## Reading the output

- Every line printed as `command, params -> response` (or similar, depending on your
  terminal) after a `get`/`set` command is the direct reply `run-console.py` prints from
  `client.query(...)`.
- A `set` command has **no reply of its own** — `run-console.py` will silently swallow the
  resulting `RuntimeError` (the query times out waiting for a reply that never comes on that
  address). This is expected, not a bug.
- If a `start_listen` is active on the property being set, watch for a **second, unsolicited
  line** printed shortly after (within ~100ms) on the `.../get/<prop>` address, carrying the
  new value — that's the listener push, and its presence/absence is the actual thing being
  tested. `-v` prints every incoming OSC message, so it'll show up even though
  `run-console.py`'s own `query()` for the `set` command already timed out.
- After `stop_listen`, confirm no further push arrives for subsequent `set` calls on that
  property.
- `clip_view.txt` ends with one query against a clip slot after its clip has just been
  deleted — that's a deliberate check that the "no clip at that slot" warning path (logged
  server-side) doesn't crash or hang the server. Expect the console to sit for ~150ms and
  print nothing for that line, then move on.
- Also check Live's own log (`logs/abletonosc.log` under the AbletonOSC script directory)
  for any `Traceback`/`AttributeError` during the run — that's the main thing this suite is
  designed to catch, and it won't necessarily surface as a `run-console.py` error.
- Each file ends by restoring anything it changed (track collapse state, draw mode,
  browse mode, created clips, etc.) — if a run is interrupted partway through, check the Set
  by hand before re-running.
