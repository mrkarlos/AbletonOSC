# Manual integration tests

Plain OSC command scripts for smoke-testing behavior against a real, running Ableton Live
instance, using `run-console.py`, that the automated suite in `tests/` can't easily cover.
Unlike that suite, these don't assert anything — they're meant to be read by eye, in verbose
mode.

Most of these cover the `application_view`, `song_view`, `track_view`, `clip_view` and
`device_view` namespaces, catching things like an `AttributeError` deep in Live's log
because a property turns out not to have a real `add_<prop>_listener`, despite the LOM docs
saying it's observable. `track_data_listen.txt` is different: it exercises
`start_listen`/`stop_listen` on `/live/song/*/track_data`, specifically the auto-rebuild
behavior on track/scene count changes -- too invasive against the shared `tests/` fixture
Set to automate (see `tests/test_song_track_data_listen.py` for the automated coverage of
everything else about that feature).

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
python3 run-console.py -v < tests/manual/track_data_listen.txt
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
- `track_data_listen.txt` is checking that `start_listen/track_data`'s coverage survives
  structural changes with no further `start_listen` call needed: watch for a
  `/live/track/get/name` push after each `set/name`, and a `/live/clip/get/name` push after
  each `create_clip`/`delete_clip` on track 2 or 3 — including the ones that happen *after*
  a scene or track is added/removed elsewhere in the Set, which is the part `pytest` can't
  safely exercise against the shared fixture Set. In the final block (auto-rebuild disabled),
  confirm the opposite: no `/live/clip/get/name` push arrives for the `create_clip`.
