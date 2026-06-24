# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

AbletonOSC is an Ableton Live MIDI remote script that exposes Live's Python API over OSC (Open Sound Control). It runs inside Live's embedded Python runtime, not as a standalone process. The script listens on UDP port 11000 and replies on port 11001.

## Running tests

Tests require Ableton Live to be running with a blank default set. From the `AbletonOSC` directory:

```bash
pytest                          # all tests
pytest tests/test_session_ring.py  # single test file
pytest tests/test_song.py::test_function_name  # single test
```

**Prerequisites before running tests:**
- Live must be started with a blank default set
- Live must have default audio input/output devices configured
- In `Preferences > Record, Warp & Launch`, set `Count-In` to `None`
- AbletonOSC must be selected as the Control Surface in Live's MIDI preferences

The `tests/__init__.py` sends `/live/api/reload` on import, which hot-reloads the handler code before each test module runs.

## Live reloading during development

Send an OSC message to `/live/api/reload` to reload all handler modules without restarting Live:

```bash
./run-console.py   # interactive console
>>> /live/api/reload
```

Logs are written to `logs/abletonosc.log` relative to the script directory. Log level defaults to `info` and can be changed at runtime with `/live/api/set/log_level debug`.

## Debugging boot errors

To tail Live's boot log and filter for AbletonOSC errors:

```bash
LOG_DIR="$HOME/Library/Application Support/Ableton/Live Reports/Usage"
LOG_FILE=$(ls -atr "$LOG_DIR"/*.log | tail -1)
tail -5000f "$LOG_FILE" | grep AbletonOSC
```

## Architecture

### Entry point and lifecycle

- **`__init__.py`** (root) — not shown but exists; Ableton discovers the script here
- **`manager.py`** — `Manager` extends `ControlSurface`. Live instantiates this class. It owns the `OSCServer`, the `SessionRingComponent`, and all handlers. The `tick()` method is called every 100ms via `schedule_message`, driving `osc_server.process()` (Live's embedded Python doesn't support threads).

### Handler pattern

Every domain (song, track, clip, scene, device, view, session_ring, clip_slot, midimap, application) is a subclass of `AbletonOSCHandler` in `abletonosc/handler.py`. Each handler:

- Calls `self.osc_server.add_handler("/live/<domain>/...")` in `init_api()`
- Accesses the Live API via `self.song`, `self.application`, etc. (inherited from `Component`)
- Uses `_get_property`, `_set_property`, `_call_method` helpers for uniform get/set
- Uses `_start_listen` / `_stop_listen` to register Live property-change listeners that push updates to the OSC client

**OSC convention**: handlers that return data return a `tuple`; the OSC server sends the tuple as the reply to the same address that was queried. Handlers that only act (setters, methods) return `None`.

### Session Ring

`SessionRingHandler` is unique — it doesn't own the `SessionRingComponent` itself. The component lives on `Manager` (`manager.session_ring`) and is created/replaced via `manager.build_session_ring()`. This is because `SessionRingComponent` must be created inside `component_guard()`, which only `ControlSurface` methods can enter.

The handler delegates to `manager.build_session_ring(num_tracks, num_scenes, is_enabled)` on `/live/session_ring/on`. Listeners (`add_offset_listener`) are re-registered after each rebuild to avoid duplicate callbacks.

### OSC server

`abletonosc/osc_server.py` is a custom non-blocking UDP server (not pythonosc's threaded server, which caused beachballs in Live). It processes all queued packets synchronously in each `tick()`. Wildcard patterns (`*`) in OSC addresses are supported and matched against all registered handlers using a regex.

### Bundled pythonosc

`pythonosc/` is a vendored copy of the python-osc library, included because Live's embedded Python cannot install packages. Do not upgrade it via pip; modify in-place if changes are needed.

### Test client

`client/client.py` provides `AbletonOSCClient` for tests and scripts. It runs a `ThreadingOSCUDPServer` in a background thread to receive replies. Key methods:
- `send_message(address, params)` — fire and forget
- `query(address, params, timeout)` — send and wait for reply on the same address
- `await_message(address, timeout)` — wait for an unsolicited push message
