# AbletonOSC: Device-Specific API

This document is an addendum to [README.md](README.md). It covers the device-specific OSC address space — named access to properties, parameters, and functions for individual Ableton Live device classes, such as the Looper.

---

## Overview

The generic Device API (documented in README.md) exposes device controls by **numeric parameter index**. This is sufficient for building generic control surfaces, but code that needs to interact with a specific device by name — e.g., read the Looper's recording state, or trigger `undo` — requires the device-specific API described here.

### Address convention

Device-specific addresses use the device's class name in lowercase:

```
/live/device/<class>/get/<name>            track_id, device_id        →  track_id, device_id, value
/live/device/<class>/set/<name>            track_id, device_id, value
/live/device/<class>/start_listen/<name>   track_id, device_id        (immediately pushes current value, then on each change)
/live/device/<class>/stop_listen/<name>    track_id, device_id
/live/device/<class>/function/<name>       track_id, device_id
```

If the device at `(track_id, device_id)` has a different class name, the handler logs an error and sends no OSC reply.

### Discovering a device's class name

```
/live/device/get/class_name   track_id, device_id   →   track_id, device_id, class_name
```

### LOM terminology

The Cycling 74 [Live Object Model](https://docs.cycling74.com/apiref/lom/) distinguishes three kinds of members on a device:

- **Properties** — direct attributes on the device object (`loop_length`, `tempo`, `overdub_after_record`, etc.). Some are read-only; some are observable (have change listeners).
- **Parameters** — automation-capable controls that appear in `device.parameters` (the knobs and buttons you can record automation for, e.g. `State` on the Looper). Accessed by name, always observable.
- **Functions** — methods callable directly on the device (`record()`, `undo()`, `clear()`, etc.).

Both properties and parameters are accessed via the same `/get/`, `/set/`, `/start_listen/`, `/stop_listen/` OSC pattern. Functions use `/function/`.

---

## Generic Device API

The following addresses work for **any device**, regardless of class. See README.md for the full parameter list API.

| Address | Query params | Response params | Description |
|:--------|:-------------|:----------------|:------------|
| /live/device/get/name | track_id, device_id | track_id, device_id, name | Human-readable device name |
| /live/device/get/class_name | track_id, device_id | track_id, device_id, class_name | Device class (e.g. `Looper`, `Operator`) |
| /live/device/get/type | track_id, device_id | track_id, device_id, type | 1=audio_effect, 2=instrument, 4=midi_effect |
| /live/device/get/is_active | track_id, device_id | track_id, device_id, is_active | 1=enabled, 0=bypassed |
| /live/device/set/is_active | track_id, device_id, is_active | | Enable or bypass the device |
| /live/device/start_listen/is_active | track_id, device_id | | Subscribe to enabled state changes |
| /live/device/stop_listen/is_active | track_id, device_id | | Unsubscribe |

---

## Introspection

Each device class exposes introspection endpoints that return the names of its available properties, parameters, and functions:

| Address | Query params | Response params |
|:--------|:-------------|:----------------|
| /live/device/\<class\>/get/properties/name | track_id, device_id | track_id, device_id, name, name, ... |
| /live/device/\<class\>/get/parameters/name | track_id, device_id | track_id, device_id, name, name, ... |
| /live/device/\<class\>/get/functions/name | track_id, device_id | track_id, device_id, name, name, ... |

Example — list all Looper properties:
```
/live/device/looper/get/properties/name  0  0
→  0  0  "loop_length"  "overdub_after_record"  "record_length_index"  "record_length_list"  "tempo"
```

---

## Looper

The Looper (`class_name = "Looper"`) is Ableton's built-in audio looper device.

### Parameters

Parameters are automation-capable controls in `device.parameters`. They are always observable.

| Address | Query params | Response params | Description |
|:--------|:-------------|:----------------|:------------|
| /live/device/looper/get/state | track_id, device_id | track_id, device_id, state | Current state (float) |
| /live/device/looper/set/state | track_id, device_id, state | | Set state directly |
| /live/device/looper/start_listen/state | track_id, device_id | | Subscribe; immediately pushes current value |
| /live/device/looper/stop_listen/state | track_id, device_id | | Unsubscribe |

State values: `0` = Stop, `1` = Record, `2` = Play, `3` = Overdub.

### Properties

Direct attributes on the Looper device object. Read-only properties have no `/set/` handler. Non-observable properties have no `/start_listen/` or `/stop_listen/` handlers.

| Address | Query params | Response params | Description |
|:--------|:-------------|:----------------|:------------|
| /live/device/looper/get/loop_length | track_id, device_id | track_id, device_id, loop_length | Length of Looper's buffer (float, read-only) |
| /live/device/looper/start_listen/loop_length | track_id, device_id | | Subscribe to buffer length changes |
| /live/device/looper/stop_listen/loop_length | track_id, device_id | | Unsubscribe |
| /live/device/looper/get/tempo | track_id, device_id | track_id, device_id, tempo | Tempo of Looper's buffer in BPM (float, read-only) |
| /live/device/looper/start_listen/tempo | track_id, device_id | | Subscribe to buffer tempo changes |
| /live/device/looper/stop_listen/tempo | track_id, device_id | | Unsubscribe |
| /live/device/looper/get/record_length_list | track_id, device_id | track_id, device_id, str, str, ... | List of Record Length chooser options as strings (read-only, no listener) |
| /live/device/looper/get/record_length_index | track_id, device_id | track_id, device_id, record_length_index | Selected Record Length chooser index (int) |
| /live/device/looper/set/record_length_index | track_id, device_id, index | | Set the Record Length chooser |
| /live/device/looper/start_listen/record_length_index | track_id, device_id | | Subscribe to Record Length changes |
| /live/device/looper/stop_listen/record_length_index | track_id, device_id | | Unsubscribe |
| /live/device/looper/get/overdub_after_record | track_id, device_id | track_id, device_id, overdub_after_record | 1 = switch to Overdub after fixed-length recording, 0 = switch to Play |
| /live/device/looper/set/overdub_after_record | track_id, device_id, value | | Set overdub-after-record behaviour |
| /live/device/looper/start_listen/overdub_after_record | track_id, device_id | | Subscribe to changes |
| /live/device/looper/stop_listen/overdub_after_record | track_id, device_id | | Unsubscribe |

### Functions

Functions are methods called directly on the device. They send no OSC reply unless otherwise noted.

| Address | Query params | Description |
|:--------|:-------------|:------------|
| /live/device/looper/function/record | track_id, device_id | Start recording incoming audio |
| /live/device/looper/function/overdub | track_id, device_id | Play back while adding new layers |
| /live/device/looper/function/play | track_id, device_id | Play back without overdubbing |
| /live/device/looper/function/stop | track_id, device_id | Stop playback |
| /live/device/looper/function/undo | track_id, device_id | Erase everything since Overdub was last enabled; call again to restore |
| /live/device/looper/function/clear | track_id, device_id | Erase all recorded content |
| /live/device/looper/function/double_speed | track_id, device_id | Double playback speed |
| /live/device/looper/function/half_speed | track_id, device_id | Halve playback speed |
| /live/device/looper/function/double_length | track_id, device_id | Double the buffer length |
| /live/device/looper/function/half_length | track_id, device_id | Halve the buffer length |
