# AbletonOSC: Control Ableton Live with OSC

[![stability-beta](https://img.shields.io/badge/stability-beta-33bbff.svg)](https://github.com/mkenney/software-guides/blob/master/STABILITY-BADGES.md#beta)

AbletonOSC is a MIDI remote script that provides an [Open Sound Control (OSC)](https://ccrma.stanford.edu/groups/osc/) interface to
control [Ableton Live](https://www.ableton.com/en/live/). The project's aim is to expose the
entire [Live Object Model](https://docs.cycling74.com/max8/vignettes/live_object_model) API
([full API docs](https://structure-void.com/PythonLiveAPI_documentation/Live11.0.xml)), providing comprehensive control
over Live's control interfaces using the same naming structure and object hierarchy as LOM.

# Installation

AbletonOSC requires Ableton Live 11 or above.

To install the script:

- [Download a zip of this repository](https://github.com/ideoforms/AbletonOSC/archive/refs/heads/master.zip), unzip its contents, and rename `AbletonOSC-master` to `AbletonOSC`
- Install it following the instructions on
  Ableton's [Installing third-party remote scripts](https://help.ableton.com/hc/en-us/articles/209072009-Installing-third-party-remote-scripts)
  doc, by copying the `AbletonOSC` folder to:
    - **Windows**: `\Users\[username]\Documents\Ableton\User Library\Remote Scripts`
    - **macOS**: `Macintosh HD/Users/[username]/Music/Ableton/User Library/Remote Scripts`
- Restart Live
- In `Preferences > Link / Tempo / MIDI`, under the Control Surface dropdown, select the new "AbletonOSC" option. Live should display a message
  saying "AbletonOSC: Listening for OSC on port 11000"

Activity logs will be output to a `logs` subdirectory. Logging granularity can be controlled with `/live/api/set/log_level` (see [Application API](#application-api) below). 

# Usage

AbletonOSC listens for OSC messages on port **11000**, and sends replies on port **11001**. Replies will be sent to the
same IP as the originating message. When querying properties, OSC wildcard patterns can be used; for example, `/live/clip/get/* 0 0` will query all the properties of track 0, clip 0.

## Application API

<details>
<summary><b>Documentation</b>: Application API</summary>

| Address                       | Query params | Response params              | Description                                                                              |
|:------------------------------|:-------------|:-----------------------------|:-----------------------------------------------------------------------------------------|
| /live/test                    |              | 'ok'                         | Display a confirmation message in Live, and sends an OSC reply to /live/test             |
| /live/application/get/version |              | major_version, minor_version | Query Live's version                                                                     |
| /live/api/get/version         |              | version                      | Query AbletonOSC's own version (SemVer string, e.g. `"0.1.0"`), from the `VERSION` file at the repo root. Also logged once on startup. |
| /live/api/reload              |              |                              | Initiates a live reload of the AbletonOSC server code. Used in development only.         |
| /live/api/clear_listeners     |              |                              | Clears all registered Live API listener state (equivalent to what `/live/api/reload` does to each handler's listeners), without touching OSC address routing. Safe to call standalone, unlike a full reload. |
| /live/api/get/log_level       |              | log_level                    | Returns the current log level. Default is `info`.                                        |
| /live/api/set/log_level       | log_level    |                              | Set the log level, which can be one of: `debug`, `info`, `warning`, `error`, `critical`. |
| /live/api/show_message        | message      |                              | Show a message in Live's status bar                                                      |

### Application status messages

These messages are sent to the client automatically when the application state changes.

| Address       | Response params | Description                                                                                        |
|:--------------|:----------------|:---------------------------------------------------------------------------------------------------|
| /live/startup |                 | Sent to the client application when AbletonOSC is started                                          |
| /live/error   | error_msg       | Sent to the client application when an error occurs. For more diagnostics, see logs/abletonosc.log |

</details>

---

## Application View API

Represents `Application.View` — top-level UI/window state (which main view is focused,
hot-swap/browse mode) and the show/hide/focus/scroll/zoom view-navigation methods. No index
is required; there is only one Application.

<details>
<summary><b>Documentation</b>: Application View API</summary>

| Address                                            | Query params                            | Response params           | Description                                                                                     |
|:----------------------------------------------------|:-----------------------------------------|:---------------------------|:--------------------------------------------------------------------------------------------------|
| /live/application_view/get/browse_mode              |                                           | browse_mode                | Whether Hot-Swap Mode is active for any target (1 = active)                                       |
| /live/application_view/get/focused_document_view     |                                           | focused_document_view      | The name of the currently visible view ("Session" or "Arranger")                                  |
| /live/application_view/start_listen/browse_mode      |                                           | browse_mode                | Start listening; replies sent to `.../get/browse_mode`                                            |
| /live/application_view/stop_listen/browse_mode       |                                           |                             | Stop listening                                                                                     |
| /live/application_view/start_listen/focused_document_view |                                     | focused_document_view      | Start listening; replies sent to `.../get/focused_document_view`                                  |
| /live/application_view/stop_listen/focused_document_view  |                                     |                             | Stop listening                                                                                     |
| /live/application_view/get/available_main_views      |                                           | view_name, [view_name, ...]| Returns the list of view names usable with show_view/hide_view/focus_view/is_view_visible          |
| /live/application_view/get/is_view_visible           | view_name                                | is_visible                 | Whether the named view is currently visible                                                       |
| /live/application_view/show_view                     | view_name                                |                             | Show the named view (e.g. "Session", "Arranger", "Browser", "Detail", "Detail/Clip", "Detail/DeviceChain") |
| /live/application_view/hide_view                     | view_name                                |                             | Hide the named view (pass `" "` for the current main view)                                        |
| /live/application_view/focus_view                    | view_name                                |                             | Show and focus the named view (pass `" "` for the current main view)                              |
| /live/application_view/toggle_browse                 |                                           |                             | Show the device chain/browser and toggle Hot-Swap Mode for the selected device                    |
| /live/application_view/scroll_view                   | direction, view_name, modifier_pressed   |                             | Scroll a view. direction: 0=up, 1=down, 2=left, 3=right                                           |
| /live/application_view/zoom_view                     | direction, view_name, modifier_pressed   |                             | Zoom the Arrangement or Session view (same params as scroll_view)                                 |

</details>

---

## Song API

Represents the top-level Song object. Used to start/stop playback, create/modify scenes, create/jump to cue points, and set global parameters (tempo, metronome).

<details>
<summary><b>Documentation</b>: Song API</summary>

### Song methods

| Address                           | Query params | Response params | Description                                                                              |
|:----------------------------------|:-------------|:----------------|:-----------------------------------------------------------------------------------------|
| /live/song/capture_midi           |              |                 | Capture midi                                                                             |
| /live/song/continue_playing       |              |                 | Resume session playback                                                                  |
| /live/song/create_audio_track     | index        |                 | Create a new audio track at the specified index (-1 = end of list)                       |
| /live/song/create_midi_track      | index        |                 | Create a new MIDI track at the specified index (-1 = end of list)                        |
| /live/song/create_return_track    |              |                 | Create a new return track                                                                |
| /live/song/create_scene           | index        |                 | Create a new scene at the specified index (-1 = end of list)                             |
| /live/song/cue_point/jump         | cue_point    |                 | Jump to a specific cue point, by name or numeric index (based on the list of cue points) |
| /live/song/cue_point/add_or_delete |             |                 | Add a cue point under the cursor, or, if one exists, delete it |
| /live/song/cue_point/set/name         | cue_point    |                 | Rename a cue point, given its index |
| /live/song/delete_scene           | scene_index  |                 | Delete a scene                                                                           |
| /live/song/delete_return_track    | track_index  |                 | Delete a return track                                                                    |
| /live/song/delete_track           | track_index  |                 | Delete a track                                                                           |
| /live/song/duplicate_scene        | scene_index  |                 | Duplicate a scene                                                                        |
| /live/song/duplicate_track        | track_index  |                 | Duplicate a track                                                                        |
| /live/song/jump_by                | time         |                 | Jump song position by the specified time, in beats                                       |
| /live/song/jump_to_next_cue       |              |                 | Jump to the next cue marker                                                              |
| /live/song/jump_to_prev_cue       |              |                 | Jump to the previous cue marker                                                          |
| /live/song/redo                   |              |                 | Redo the last undone operation                                                           |
| /live/song/start_playing          |              |                 | Start session playback                                                                   |
| /live/song/stop_playing           |              |                 | Stop session playback                                                                    |
| /live/song/stop_all_clips         |              |                 | Stop all clips from playing                                                              |
| /live/song/tap_tempo              |              |                 | Mimics a tap of the "Tap Tempo" button                                                   |
| /live/song/trigger_session_record |              |                 | Triggers record in session mode                                                          |
| /live/song/undo                   |              |                 | Undo the last operation                                                                  |

### Song properties

 - Changes to any Track property can be listened for by calling `/live/song/start_listen/<property>`
 - Responses will be sent to `/live/song/get/<property>`, with parameters `<property_value>`
 - For further information on these properties and their parameters, see documentation
for [Live Object Model - Song](https://docs.cycling74.com/max8/vignettes/live_object_model#Song).
 
#### Getters

| Address                                    | Query params | Response params             | Description                                       |
|:-------------------------------------------|:-------------|:----------------------------|:--------------------------------------------------|
| /live/song/get/arrangement_overdub         |              | arrangement_overdub         | Query whether arrangement overdub is on           |
| /live/song/get/back_to_arranger            |              | back_to_arranger            | Query whether "back to arranger" is lit           |
| /live/song/get/can_redo                    |              | can_redo                    | Query whether redo is available                   |
| /live/song/get/can_undo                    |              | can_undo                    | Query whether undo is available                   |
| /live/song/get/clip_trigger_quantization   |              | clip_trigger_quantization   | Query the current clip trigger quantization level |
| /live/song/get/current_song_time           |              | current_song_time           | Query the current song time, in beats             |
| /live/song/get/groove_amount               |              | groove_amount               | Query the current groove amount                   |
| /live/song/get/is_playing                  |              | is_playing                  | Query whether the song is currently playing       |
| /live/song/get/loop                        |              | loop                        | Query whether the song is currently looping       |
| /live/song/get/loop_length                 |              | loop_length                 | Query the current loop length                     |
| /live/song/get/loop_start                  |              | loop_start                  | Query the current loop start point                |
| /live/song/get/metronome                   |              | metronome_on                | Query metronome on/off                            |
| /live/song/get/midi_recording_quantization |              | midi_recording_quantization | Query the current MIDI recording quantization     |
| /live/song/get/nudge_down                  |              | nudge_down                  | Query nudge down                                  |
| /live/song/get/nudge_up                    |              | nudge_up                    | Query nudge up                                    |
| /live/song/get/punch_in                    |              | punch_in                    | Query punch in                                    |
| /live/song/get/punch_out                   |              | punch_out                   | Query punch out                                   |
| /live/song/get/record_mode                 |              | record_mode                 | Query the current record mode                     |
| /live/song/get/root_note                 |              | root_note                 | Query the current root note                     |
| /live/song/get/scale_name                 |              | scale_name                 | Query the current scale name                     |
| /live/song/get/session_record              |              | session_record              | Query whether session record is enabled           |
| /live/song/get/session_record_status       |              | session_record_status       | Query the current session record status           |
| /live/song/get/signature_denominator       |              | denominator                 | Query the current time signature's denominator    |
| /live/song/get/signature_numerator         |              | numerator                   | Query the current time signature's numerator      |
| /live/song/get/song_length                 |              | song_length                 | Query the song arrangement length, in beats       |
| /live/song/get/tempo                       |              | tempo_bpm                   | Query the current song tempo                      |

#### Setters

| Address                                    | Query params                | Response params | Description                                             |
|:-------------------------------------------|:----------------------------|:----------------|:--------------------------------------------------------|
| /live/song/set/arrangement_overdub         | arrangement_overdub         |                 | Set arrangement overdub (1=on, 0=off)                   |
| /live/song/set/back_to_arranger            | back_to_arranger            |                 | Set whether "back to arranger" is lit (1=on, 0=off)     |
| /live/song/set/clip_trigger_quantization   | clip_trigger_quantization   |                 | Set the current clip trigger quantization level         |
| /live/song/set/current_song_time           | current_song_time           |                 | Set the current song time, in beats                     |
| /live/song/set/groove_amount               | groove_amount               |                 | Set the current groove amount                           |
| /live/song/set/loop                        | loop                        |                 | Set whether the song is currently looping (1=on, 0=off) |
| /live/song/set/loop_length                 | loop_length                 |                 | Set the current loop length                             |
| /live/song/set/loop_start                  | loop_start                  |                 | Set the current loop start point                        |
| /live/song/set/metronome                   | metronome_on                |                 | Set metronome (1=on, 0=off)                             |
| /live/song/set/midi_recording_quantization | midi_recording_quantization |                 | Set the current MIDI recording quantization             |
| /live/song/set/nudge_down                  | nudge_down                  |                 | Set nudge down                                          |
| /live/song/set/nudge_up                    | nudge_up                    |                 | Set nudge up                                            |
| /live/song/set/punch_in                    | punch_in                    |                 | Set punch in                                            |
| /live/song/set/punch_out                   | punch_out                   |                 | Set punch out                                           |
| /live/song/set/record_mode                 | record_mode                 |                 | Set the current record mode                             |
| /live/song/set/session_record              | session_record              |                 | Set whether session record is enabled (1=on, 0=off)     |
| /live/song/set/signature_denominator       | signature_denominator       |                 | Set the time signature's denominator                    |
| /live/song/set/signature_numerator         | signature_numerator         |                 | Set the time signature's numerator                      |
| /live/song/set/record_mode                 | record_mode                 |                 | Set the current record mode                             |
| /live/song/set/tempo                       | tempo_bpm                   |                 | Set the current song tempo                              |

### Song: Properties of cue points, scenes and tracks

| Address                    | Query params | Response params        | Description                                                                 |
|:---------------------------|:-------------|:-----------------------|:----------------------------------------------------------------------------|
| /live/song/get/cue_points  |              | name, time, ...        | Query a list of the song's cue points                                       |
| /live/song/get/num_scenes  |              | num_scenes             | Query the number of scenes. Can be listened for with `/live/song/start_listen/num_scenes` |
| /live/song/get/num_tracks  |              | num_tracks             | Query the number of tracks. Can be listened for with `/live/song/start_listen/num_tracks` |
| /live/song/get/track_names |              | [index_min, index_max] | Query track names (optionally, over a given range)                          |
| /live/song/get/tracks      |              | name, name, ...        | Query all track names in their current order                               |
| /live/song/get/scenes      |              | name, name, ...        | Query all scene names in their current order                                |
| /live/song/get/track_data  |              | [various]              | Query bulk properties of multiple tracks/clips. See below for further info. |
| /live/song/start_listen/track_data | index_min, index_max, prop, ... | [various] | Start bulk-listening for changes to the given properties, across the given tracks. See below for further info. |
| /live/song/stop_listen/track_data | index_min, index_max, [prop, ...] | | Stop bulk-listening. See below for further info. |
| /live/song/get/track_data_auto_rebuild |  | enabled | Query whether `track_data` listeners automatically extend to newly-created clips/tracks/scenes. See below. |
| /live/song/set/track_data_auto_rebuild | enabled | | Set whether `track_data` listeners automatically extend to newly-created clips/tracks/scenes. See below. |


#### Querying track/clip data in bulk with /live/song/get/track_data

It is often useful to be able to query data en masse about lots of different tracks and clips -- for example, when a set is first opened, to synchronise the state of your client with the Ableton set. This can be achieved with the `/live/song/get/track_data` API, which can query user-specified properties of multiple tracks and clips.

Properties must be of the format `track.property_name`, `clip.property_name`, `clip_slot.property_name` or `device.property_name`.

For example:
```
/live/song/get/track_data 0 12 track.name clip.name clip.length
```

Queries tracks 0..11, and returns a long list of values comprising:

```
[track_0_name, clip_0_0_name,   clip_0_1_name,   ... clip_0_7_name,
               clip_1_0_length, clip_0_1_length, ... clip_0_7_length,
 track_1_name, clip_1_0_name,   clip_1_1_name,   ... clip_1_7_name, ...]
```

#### Bulk-listening for track/clip data changes with /live/song/start_listen/track_data

Building the same picture of a set incrementally with individual `start_listen` calls
requires one call per track × scene combination. `start_listen/track_data` does it in one
call: it takes the same params as `get/track_data`, and

1. replies once, immediately, to `/live/song/get/track_data`, with exactly what a
   `get/track_data` call with the same params would have returned; then
2. arms the normal individual listener for every `track.*`/`clip.*`/`clip_slot.*`/`device.*`
   property in range -- so all *subsequent* updates arrive via the ordinary per-property
   addresses (`/live/track/get/<prop>`, `/live/clip/get/<prop>`, `/live/clip_slot/get/<prop>`,
   `/live/device/get/<prop>`), exactly as if you had called that object's own `start_listen`
   directly for every track/clip/device in range.

```
/live/song/start_listen/track_data 0 12 track.name clip.name clip.length
-> /live/song/get/track_data  [same shape as a get/track_data 0 12 track.name clip.name clip.length reply]
   ... later ...
-> /live/track/get/name  0 "Drums"
-> /live/clip/get/length 3 2 8.0
```

Repeated `start_listen/track_data` calls merge: a second call unions its own range ×
properties into whatever's already active, rather than replacing it.

`stop_listen/track_data <index_min> <index_max> [prop, ...]` reverses this. With properties
given, it removes exactly those track × property combinations; with none given, it removes
every `track_data` listener for tracks in that range, regardless of property.

By default (`track_data_auto_rebuild` enabled), coverage automatically follows structural
changes: a clip created in a previously-empty watched slot picks up its requested clip
properties with no further `start_listen` call, and listeners are dropped for clips/tracks
that disappear. Track/scene reorders are also handled. Devices added to or removed from a
track are **not** auto-tracked -- `device.*` coverage reflects whatever devices existed when
`start_listen`/the last rebuild ran; re-issue `start_listen/track_data` after a device is
added if you need it picked up. This can be disabled per-session with
`/live/song/set/track_data_auto_rebuild 0` if you'd rather manage re-subscription yourself;
the flag (and all `track_data` listen state) resets to enabled every time a Set is (re)loaded
or `/live/api/reload` runs.

Two caveats:

- `track.num_devices` is a synthetic value (`len(track.devices)`) with no native Live
  listener. `get/track_data` supports reading it; `start_listen/track_data` silently skips it
  (logging a warning) since there's nothing to listen to.
- `track.*`/`clip.*`/`clip_slot.*` listeners registered this way share the same underlying
  native listener as the plain `/live/track|clip|clip_slot/start_listen/<prop>` endpoints for
  the same track/clip index. If you also listen to the same property/index directly,
  `stop_listen/track_data` tearing it down will stop that listener too, and vice versa. This
  does not apply to `device.*` properties, which `track_data` always registers with explicit
  track/device ids, unlike the plain `/live/device/start_listen/<prop>` endpoints (other than
  `parameter/value`).

### Finding tracks and devices by name/class

Addresses like `/live/track/get/...` and `/live/device/get/...` identify a track/device by numeric index, which is fragile: indices shift whenever tracks are reordered or a set is reloaded, and track/device names are freely renamed by the user. `find_tracks` and `find_devices` let a client resolve the current index of a track or device from a more stable clue instead of hardcoding one.

| Address                    | Query params                                                | Response params                                          | Description                                                                        |
|:----------------------------|:-------------------------------------------------------------|:-----------------------------------------------------------|:-------------------------------------------------------------------------------------|
| /live/song/find_tracks      | name_pattern                                                  | [track_index, track_name, ...]                            | Find tracks whose name contains `name_pattern` (case-insensitive substring match)  |
| /live/song/find_devices     | class_name, [track_name_pattern], [device_name_pattern]       | [track_index, device_index, track_name, device_name, ...] | Find devices anywhere in the song matching `class_name` exactly, optionally narrowed by track/device name substring |

`class_name` (e.g. `"Looper"`) is the only identifier that survives track/device renames, so it's the required filter for `find_devices`; the name-pattern args are optional disambiguators for sets containing more than one device of the same class. Both calls return every match, flattened; an empty reply means no matches. See also `/live/track/find_devices` in the [Track API](#track-api) for scoping a device search to a track you've already resolved (e.g. via `find_tracks`).

For example, to locate a guitar track's Looper without hardcoding indices:
```
/live/song/find_tracks Guitar
-> (2, "Guitar")
/live/track/find_devices 2 Looper
-> (2, 0, "Looper")
```

### Beat events

To request a status message to be sent to the client on each beat, call `/live/song/start_listen/beat`. Every beat, a reply will be sent to `/live/song/get/beat`, with an int parameter containing the current beat number. To stop listening for beat events, call `/live/song/stop_listen/beat`.

### Track and scene order changes

To be notified whenever tracks or scenes are added, deleted, or reordered, call `/live/song/start_listen/tracks` (or `.../scenes`). A reply is sent immediately with the current state, and again every time it changes, to `/live/song/get/tracks` (or `.../scenes`), containing the full list of track (or scene) names in their current order. Call `/live/song/stop_listen/tracks` / `.../scenes` to stop.

| Address                          | Query params | Response params | Description                                             |
|:----------------------------------|:-------------|:-----------------|:---------------------------------------------------------|
| /live/song/start_listen/tracks   |              |                  | Start listening; replies sent to `.../get/tracks`        |
| /live/song/stop_listen/tracks    |              |                  | Stop listening for track list changes                    |
| /live/song/start_listen/scenes   |              |                  | Start listening; replies sent to `.../get/scenes`        |
| /live/song/stop_listen/scenes    |              |                  | Stop listening for scene list changes                    |

</details>

---

## View API

Represents the view (user interface) of live. This section covers Song.View's selection
state only (`selected_scene`/`selected_track`/`selected_clip`/`selected_device`), kept here
for backward compatibility. [Song View API](#song-view-api) below covers the full
`Song.View` class, including duplicates of everything in this section — new integrations
should prefer `/live/song_view/*` over this legacy namespace.

<details>
<summary><b>Documentation</b>: View API</summary>

| Address                                | Query params             | Response params          | Description                                             |
|:---------------------------------------|:-------------------------|:-------------------------|:--------------------------------------------------------|
| /live/view/get/selected_scene          |                          | scene_index              | Returns the selected scene index (first scene = 0)      |
| /live/view/get/selected_track          |                          | track_index              | Returns the selected index track (first track = 0)      |
| /live/view/get/selected_clip           |                          | track_index, scene_index | Returns the track and scene index of the selected clip  |
| /live/view/get/selected_device         |                          | track_index, device_index| Get the selected device (first device = 0)              |
| /live/view/set/selected_scene          | scene_index              |                          | Set the selected scene (first scene = 0)                |
| /live/view/set/selected_track          | track_index              |                          | Set the selected track (first track = 0)                |
| /live/view/set/selected_clip           | track_index, scene_index |                          | Set the selected clip                                   |
| /live/view/set/selected_device         | track_index, device_index|                          | Set the selected device (first device = 0)              |
| /live/view/start_listen/selected_scene |                          | selected_scene           | Start listening to the selected scene (first scene = 0) |
| /live/view/start_listen/selected_track |                          | selected_track           | Start listening to selected track (first track = 0)     |
| /live/view/stop_listen/selected_scene  |                          |                          | Stop listening to the selected scene (first scene = 0)  |
| /live/view/stop_listen/selected_track  |                          |                          | Stop listening to selected track (first track = 0)      |
</details>

---

## Song View API

Represents the full public surface of Live's `Song.View` class — draw_mode, follow_song,
detail_clip, highlighted_clip_slot, selected_scene, selected_track, selected_device, and
the derived selected_clip convenience.

`selected_scene`/`selected_track`/`selected_clip`/`selected_device` are also available
under legacy [View API](#view-api) (`/live/view/*`), kept there for backward compatibility.
They're deliberately duplicated here too — as an independent implementation, not a
delegation — so `/live/song_view/*` is a strict superset of `/live/view/*`: if `/live/view/*`
is ever deprecated, anything already using `/live/song_view/*` is unaffected.

<details>
<summary><b>Documentation</b>: Song View API</summary>

| Address                                        | Query params              | Response params           | Description                                                                                     |
|:------------------------------------------------|:---------------------------|:----------------------------|:--------------------------------------------------------------------------------------------------|
| /live/song_view/get/draw_mode                    |                            | draw_mode                  | Automation Draw Mode state (0 = breakpoint editing, 1 = drawing)                                  |
| /live/song_view/set/draw_mode                    | draw_mode                  |                             | Set Draw Mode                                                                                      |
| /live/song_view/start_listen/draw_mode           |                            | draw_mode                  | Start listening; replies sent to `.../get/draw_mode`                                              |
| /live/song_view/stop_listen/draw_mode            |                            |                             | Stop listening                                                                                     |
| /live/song_view/get/follow_song                  |                            | follow_song                | Follow switch state (0 = don't follow playback position, 1 = follow)                              |
| /live/song_view/set/follow_song                  | follow_song                |                             | Set the Follow switch                                                                              |
| /live/song_view/start_listen/follow_song         |                            | follow_song                | Start listening; replies sent to `.../get/follow_song`                                            |
| /live/song_view/stop_listen/follow_song          |                            |                             | Stop listening                                                                                     |
| /live/song_view/get/detail_clip                  |                            | track_index, clip_index    | The clip shown in Detail View, as (track_index, clip_index); (-1, -1) if none. Note: an Arrangement-view detail clip is also reported as (-1, -1), since it has no clip_slot address. |
| /live/song_view/set/detail_clip                  | track_index, clip_index    |                             | Show the given clip in Detail View. (-1, -1) is a documented no-op, not a clear — Live's API has no supported way to explicitly clear detail_clip; it only reverts to (-1, -1) as a side effect of the underlying clip being deleted |
| /live/song_view/start_listen/detail_clip         |                            | track_index, clip_index    | Start listening; replies sent to `.../get/detail_clip`                                            |
| /live/song_view/stop_listen/detail_clip          |                            |                             | Stop listening                                                                                     |
| /live/song_view/get/highlighted_clip_slot        |                            | track_index, clip_index    | The Session View slot currently highlighted, as (track_index, clip_index); (-1, -1) if none       |
| /live/song_view/set/highlighted_clip_slot        | track_index, clip_index    |                             | Set the highlighted slot                                                                            |
| /live/song_view/get/selected_scene               |                            | scene_index                | Returns the selected scene index (first scene = 0)                                                |
| /live/song_view/set/selected_scene               | scene_index                |                             | Set the selected scene (first scene = 0)                                                          |
| /live/song_view/start_listen/selected_scene      |                            | scene_index                 | Start listening; replies sent to `.../get/selected_scene`                                         |
| /live/song_view/stop_listen/selected_scene       |                            |                             | Stop listening                                                                                     |
| /live/song_view/get/selected_track               |                            | track_index                | Returns the selected track index (first track = 0)                                                |
| /live/song_view/set/selected_track               | track_index                |                             | Set the selected track (first track = 0)                                                          |
| /live/song_view/start_listen/selected_track      |                            | track_index                 | Start listening; replies sent to `.../get/selected_track`                                         |
| /live/song_view/stop_listen/selected_track       |                            |                             | Stop listening                                                                                     |
| /live/song_view/get/selected_clip                |                            | track_index, scene_index   | Returns the track and scene index of the selected clip (derived from selected_track + selected_scene; not a real Song.View property) |
| /live/song_view/set/selected_clip                | track_index, scene_index   |                             | Set the selected clip (sets selected_track and selected_scene together)                            |
| /live/song_view/start_listen/selected_clip       |                            | track_index, scene_index   | Start listening (fires on either selected_track or selected_scene changing)                       |
| /live/song_view/stop_listen/selected_clip        |                            |                             | Stop listening                                                                                     |
| /live/song_view/get/selected_device              |                            | track_index, device_index  | The selected device on the selected track (first device = 0); -1 if none selected                 |
| /live/song_view/set/selected_device              | track_index, device_index  |                             | Select the given device (wraps Song.View.select_device(device))                                    |
| /live/song_view/start_listen/selected_device     |                            | track_index, device_index  | Start listening (re-attaches across a selected_track change)                                       |
| /live/song_view/stop_listen/selected_device      |                            |                             | Stop listening                                                                                     |

Notes:
- `highlighted_clip_slot` has no `start_listen`/`stop_listen` support — Live does not expose
  a listener for this property.
- `selected_chain` and `selected_parameter` (Song.View's remaining two members) are not yet
  supported: both need a chain/parameter addressing scheme this codebase doesn't have yet
  (the same reason [Clip View API](#clip-view-api)'s `select_envelope_parameter` is omitted).

</details>

---

## Track API

Represents an audio, MIDI, return or master track. Can be used to set track audio parameters (volume, panning, send, mute, solo), listen for the playing clip slot, query devices, etc. Can also be used to query clips in arrangement view.

To query the properties of multiple tracks, see [Song: Properties of cue points, scenes and tracks](https://github.com/ideoforms/AbletonOSC#song-properties-of-cue-points-scenes-and-tracks).

<details>
<summary><b>Documentation</b>: Track API</summary>

### Track methods

| Address                    | Query params | Response params | Description             |
|:---------------------------|:-------------|:----------------|:------------------------|
| /live/track/stop_all_clips | track_id     |                 | Stop all clips on track |

### Track properties

 - Changes for any Track property can be listened for by calling `/live/track/start_listen/<property> <track_index>`
 - Responses will be sent to `/live/track/get/<property>`, with parameters `<track_index> <property_value>`

#### Getters

| Address                                           | Query params      | Response params            | Description                                       |
|:--------------------------------------------------|:------------------|:---------------------------|:--------------------------------------------------|
| /live/track/get/arm                               | track_id          | track_id, armed            | Query whether track is armed                      |
| /live/track/get/available_input_routing_channels  | track_id          | track_id, channel, ...     | List input channels (e.g. "1", "2", "1/2", ...)   |
| /live/track/get/available_input_routing_types     | track_id          | track_id, type, ...        | List input routes (e.g. "Ext. In", ...)           |
| /live/track/get/available_output_routing_channels | track_id          | track_id, channel, ...     | List output channels (e.g. "1", "2", "1/2", ...)  |
| /live/track/get/available_output_routing_types    | track_id          | track_id, type, ...        | List output routes (e.g. "Ext. Out", ...)         |
| /live/track/get/can_be_armed                      | track_id          | track_id, can_be_armed     | Query whether track can be armed                  |
| /live/track/get/color                             | track_id          | track_id, color            | Query track color                                 |
| /live/track/get/color_index                       | track_id          | track_id, color_index      | Query track color index                           |
| /live/track/get/current_monitoring_state          | track_id          | track_id, state            | Query current monitoring state (1=on, 0=off)      |
| /live/track/get/fired_slot_index                  | track_id          | track_id, index            | Query currently-fired slot                        |
| /live/track/get/fold_state                        | track_id          | track_id, fold_state       | Query folded state (for groups)                   |
| /live/track/get/has_audio_input                   | track_id          | track_id, has_audio_input  | Query has_audio_input                             |
| /live/track/get/has_audio_output                  | track_id          | track_id, has_audio_output | Query has_audio_output                            |
| /live/track/get/has_midi_input                    | track_id          | track_id, has_midi_input   | Query has_midi_input                              |
| /live/track/get/has_midi_output                   | track_id          | track_id, has_midi_output  | Query has_midi_output                             |
| /live/track/get/input_routing_channel             | track_id          | track_id, channel          | Query current input routing channel               |
| /live/track/get/input_routing_type                | track_id          | track_id, type             | Query current input routing type                  |
| /live/track/get/output_routing_channel            | track_id          | track_id, channel          | Query current output routing channel              |
| /live/track/get/output_meter_left                 | track_id          | track_id, level            | Query current output level, left channel          |
| /live/track/get/output_meter_level                | track_id          | track_id, level            | Query current output level, both channels         |
| /live/track/get/output_meter_right                | track_id          | track_id, level            | Query current output level, right channel         |
| /live/track/get/output_routing_type               | track_id          | track_id, type             | Query current output routing type                 |
| /live/track/get/is_foldable                       | track_id          | track_id, is_foldable      | Query whether track is foldable, i.e. is a group  |
| /live/track/get/is_grouped                        | track_id          | track_id, is_grouped       | Query whether track is in a group                 |
| /live/track/get/is_visible                        | track_id          | track_id, is_visible       | Query whether track is visible (1=on, 0=off)      |
| /live/track/get/mute                              | track_id          | track_id, mute             | Query track mute (1=on, 0=off)                    |
| /live/track/get/name                              | track_id          | track_id, name             | Query track name                                  |
| /live/track/get/panning                           | track_id          | track_id, panning          | Query track panning                               |
| /live/track/get/playing_slot_index                | track_id          | track_id, index            | Query currently-playing slot                      |
| /live/track/get/send                              | track_id, send_id | track_id, send_id, value   | Query track send                                  |
| /live/track/get/solo                              | track_id          | track_id, solo             | Query track solo on/off                           |
| /live/track/get/volume                            | track_id          | track_id, volume           | Query track volume                                |

#### Setters

| Address                                  | Query params             | Response params | Description                       |
|:-----------------------------------------|:-------------------------|:----------------|:----------------------------------|
| /live/track/set/arm                      | track_id, armed          |                 | Set track arm state (1=on, 0=off) |
| /live/track/set/color                    | track_id, color          |                 | Set track color                   |
| /live/track/set/color_index              | track_id, color_index    |                 | Set track color index             |
| /live/track/set/current_monitoring_state | track_id, state          |                 | Set monitoring on/off             |
| /live/track/set/fold_state               | track_id, fold_state     |                 | Set group folded (1=on, 0=off)    |
| /live/track/set/input_routing_channel    | track_id, channel        |                 | Set input routing channel         |
| /live/track/set/input_routing_type       | track_id, type           |                 | Set input routing type            |
| /live/track/set/mute                     | track_id, mute           |                 | Set track mute (1=on, 0=off)      |
| /live/track/set/name                     | track_id, name           |                 | Set track name                    |
| /live/track/set/output_routing_channel   | track_id, channel        |                 | Set output routing channel        |
| /live/track/set/output_routing_type      | track_id, type           |                 | Set output routing type           |
| /live/track/set/panning                  | track_id, panning        |                 | Set track panning                 |
| /live/track/set/send                     | track_id, send_id, value |                 | Set track send                    |
| /live/track/set/solo                     | track_id, solo           |                 | Set track solo (1=on, 0=off)      |
| /live/track/set/volume                   | track_id, volume         |                 | Set track volume                  |

### Track: Properties of multiple clips

| Address                                      | Query params | Response params             | Description                                      |
|:---------------------------------------------|:-------------|:----------------------------|:-------------------------------------------------|
| /live/track/get/clips/name                   | track_id     | track_id, [name, ....]      | Query all clip names on track                    |
| /live/track/get/clips/length                 | track_id     | track_id, [length, ...]     | Query all clip lengths on track                  |
| /live/track/get/clips/color                  | track_id     | track_id, [color, ...]      | Query all clip colors on track                   |
| /live/track/get/arrangement_clips/name       | track_id     | track_id, [name, ....]      | Query all arrangement view clip names on track   |
| /live/track/get/arrangement_clips/length     | track_id     | track_id, [length, ...]     | Query all arrangement view clip lengths on track |
| /live/track/get/arrangement_clips/start_time | track_id     | track_id, [start_time, ...] | Query all arrangement view clip times on track   |

### Track: Properties of devices
| Address                            | Query params | Response params        | Description                              |
|:-----------------------------------|:-------------|:-----------------------|:-----------------------------------------|
| /live/track/get/num_devices        | track_id     | track_id, num_devices  | Query the number of devices on the track |
| /live/track/get/devices/name       | track_id     | track_id, [name, ...]  | Query all device names on track          |
| /live/track/get/devices/type       | track_id     | track_id, [type, ...]  | Query all devices types on track         |
| /live/track/get/devices/class_name | track_id     | track_id, [class, ...] | Query all device class names on track    |
| /live/track/find_devices           | track_id, class_name, [device_name_pattern] | track_id, [device_index, device_name, ...] | Find devices on this track matching `class_name` exactly, optionally narrowed by a device-name substring |

See [Device API](#device-api) for details on Device type/class_names, and [Finding tracks and devices by name/class](#finding-tracks-and-devices-by-nameclass) for the companion `/live/song/find_tracks` / `/live/song/find_devices` calls.
 
</details>

---

## Track View API

Represents Live's `Track.View` class, indexed by `track_index`.

<details>
<summary><b>Documentation</b>: Track View API</summary>

| Address                                       | Query params                | Response params              | Description                                                                                  |
|:------------------------------------------------|:------------------------------|:--------------------------------|:-------------------------------------------------------------------------------------------------|
| /live/track_view/get/device_insert_mode          | track_id                      | track_id, device_insert_mode    | Where a device is inserted when loaded from the browser (0 = end, 1 = left of selected device, 2 = right) |
| /live/track_view/set/device_insert_mode          | track_id, device_insert_mode  |                                  | Set device_insert_mode                                                                            |
| /live/track_view/start_listen/device_insert_mode | track_id                      | track_id, device_insert_mode    | Start listening; replies sent to `.../get/device_insert_mode`                                    |
| /live/track_view/stop_listen/device_insert_mode  | track_id                      |                                  | Stop listening                                                                                    |
| /live/track_view/get/is_collapsed                | track_id                      | track_id, is_collapsed          | Whether the track is collapsed in Arrangement View                                               |
| /live/track_view/set/is_collapsed                | track_id, is_collapsed        |                                  | Set is_collapsed                                                                                   |
| /live/track_view/start_listen/is_collapsed       | track_id                      | track_id, is_collapsed          | Start listening; replies sent to `.../get/is_collapsed`                                          |
| /live/track_view/stop_listen/is_collapsed        | track_id                      |                                  | Stop listening                                                                                    |
| /live/track_view/get/selected_device             | track_id                      | track_id, device_index          | The selected device on this track (first device = 0); -1 if none selected                        |
| /live/track_view/start_listen/selected_device    | track_id                      | track_id, device_index          | Start listening; replies sent to `.../get/selected_device`                                       |
| /live/track_view/stop_listen/selected_device     | track_id                      |                                  | Stop listening                                                                                    |
| /live/track_view/select_instrument               | track_id                      | track_id, selected              | Select the track's instrument or first device. `selected` is 0 if no devices are available        |

`track_id` also accepts the wildcard `"*"` to apply to all tracks, matching the [Track API](#track-api) convention.

Note: `device_insert_mode` is documented in Cycling '74's LOM reference as a 3-way int enum
(0/1/2), but was observed returning/accepting a plain bool at runtime in Live 12.3. This
handler is a pure passthrough of whatever Live returns, so treat the value's exact type as
Live-version-dependent rather than relying on the documented int semantics.

</details>

---

## Clip Slot API

A Clip Slot represents a container for a clip. It is used to create and delete clips, and query their existence.

<details>
<summary><b>Documentation</b>: Clip Slot API</summary>

| Address                             | Query params                                                   | Response params                          | Description                                     |
|:------------------------------------|:---------------------------------------------------------------|:-----------------------------------------|:------------------------------------------------|
| /live/clip_slot/fire                | track_index, clip_index                                        |                                          | Fire play/pause of the specified clip slot      |
| /live/clip_slot/create_clip         | track_index, clip_index, length                                |                                          | Create a clip in the slot                       |
| /live/clip_slot/delete_clip         | track_index, clip_index                                        |                                          | Delete the clip in the slot                     |
| /live/clip_slot/get/has_clip        | track_index, clip_index                                        | track_index, clip_index, has_clip        | Query whether the slot has a clip               |
| /live/clip_slot/get/has_stop_button | track_index, clip_index                                        | track_index, clip_index, has_stop_button | Query whether the slot has a stop button        |
| /live/clip_slot/set/has_stop_button | track_index, clip_index, has_stop_button                       |                                          | Add or remove stop button (1=on, 0=off)         |
| /live/clip_slot/duplicate_clip_to   | track_index, clip_index, target_track_index, target_clip_index |                                          | Duplicate the clip to an empty target clip slot |

</details>

---

## Clip API

Represents an audio or MIDI clip. Can be used to start/stop clips, and query/modify their notes, name, gain, pitch, color, playing state/position, etc.

<details>
<summary><b>Documentation</b>: Clip API</summary>

| Address                                  | Query params                                                        | Response params                                                                        | Description                                                                                                                                              |
|:-----------------------------------------|:--------------------------------------------------------------------|:---------------------------------------------------------------------------------------|:---------------------------------------------------------------------------------------------------------------------------------------------------------|
| /live/clip/fire                          | track_id, clip_id                                                   |                                                                                        | Start clip playback                                                                                                                                      |
| /live/clip/stop                          | track_id, clip_id                                                   |                                                                                        | Stop clip playback                                                                                                                                       |
| /live/clip/duplicate_loop                | track_id, clip_id                                                   |                                                                                        | Duplicates clip loop                                                                                                                                     |
| /live/clip/get/notes                     | track_id, clip_id, [start_pitch, pitch_span, start_time, time_span] | track_id, clip_id, pitch, start_time, duration, velocity, mute, [pitch, start_time...] | Query the notes in a given clip, optionally including a start time/pitch and time/pitch span.                                                            |
| /live/clip/add/notes                     | track_id, clip_id, pitch, start_time, duration, velocity, mute, ... |                                                                                        | Add new MIDI notes to a clip. pitch is MIDI note index, start_time and duration are beats in floats, velocity is MIDI velocity index, mute is true/false |
| /live/clip/remove/notes                  | [start_pitch, pitch_span, start_time, time_span]                    |                                                                                        | Remove notes from a clip in a range of pitches and times. If no ranges specified, all notes are removed. Note that ordering has changed as of 2023-11.   |
| /live/clip/get/color                     | track_id, clip_id                                                   | track_id, clip_id, color                                                               | Get clip color                                                                                                                                           |
| /live/clip/set/color                     | track_id, clip_id, color                                            |                                                                                        | Set clip color                                                                                                                                           |
| /live/clip/get/color_index               | track_id, clip_id                                                   | track_id, clip_id, color_index                                                               | Get clip color index (0-69)                                                                                                                                           |
| /live/clip/set/color_index               | track_id, clip_id, color_index                                      |                                                                                        | Set clip color index (0-69)                                                                                                                                          |
| /live/clip/get/name                      | track_id, clip_id                                                   | track_id, clip_id, name                                                                | Get clip name                                                                                                                                            |
| /live/clip/set/name                      | track_id, clip_id, name                                             |                                                                                        | Set clip name                                                                                                                                            |
| /live/clip/get/gain                      | track_id, clip_id                                                   | track_id, clip_id, gain                                                                | Get clip gain                                                                                                                                            |
| /live/clip/set/gain                      | track_id, clip_id, gain                                             |                                                                                        | Set clip gain                                                                                                                                            |
| /live/clip/get/length                    | track_id, clip_id                                                   | track_id, clip_id, length                                                              | Get clip length                                                                                                                                          |
| /live/clip/get/sample_length              | track_id, clip_id                                                   | track_id, clip_id, sample_length                                                           | Get clip sample length                                                                                                                                 |
| /live/clip/get/start_time              | track_id, clip_id                                                   | track_id, clip_id, start_time                                                           | Get clip start time                                                                                                                                 |
| /live/clip/get/pitch_coarse              | track_id, clip_id                                                   | track_id, clip_id, semitones                                                           | Get clip coarse re-pitch                                                                                                                                 |
| /live/clip/set/pitch_coarse              | track_id, clip_id, semitones                                        |                                                                                        | Set clip coarse re-pitch                                                                                                                                 |
| /live/clip/get/pitch_fine                | track_id, clip_id                                                   | track_id, clip_id, cents                                                               | Get clip fine re-pitch                                                                                                                                   |
| /live/clip/set/pitch_fine                | track_id, clip_id, cents                                            |                                                                                        | Set clip fine re-pitch                                                                                                                                   |
| /live/clip/get/file_path                 | track_id, clip_id                                                   | track_id, clip_id, file_path                                                           | Get clip file path                                                                                                                                       |
| /live/clip/get/is_audio_clip             | track_id, clip_id                                                   | track_id, clip_id, is_audio_clip                                                       | Query whether clip is audio                                                                                                                              |
| /live/clip/get/is_midi_clip              | track_id, clip_id                                                   | track_id, clip_id, is_midi_clip                                                        | Query whether clip is MIDI                                                                                                                               |
| /live/clip/get/is_playing                | track_id, clip_id                                                   | track_id, clip_id, is_playing                                                          | Query whether clip is playing                                                                                                                            |
| /live/clip/get/is_overdubbing                | track_id, clip_id                                                   | track_id, clip_id, is_overdubbing                                                          | Query whether clip is overdubbing                                                                                                                            |
| /live/clip/get/is_recording              | track_id, clip_id                                                   | track_id, clip_id, is_recording                                                        | Query whether clip is recording                                                                                                                          |
| /live/clip/get/will_record_on_start                | track_id, clip_id                                                   | track_id, clip_id, will_record_on_start                                                          | Query whether clip will record on start                                                                                                                            |
| /live/clip/get/playing_position          | track_id, clip_id                                                   | track_id, clip_id, playing_position                                                    | Get clip's playing position                                                                                                                              |
| /live/clip/start_listen/playing_position | track_id, clip_id                                                   |                                                                                        | Start listening for clip's playing position. Replies are sent to /live/clip/get/playing_position, with args: track_id, clip_id, playing_position         |
| /live/clip/stop_listen/playing_position  | track_id, clip_id                                                   |                                                                                        | Stop listening for clip's playing position.                                                                                                              |
| /live/clip/get/loop_start                | track_id, clip_id                                                   | track_id, clip_id, loop_start                                                          | Get clip's loop start                                                                                                                                    |
| /live/clip/set/loop_start                | track_id, clip_id, loop_start                                       |                                                                                        | Set clip's loop start                                                                                                                                    |
| /live/clip/get/loop_end                  | track_id, clip_id                                                   | track_id, clip_id, loop_end                                                            | Get clip's loop end                                                                                                                                      |
| /live/clip/set/loop_end                  | track_id, clip_id, loop_end                                         |                                                                                        | Set clip's loop end                                                                                                                                      |
| /live/clip/get/warping                   | track_id, clip_id                                                   | track_id, clip_id, warping                                                             | Get clip's warp mode                                                                                                                                     |
| /live/clip/set/warping                   | track_id, clip_id, warping                                          |                                                                                        | Set clip's warp mode                                                                                                                                     |
| /live/clip/get/launch_mode                   | track_id, clip_id                                                   | track_id, clip_id, launch_mode                                                             | Get clip's launch mode (0=Trigger, 1=Gate, 2=Toggle, 3=Repeat)                                                                                                                                    |
| /live/clip/set/launch_mode                   | track_id, clip_id, launch_mode                                          |                                                                                        | Set clip's launch mode (0=Trigger, 1=Gate, 2=Toggle, 3=Repeat)                                                                                                                                     |
| /live/clip/get/launch_quantization                   | track_id, clip_id                                                   | track_id, clip_id, launch_quantization                                                             | Get clip's launch Quantization Value (0=Global, 1=None, 2=8Bars, 3=4Bars, 4=2Bars, 5=1Bar, 6=1/2, 7=1/2T, 8=1/4, 9=1/4T, 10=1/8, 11=1/8T, 12=1/16, 13=1/16T, 14=1/32)                                                                                                                                    |
| /live/clip/set/launch_quantization                   | track_id, clip_id, launch_quantization                                          |                                                                                        | Set clip's launch Quantization Value (0=Global, 1=None, 2=8Bars, 3=4Bars, 4=2Bars, 5=1Bar, 6=1/2, 7=1/2T, 8=1/4, 9=1/4T, 10=1/8, 11=1/8T, 12=1/16, 13=1/16T, 14=1/32)                                                                                                                                     |
| /live/clip/get/ram_mode                   | track_id, clip_id                                                   | track_id, clip_id, ram_mode                                                             | Get clip's Ram Mode (0=False, 1=True)                                                                                                      |
| /live/clip/set/ram_mode                   | track_id, clip_id, ram_mode                                          |                                                                                        | Set clip's Ram Mode (0=False, 1=True)                                                                                                                                     |
| /live/clip/get/warp_mode                   | track_id, clip_id                                                   | track_id, clip_id, warp_mode                                                             | Get clip's Warp Mode (0=Beats, 1=Tones, 2=Texture, 3=Re-Pitch, 4=Complex, 5=Invalid/Error, 6=Pro)                                                                                                     |
| /live/clip/set/warp_mode                   | track_id, clip_id, warp_mode                                          |                                                                                        | Set clip's Warp Mode (0=Beats, 1=Tones, 2=Texture, 3=Re-Pitch, 4=Complex, 5=Invalid/Error, 6=Pro)                                                                                                                                    |
| /live/clip/get/has_groove                   | track_id, clip_id                                                   | track_id, clip_id, has_groove                                                             | Get clip Groove state (0=False, 1=True)
| /live/clip/get/groove                   | track_id, clip_id                                                   | track_id, clip_id, groove_name                                                             | Get the name of the clip's assigned groove, or an empty string if none is set                                                                                                                                     |
| /live/clip/get/legato                   | track_id, clip_id                                                   | track_id, clip_id, legato                                                             | Get clip's Legato state (0=False, 1=True)                                                                                                      |
| /live/clip/set/legato                   | track_id, clip_id, legato                                          |                                                                                        | Set clip's Legato state (0=False, 1=True)                                                                                                                                     |
| /live/clip/get/position                   | track_id, clip_id                                                   | track_id, clip_id, position                                                             | Get clip's position (LoopStart)                                                                                                     |
| /live/clip/set/position                   | track_id, clip_id, position                                          |                                                                                        | Set clip's position (LoopStart)                                                                                                                                     |
| /live/clip/get/muted                   | track_id, clip_id                                                   | track_id, clip_id, muted                                                             | Get clip's Muted state (0=False, 1=True)                                                                                                      |
| /live/clip/set/muted                   | track_id, clip_id, muted                                          |                                                                                        | Set clip's Muted state (0=False, 1=True)                                                                                                                                     |
| /live/clip/get/velocity_amount              | track_id, clip_id                                                   | track_id, clip_id, velocity_amount                                                       | Get clip's Velocity Amount (0.0-1.0 aka 0% to 100%)                                                                                                                                  |
| /live/clip/set/velocity_amount              | track_id, clip_id, velocity_amount                                     |                                                                                        | Set clip's Velocity Amount (0.0-1.0 aka 0% to 100%)                                                                                               |
| /live/clip/get/start_marker              | track_id, clip_id                                                   | track_id, clip_id, start_marker                                                        | Get clip's start marker                                                                                                                                  |
| /live/clip/set/start_marker              | track_id, clip_id, start_marker                                     |                                                                                        | Set clip's start marker, expressed in floating-point beats                                                                                               |
| /live/clip/get/end_marker                | track_id, clip_id                                                   | track_id, clip_id, end_marker                                                          | Get clip's end marker                                                                                                                                    |
| /live/clip/set/end_marker                | track_id, clip_id, end_marker                                       |                                                                                        | Set clip's end marker, expressed in floating-point beats                                                                                                 |

</details>

---

## Clip View API

Represents Live's `Clip.View` class, indexed by `(track_id, clip_id)` — same addressing as
[Clip API](#clip-api).

<details>
<summary><b>Documentation</b>: Clip View API</summary>

| Address                                  | Query params                    | Response params                     | Description                                                             |
|:-------------------------------------------|:-----------------------------------|:---------------------------------------|:----------------------------------------------------------------------------|
| /live/clip_view/get/grid_quantization       | track_id, clip_id                  | track_id, clip_id, grid_quantization   | The clip's grid quantization value (RecordingQuantization enum)             |
| /live/clip_view/set/grid_quantization       | track_id, clip_id, grid_quantization |                                       | Set grid_quantization                                                       |
| /live/clip_view/get/grid_is_triplet         | track_id, clip_id                  | track_id, clip_id, grid_is_triplet     | Whether the clip is displayed with a triplet grid                           |
| /live/clip_view/set/grid_is_triplet         | track_id, clip_id, grid_is_triplet |                                       | Set grid_is_triplet                                                         |
| /live/clip_view/show_envelope               | track_id, clip_id                  |                                         | Show the Envelopes box in Clip View                                         |
| /live/clip_view/hide_envelope               | track_id, clip_id                  |                                         | Hide the Envelopes box                                                      |
| /live/clip_view/show_loop                   | track_id, clip_id                  |                                         | If the clip is visible in Detail View, scroll it to show the current loop   |

Notes:
- `grid_quantization`/`grid_is_triplet` have no `start_listen`/`stop_listen` support — Live does
  not expose listeners for these properties.
- `select_envelope_parameter(parameter)` is not yet supported: it needs a
  `(device_id, parameter_id)` address that doesn't fit this namespace's two-index protocol.

</details>

---

## Scene API

Represents a scene, used to trigger a row of clips simultaneously. A scene's name, color, tempo and time signature can all be set and queried.

<details>
<summary><b>Documentation</b>: Scene API</summary>

### Scene methods

| Address                         | Query params | Response params | Description             |
|:--------------------------------|:-------------|:----------------|:------------------------|
| /live/scene/fire                | scene_id     |                 | Trigger the given scene |
| /live/scene/fire_as_selected    | scene_id     |                 | Trigger the scene and select the next scene |
| /live/scene/fire_selected       |              |                 | Trigger the selected scene and select the next scene |

### Scene properties

 - Changes for any Scene property can be listened for by calling `/live/scene/start_listen/<property> <scene_index>`
 - Responses will be sent to `/live/scene/get/<property>`, with parameters `<scene_index> <property_value>`

#### Getters

| Address                      | Query params      | Response params            | Description                                       |
|:-----------------------------|:------------------|:---------------------------|:--------------------------------------------------|
| /live/scene/get/color        | scene_id          | scene_id, color            | Query scene color                      |
| /live/scene/get/color_index  | scene_id          | scene_id, color_index      | Query scene color index                |
| /live/scene/get/is_empty        | scene_id          | scene_id, is_empty            | Query whether scene is empty                      |
| /live/scene/get/is_triggered        | scene_id          | scene_id, is_triggered            | Query whether scene is in triggered state  |
| /live/scene/get/name         | scene_id          | scene_id, name             | Query scene name                      |
| /live/scene/get/tempo        | scene_id          | scene_id, tempo            | Query scene tempo |
| /live/scene/get/tempo_enabled       | scene_id          | scene_id, tempo_enabled            | Query whether scene tempo is enabled |
| /live/scene/get/time_signature_numerator        | scene_id          | scene_id, numerator            | Query scene time signature numerator  |
| /live/scene/get/time_signature_denominator        | scene_id          | scene_id, denominator            | Query scene time signature denominator |
| /live/scene/get/time_signature_enabled        | scene_id          | scene_id, enabled            | Query whether scene time signature is enabled |

#### Setters

| Address                                        | Query params             | Response params | Description                                  |
|:-----------------------------------------------|:-------------------------|:----------------|:---------------------------------------------|
| /live/scene/set/name                           | scene_id, name           |                 | Set scene name                               |
| /live/scene/set/color                          | scene_id, color          |                 | Set scene color                              |
| /live/scene/set/color_index                    | scene_id, color_index    |                 | Set scene color_index                        |
| /live/scene/set/tempo                          | scene_id, tempo          |                 | Set scene tempo                              |
| /live/scene/set/tempo_enabled                  | scene_id, tempo_enabled  |                 | Set whether scene tempo is enabled           |
| /live/scene/set/time_signature_numerator       | scene_id, numerator      |                 | Set scene time signature numerator           |
| /live/scene/set/time_signature_denominator     | scene_id, denominator    |                 | Set scene time signature denominator         |
| /live/scene/set/time_signature_enabled         | scene_id, enabled        |                 | Set whether scene time signature is enabled  |


</details>

---
## SessionRing API

Represents the Live Session Ring — a movable viewport over tracks and scenes in the Session View.

<details>
<summary><b>Documentation</b>: SessionRing API</summary>

### SessionRing lifecycle

| Address                | Query params           | Response params | Description                                           |
|:-----------------------|:-----------------------|:----------------|:------------------------------------------------------|
| /live/session_ring/on  | num_tracks, num_scenes |                 | Enable the session ring with the given dimensions     |
| /live/session_ring/off |                        |                 | Disable the session ring and stop all listeners       |

### SessionRing movement

| Address                              | Query params       | Response params | Description                                                     |
|:-------------------------------------|:-------------------|:----------------|:----------------------------------------------------------------|
| /live/session_ring/move              | x_offset, y_offset |                 | Move the ring by a relative (track, scene) offset               |
| /live/session_ring/move_left         |                    |                 | Move the ring one track to the left                             |
| /live/session_ring/move_right        |                    |                 | Move the ring one track to the right                            |
| /live/session_ring/move_up           |                    |                 | Move the ring one scene up                                      |
| /live/session_ring/move_down         |                    |                 | Move the ring one scene down                                    |
| /live/session_ring/move_track_left   |                    |                 | Alias for move_left                                             |
| /live/session_ring/move_track_right  |                    |                 | Alias for move_right                                            |
| /live/session_ring/page_up           |                    |                 | Move the ring up by `page_size` scenes (clamped at start)       |
| /live/session_ring/page_down         |                    |                 | Move the ring down by `page_size` scenes (clamped at end)       |

All movement is clamped so the ring never moves outside the song's tracks and scenes.

### SessionRing position

| Address                          | Query params                  | Response params               | Description                                   |
|:---------------------------------|:------------------------------|:------------------------------|:----------------------------------------------|
| /live/session_ring/get/position  |                               | track_offset, scene_offset    | Get the current top-left position of the ring |
| /live/session_ring/set/position  | track_offset, scene_offset    |                               | Set the top-left position of the ring         |
| /live/session_ring/get/tracks    |                               | track_index, ...              | Get the indices of all tracks in the ring     |
| /live/session_ring/get/scenes    |                               | scene_index, ...              | Get the indices of all scenes in the ring     |
| /live/session_ring/get/page_size |                               | page_size                     | Get the page size used by page_up/page_down   |
| /live/session_ring/set/page_size | page_size                     |                               | Set the page size (default: 8)                |

### Follow selected cell

When follow mode is active, the ring automatically scrolls to keep the selected track and scene visible:

- If the new selection is already within the ring's bounds, the ring does not move.
- If the selected scene is outside the ring vertically, the ring's top edge aligns with the selected scene (clamped so the ring stays within the song).
- If the selected track is outside the ring horizontally, the ring's left edge aligns with the selected track (clamped similarly).

| Address                       | Query params | Response params | Description              |
|:------------------------------|:-------------|:----------------|:-------------------------|
| /live/session_ring/follow/on  |              |                 | Enable follow mode       |
| /live/session_ring/follow/off |              |                 | Disable follow mode      |

Follow mode persists across ring rebuilds (i.e. subsequent `/live/session_ring/on` calls with different dimensions).

### SessionRing listeners

Subscribe to position changes to receive push updates whenever the ring moves:

| Address                                    | Query params | Response params            | Description                                              |
|:-------------------------------------------|:-------------|:---------------------------|:---------------------------------------------------------|
| /live/session_ring/start_listen/position   |              |                            | Start listening; replies sent to `.../get/position`      |
| /live/session_ring/stop_listen/position    |              |                            | Stop listening for position changes                      |
| /live/session_ring/start_listen/tracks     |              |                            | Start listening; replies sent to `.../get/tracks`        |
| /live/session_ring/stop_listen/tracks      |              |                            | Stop listening for track offset changes                  |
| /live/session_ring/start_listen/scenes     |              |                            | Start listening; replies sent to `.../get/scenes`        |
| /live/session_ring/stop_listen/scenes      |              |                            | Stop listening for scene offset changes                  |

</details>

---

## Device API

Represents an instrument or effect.

<details>
<summary><b>Documentation</b>: Device API</summary>

### Device properties

- Changes for any Parameter property can be listened for by calling `/live/device/start_listen/parameter/value <track_index> <device index> <parameter_index>`

| Address                                  | Query params                             | Response params                          | Description                                                                             |
|:-----------------------------------------|:-----------------------------------------|:-----------------------------------------|:----------------------------------------------------------------------------------------|
| /live/device/get/name                    | track_id, device_id                      | track_id, device_id, name                | Get device name                                                                         |
| /live/device/get/class_name              | track_id, device_id                      | track_id, device_id, class_name          | Get device class_name                                                                   |
| /live/device/get/type                    | track_id, device_id                      | track_id, device_id, type                | Get device type                                                                         |
| /live/device/get/is_active               | track_id, device_id                      | track_id, device_id, is_active           | Get device enabled state (1 = enabled, 0 = bypassed); read-only                        |
| /live/device/start_listen/is_active      | track_id, device_id                      |                                          | Subscribe to device enabled state changes                                               |
| /live/device/stop_listen/is_active       | track_id, device_id                      |                                          | Unsubscribe from device enabled state changes                                           |
| /live/device/get/num_parameters          | track_id, device_id                      | track_id, device_id, num_parameters      | Get the number of parameters exposed by the device                                      |
| /live/device/get/parameters/name         | track_id, device_id                      | track_id, device_id, [name, ...]         | Get the list of parameter names exposed by the device                                   |
| /live/device/get/parameters/value        | track_id, device_id                      | track_id, device_id, [value, ...]        | Get the device parameter values                                                         |
| /live/device/get/parameters/min          | track_id, device_id                      | track_id, device_id, [value, ...]        | Get the device parameter minimum values                                                 |
| /live/device/get/parameters/max          | track_id, device_id                      | track_id, device_id, [value, ...]        | Get the device parameter maximum values                                                 |
| /live/device/get/parameters/is_quantized | track_id, device_id                      | track_id, device_id, [value, ...]        | Get the list of is_quantized settings (i.e., whether the parameter must be an int/bool) |
| /live/device/set/parameters/value        | track_id, device_id, value, value ...    |                                          | Set the device parameter values                                                         |
| /live/device/get/parameter/value         | track_id, device_id, parameter_id        | track_id, device_id, parameter_id, value | Get a device parameter value                                                            |
| /live/device/get/parameter/value_string  | track_id, device_id, parameter_id        | track_id, device_id, parameter_id, value | Get the device parameter value as a readable string ex: 2500 Hz                         |
| /live/device/set/parameter/value         | track_id, device_id, parameter_id, value |                                          | Set a device parameter value                                                            |

For devices:

- `name` is the human-readable name
- `type` is 1 = audio_effect, 2 = instrument, 4 = midi_effect
- `class_name` is the Live instrument/effect name, e.g. Operator, Reverb. For external plugins and racks, can be
  AuPluginDevice, PluginDevice, InstrumentGroupDevice...

</details>


---

## Device View API

Represents Live's `Device.View` class, indexed by `(track_id, device_id)` — same addressing
as [Device API](#device-api).

<details>
<summary><b>Documentation</b>: Device View API</summary>

| Address                                | Query params              | Response params               | Description                                              |
|:------------------------------------------|:-----------------------------|:----------------------------------|:--------------------------------------------------------------|
| /live/device_view/get/is_collapsed          | track_id, device_id           | track_id, device_id, is_collapsed | Whether the device is shown collapsed in the device chain     |
| /live/device_view/set/is_collapsed          | track_id, device_id, is_collapsed |                                | Set is_collapsed                                               |
| /live/device_view/start_listen/is_collapsed | track_id, device_id           | track_id, device_id, is_collapsed | Start listening; replies sent to `.../get/is_collapsed`       |
| /live/device_view/stop_listen/is_collapsed  | track_id, device_id           |                                    | Stop listening                                                 |

</details>

---

## MidiMap API

Can be used to create assignments between MIDI CC and Live parameters.

<details>
<summary><b>Documentation</b>: MidiMap API</summary>

### MidiMap methods

| Address                | Query params | Response params | Description             |
|:-----------------------|:-------------|:----------------|:------------------------|
| /live/midimap/map_cc   | track_id, device_id, param_id, channel, cc     |  | Create an assignment such that control change `cc` on channel `channel` will control the specified parameter. |

Note that, for consistency with other object types (and Live's internal API), **channels are indexed from zero** - so MIDI channel 1 should be queried with index `0`, etc.

</details>

---

# Utilities

Included with the framework is a command-line console utility `run-console.py`, which can be used as a quick and easy way to send OSC queries to AbletonOSC. Example:

```
(1653)(AbletonOSC)$ ./run-console.py
AbletonOSC command console
Usage: /live/osc/command [params]
>>> /live/song/set/tempo 123.0
>>> /live/song/get/tempo
(123.0,)
>>> /live/song/get/track_names
('1-MIDI', '2-MIDI', '3-Audio', '4-Audio')
```

# Acknowledgements

Thanks to [Stu Fisher](https://github.com/stufisher/) (and other authors) for [LiveOSC](https://livecontrol.q3f.org/ableton-liveapi/liveosc/), the spiritual predecessor to this
library. Thanks to [Julien Bayle](https://structure-void.com/ableton-live-midi-remote-scripts/#liveAPI)
and [NSUSpray](https://nsuspray.github.io/Live_API_Doc/) for providing XML API docs, based on original work
by [Hanz Petrov](http://remotescripts.blogspot.com/p/support-files.html).

For code contributions and feedback, many thanks to:
- Jörn Lengwenings ([Coupe70](https://github.com/Coupe70))
- Bill Moser ([billmoser](https://github.com/billmoser))
- [stevmills](https://github.com/stevmills)
- Marco Buongiorno Nardelli ([marcobn](https://github.com/marcobn)) and Colin Stokes
- Mark Marijnissen ([markmarijnissen](https://github.com/markmarijnissen))
- [capturcus](https://github.com/capturcus)
- Esa Ruoho a.k.a. Lackluster ([esaruoho](https://github.com/esaruoho))

