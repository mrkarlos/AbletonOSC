# Changelog

Tracks fixes and features pulled into this fork's `develop` branch, including
those adapted from upstream `ideoforms/AbletonOSC` pull requests. See
`notes/pr-triage.md` for the full triage of upstream PRs this fork is
tracking.

## Unreleased

- Fixed `/live/song_view/set/detail_clip` throwing a `Boost.Python.ArgumentError` (logged
  as an ERROR + traceback on every call) when passed `(-1, -1)` to clear it — Live's
  `Song.View.detail_clip` setter doesn't accept `None`. There's no supported way to
  explicitly clear it; `(-1, -1)` is now a documented no-op (with a warning logged), and
  `detail_clip` only reverts to `(-1, -1)` as a side effect of the underlying clip being
  deleted.
- Added five new OSC namespaces exposing Live Object Model `.View` classes that were
  previously missing or only implicitly wrapped (the legacy `/live/view/*` namespace only
  ever wrapped `Song.View`'s selection state and is left untouched):
  - `/live/application_view/*` — `Application.View` (browse_mode, focused_document_view,
    show/hide/focus_view, scroll/zoom_view, toggle_browse, is_view_visible,
    available_main_views).
  - `/live/song_view/*` — the rest of `Song.View` not already covered by `/live/view/*`
    (draw_mode, follow_song, detail_clip, highlighted_clip_slot).
  - `/live/track_view/*` — `Track.View` (device_insert_mode, is_collapsed, selected_device,
    select_instrument), indexed by `track_id`.
  - `/live/clip_view/*` — `Clip.View` (grid_quantization, grid_is_triplet, show_envelope,
    hide_envelope, show_loop), indexed by `(track_id, clip_id)`.
    `select_envelope_parameter` intentionally omitted (see README).
  - `/live/device_view/*` — `Device.View` (is_collapsed), indexed by `(track_id, device_id)`.
- `AbletonOSCHandler._call_method` now captures and returns a method's return value (if
  any), normalized the same way listener callbacks already are — needed for the new
  `is_view_visible`/`select_instrument`/`available_main_views` methods above, which reply
  with a bool/list. Existing callers (whose target methods return `None`) are unaffected.
- Fixed `send()` swallowing benign `ConnectionResetError` (WSAECONNRESET) as
  an error-level log instead of the benign warning already used for the same
  condition on the receive path. Based on upstream PR #214.
- Added `/live/clip/get/groove`, returning the assigned groove's name (or an
  empty string) — `clip.groove` previously couldn't be queried at all because
  the raw `Live.Groove.Groove` object isn't OSC-serializable. Based on
  upstream PR #203.
