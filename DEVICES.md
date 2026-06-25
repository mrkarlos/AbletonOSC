# Device-Specific OSC Address Space

This document describes the design and implementation of device class-specific OSC handlers in AbletonOSC. It is intended as a reference for extending `/live/device/...` in future sessions.

---

## Background

AbletonOSC's generic device API (`/live/device/get/parameters/name`, `/live/device/get/parameter/value`, etc.) exposes device controls only by numeric index. That is sufficient for generic inspection but not for code that needs to act on a specific control by name — e.g., reading the Looper's recording state, or calling `undo`.

The device-specific address space adds named access, organised by device class, following the same Cycling 74 LOM (Live Object Model) terminology used in Max for Live.

---

## LOM Concepts: Properties, Parameters, Functions

This is the most important distinction for extending this feature. The Cycling 74 LOM docs describe three kinds of members on a device object:

### Properties
Direct Python attributes on the device object. Settable via `setattr`, readable via `getattr`. Many have change listeners via `device.add_<name>_listener(fn)` / `device.remove_<name>_listener(fn)`.

Examples on all devices:
- `device.name` (str)
- `device.class_name` (str, read-only, e.g. `"Looper"`, `"Operator"`)
- `device.type` (int)
- `device.is_active` (bool, enabled/bypassed)

### Parameters
Items in `device.parameters` — a list of `DeviceParameter` objects. These are the automation-capable controls (knobs, sliders, buttons). Each parameter has:
- `.name` (str) — display name, e.g. `"State"`, `"Feedback"`, `"Attack"`
- `.value` (float) — current value
- `.min`, `.max` (float)
- `.is_quantized` (bool)
- `.add_value_listener(fn)` / `.remove_value_listener(fn)`

Parameters are **not** direct attributes on the device object. `getattr(device, "state")` raises `AttributeError` for the Looper — you must find it by name in `device.parameters`.

### Functions
Methods callable directly on the device object, e.g. `device.undo()`, `device.clear()`. Not all device classes expose functions. The Cycling 74 LOM docs list them per class.

---

## The DEVICE_REGISTRY — Current State and Known Issue

`abletonosc/device_registry.py`:

```python
DEVICE_REGISTRY = {
    "Looper": {
        "properties": ["state"],       # MISLEADING: state is actually a Parameter
        "functions": ["undo", "clear"],
    },
}
```

**Known issue:** The registry uses the key `"properties"` for `state`, but `state` on the Looper is a **parameter** (lives in `device.parameters`), not a device property. The current implementation papers over this with a fallback: if `getattr(device, name)` raises `AttributeError`, it searches `device.parameters` by name (case-insensitive). This works, but loses the semantic distinction.

### Recommended future registry shape

To correctly distinguish types, the registry should be expanded to:

```python
DEVICE_REGISTRY = {
    "Looper": {
        "properties": [],              # Direct LOM properties unique to this class
        "parameters": ["state"],       # Named parameters (in device.parameters list)
        "functions": ["undo", "clear"],
    },
}
```

With this distinction, the handler factory can:
- For `"properties"`: use `getattr`/`setattr` + `add_<name>_listener`
- For `"parameters"`: look up by name in `device.parameters`, use `param.value` + `param.add_value_listener`

The OSC address convention does not need to change — both map to `/live/device/looper/get/<name>`.

---

## OSC Address Convention

Class name is lowercased in the path (matches `/live/clip/...`, `/live/track/...` convention). LOM terminology is used for path segments.

```
/live/device/<class>/get/<property>            track_id, device_id        →  track_id, device_id, value
/live/device/<class>/set/<property>            track_id, device_id, value
/live/device/<class>/function/<function>       track_id, device_id, *args →  track_id, device_id, *results (or no reply)
/live/device/<class>/start_listen/<property>   track_id, device_id        (immediately fires current value)
/live/device/<class>/stop_listen/<property>    track_id, device_id
/live/device/<class>/get/properties/name       track_id, device_id        →  track_id, device_id, *names
/live/device/<class>/get/functions/name        track_id, device_id        →  track_id, device_id, *names
```

If the device at `(track_id, device_id)` has a different `class_name`, the handler logs an error and returns no OSC reply.

### Looper address table

| Address | Args | Reply | Notes |
|---|---|---|---|
| `/live/device/looper/get/state` | track_id, device_id | track_id, device_id, state | 0=Stop, 1=Record, 2=Play, 3=Overdub |
| `/live/device/looper/set/state` | track_id, device_id, value | — | |
| `/live/device/looper/start_listen/state` | track_id, device_id | (immediate push, then on change) | |
| `/live/device/looper/stop_listen/state` | track_id, device_id | — | |
| `/live/device/looper/function/undo` | track_id, device_id | — | |
| `/live/device/looper/function/clear` | track_id, device_id | — | |
| `/live/device/looper/get/properties/name` | track_id, device_id | track_id, device_id, *names | Introspection |
| `/live/device/looper/get/functions/name` | track_id, device_id | track_id, device_id, *names | Introspection |

---

## Implementation Architecture

### Handler registration (`abletonosc/device.py`)

All class-specific handlers are registered programmatically in `DeviceHandler.init_api()` by iterating `DEVICE_REGISTRY`. The factory `create_device_class_callback(expected_class, action, name)` returns a closure that:

1. Extracts `track_index`, `device_index` from OSC params
2. Fetches `device = self.song.tracks[track_index].devices[device_index]`
3. Guards `device.class_name == expected_class` — returns `None` (no reply) if wrong class
4. Dispatches to get/set/function/start_listen/stop_listen/introspect logic

### Listener storage

Class-specific listeners are stored in `self._class_listeners` (a `dict` on `DeviceHandler`), keyed by `('class_property', class_name, track_index, device_index, prop_name)`. This is separate from the base class's `self.listener_functions` (which uses 2-tuple keys and is iterated by `_clear_listeners`). `DeviceHandler.clear_api()` drains `_class_listeners` before calling `super().clear_api()`.

### Fallback for parameters

The current `get`, `set`, and `start_listen` actions all try `getattr(device, name)` first, then fall back to `next(p for p in device.parameters if p.name.lower() == name.lower())`. This works but is a runtime probe, not a registry-declared type. See the "Known issue" section above.

---

## How to Add a New Device Class

1. Look up the device's `class_name` via `/live/device/get/class_name [track_id, device_id]`
2. Look up available parameter names via `/live/device/get/parameters/name [track_id, device_id]`
3. Consult the [Cycling 74 LOM docs](https://docs.cycling74.com/max8/vignettes/live_object_model) for the device's properties and functions
4. Add an entry to `DEVICE_REGISTRY` in `abletonosc/device_registry.py`
5. Reload with `/live/api/reload` — handlers are registered automatically
6. Add tests to `tests/test_device_specific.py`

Example — adding Simpler:

```python
DEVICE_REGISTRY = {
    "Looper": { ... },
    "OriginalSimpler": {       # class_name for Simpler
        "properties": [],
        "parameters": ["Volume", "Transpose"],
        "functions": ["crop"],
    },
}
```

Note: once the registry distinguishes `"properties"` from `"parameters"`, the factory needs a corresponding update to route each correctly (see "Recommended future registry shape" above).

---

## Generic Device API (all devices)

The following work for any device regardless of class, and are implemented in the existing `properties_r` / `properties_rw` loops plus explicit handlers in `device.py`:

| Address | Notes |
|---|---|
| `/live/device/get/name` | |
| `/live/device/get/class_name` | Use this to identify the device class before using class-specific handlers |
| `/live/device/get/type` | |
| `/live/device/get/is_active` | Enabled/bypassed state — read/write |
| `/live/device/set/is_active` | |
| `/live/device/start_listen/is_active` | |
| `/live/device/stop_listen/is_active` | |
| `/live/device/get/parameters/name` | Full parameter list — useful for discovering parameter names |
| `/live/device/get/parameters/value` | |
| `/live/device/get/parameter/value` | By index |
| `/live/device/set/parameter/value` | By index |
| `/live/device/start_listen/parameter/value` | By index |
| `/live/device/stop_listen/parameter/value` | By index |
