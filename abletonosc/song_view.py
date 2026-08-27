from functools import partial
from typing import Optional, Tuple, Any
from .handler import AbletonOSCHandler

class SongViewHandler(AbletonOSCHandler):
    """
    Wraps the full public surface of Live's Song.View class (self.song.view) --
    draw_mode, follow_song, detail_clip, highlighted_clip_slot, selected_scene,
    selected_track, selected_device, and the derived selected_clip convenience.

    /live/view/* (view.py) already exposes selected_scene/selected_track/selected_clip/
    selected_device, and is left untouched for backward compatibility -- but everything
    it offers is deliberately duplicated here too (as an independent implementation, not
    a delegation), so /live/song_view/* is a strict superset of Song.View. That means it
    can absorb /live/view/*'s users without a breaking change if /live/view/* is ever
    deprecated.

    selected_chain and selected_parameter are the only Song.View members NOT covered --
    both need a chain/parameter addressing scheme this codebase doesn't have yet (the
    same reason clip_view.py omits select_envelope_parameter). Deliberately deferred,
    not an oversight.
    """
    def __init__(self, manager):
        super().__init__(manager)
        self.class_identifier = "song_view"
        #--------------------------------------------------------------------------------
        # selected_clip and selected_device don't map onto a single Live property with its
        # own add_<prop>_listener, so their listeners are managed by hand here, same
        # situation as view.py's identical selected_clip/selected_device handling (this is
        # an independent implementation, not a shared one -- Live is happy to have
        # multiple distinct listener callbacks registered on the same object).
        #--------------------------------------------------------------------------------
        self._selected_clip_listener_cb = None
        self._selected_device_listener_state = None

    def clear_api(self):
        #--------------------------------------------------------------------------------
        # selected_clip/selected_device listeners are managed outside listener_functions/
        # listener_objects (see init_api), so stop them explicitly before the base class's
        # _clear_listeners() runs over listener_functions -- same approach view.py uses.
        #--------------------------------------------------------------------------------
        if self._selected_clip_listener_cb is not None:
            self._stop_listen_selected_clip()
        if self._selected_device_listener_state is not None:
            self._stop_listen_selected_device()
        super().clear_api()

    def init_api(self):
        target = self.song.view

        properties_rw = [
            "draw_mode",
            "follow_song",
        ]

        for prop in properties_rw:
            self.osc_server.add_handler("/live/song_view/get/%s" % prop,
                                        partial(self._get_property, target, prop))
            self.osc_server.add_handler("/live/song_view/set/%s" % prop,
                                        partial(self._set_property, target, prop))
            self.osc_server.add_handler("/live/song_view/start_listen/%s" % prop,
                                        partial(self._start_listen, target, prop))
            self.osc_server.add_handler("/live/song_view/stop_listen/%s" % prop,
                                        partial(self._stop_listen, target, prop))

        #--------------------------------------------------------------------------------
        # detail_clip: a Clip, R/W, observable. Clip objects have no back-reference to
        # their own track/slot index (same limitation clip.py has), so resolve by
        # identity-scanning clip_slots. (-1, -1) is the "no clip" sentinel, mirroring
        # view.py's -1 convention for selected_device, extended to a pair since a Clip
        # needs two indices.
        #
        # Known gap: detail_clip can point to an Arrangement-view clip, which has no
        # (track_index, clip_slot_index) address in AbletonOSC at all -- that case is
        # indistinguishable from "no clip" here.
        #--------------------------------------------------------------------------------
        def get_detail_clip(params: Optional[Tuple] = ()):
            clip = self.song.view.detail_clip
            if clip is not None:
                #--------------------------------------------------------------------------------
                # Live's Python bindings hand back a fresh wrapper object on each attribute
                # access, so `is` identity comparison never matches even for the same
                # underlying clip -- use == instead, matching the codebase's existing
                # convention for this exact situation (e.g. view.py's get_selected_track/
                # get_selected_scene, via list.index()).
                #--------------------------------------------------------------------------------
                for track_index, track in enumerate(self.song.tracks):
                    for clip_index, clip_slot in enumerate(track.clip_slots):
                        if clip_slot.clip == clip:
                            return (track_index, clip_index)
            return (-1, -1)

        def set_detail_clip(params: Tuple[Any]):
            track_index, clip_index = int(params[0]), int(params[1])
            if track_index < 0 or clip_index < 0:
                #--------------------------------------------------------------------------------
                # Live's Song.View.detail_clip setter doesn't accept None -- it raises
                # Boost.Python.ArgumentError, requiring a genuine Clip handle. There's no
                # supported way to explicitly clear detail_clip via this property; it only
                # reverts to "no clip" as a side effect of the underlying clip being deleted.
                # So (-1, -1) as input is a documented no-op, not an actual clear.
                #--------------------------------------------------------------------------------
                self.logger.warning("detail_clip cannot be explicitly cleared (Live's API doesn't "
                                    "support it) -- ignoring")
                return
            self.song.view.detail_clip = self.song.tracks[track_index].clip_slots[clip_index].clip

        self.osc_server.add_handler("/live/song_view/get/detail_clip", get_detail_clip)
        self.osc_server.add_handler("/live/song_view/set/detail_clip", set_detail_clip)
        self.osc_server.add_handler("/live/song_view/start_listen/detail_clip",
                                    partial(self._start_listen, target, "detail_clip", getter=get_detail_clip))
        self.osc_server.add_handler("/live/song_view/stop_listen/detail_clip",
                                    partial(self._stop_listen, target, "detail_clip"))

        #--------------------------------------------------------------------------------
        # highlighted_clip_slot: a ClipSlot, R/W, NOT observable (per LOM doc) -- get/set
        # only, no start_listen/stop_listen handlers. This is a deliberate omission, not
        # an oversight.
        #--------------------------------------------------------------------------------
        def get_highlighted_clip_slot(params: Optional[Tuple] = ()):
            slot = self.song.view.highlighted_clip_slot
            if slot is not None:
                for track_index, track in enumerate(self.song.tracks):
                    for clip_index, clip_slot in enumerate(track.clip_slots):
                        if clip_slot == slot:
                            return (track_index, clip_index)
            return (-1, -1)

        def set_highlighted_clip_slot(params: Tuple[Any]):
            track_index, clip_index = int(params[0]), int(params[1])
            self.song.view.highlighted_clip_slot = self.song.tracks[track_index].clip_slots[clip_index]

        self.osc_server.add_handler("/live/song_view/get/highlighted_clip_slot", get_highlighted_clip_slot)
        self.osc_server.add_handler("/live/song_view/set/highlighted_clip_slot", set_highlighted_clip_slot)

        #--------------------------------------------------------------------------------
        # selected_scene, selected_track, selected_clip (derived), selected_device: full
        # parity with /live/view/*'s equivalents (view.py), reimplemented independently
        # here rather than delegated to, so this handler is a self-contained Song.View
        # surface. Comments trimmed relative to view.py's originals where the reasoning is
        # identical; see view.py for the fuller rationale on each pattern.
        #--------------------------------------------------------------------------------
        def get_selected_scene(params: Optional[Tuple] = ()):
            return (list(self.song.scenes).index(self.song.view.selected_scene),)

        def get_selected_track(params: Optional[Tuple] = ()):
            return (list(self.song.tracks).index(self.song.view.selected_track),)

        def get_selected_clip(params: Optional[Tuple] = ()):
            return (get_selected_track()[0], get_selected_scene()[0])

        def get_selected_device(params: Optional[Tuple] = ()):
            track = self.song.view.selected_track
            device = track.view.selected_device
            if device is None:
                return (get_selected_track()[0], -1)
            return (get_selected_track()[0], list(track.devices).index(device))

        def set_selected_scene(params: Optional[Tuple] = ()):
            self.song.view.selected_scene = self.song.scenes[params[0]]

        def set_selected_track(params: Optional[Tuple] = ()):
            self.song.view.selected_track = self.song.tracks[params[0]]

        def set_selected_clip(params: Optional[Tuple] = ()):
            set_selected_track((params[0],))
            set_selected_scene((params[1],))

        def set_selected_device(params: Optional[Tuple] = ()):
            #--------------------------------------------------------------------------------
            # Song.View.select_device(device) is Song.View's actual method for this --
            # exposed here as a property-style setter to match /live/view/*'s existing
            # convention, rather than as a separate "select_device" method endpoint that
            # would just duplicate the same functionality under a different name.
            #--------------------------------------------------------------------------------
            device = self.song.tracks[params[0]].devices[params[1]]
            self.song.view.select_device(device)
            return params[0], params[1]

        self.osc_server.add_handler("/live/song_view/get/selected_scene", get_selected_scene)
        self.osc_server.add_handler("/live/song_view/get/selected_track", get_selected_track)
        self.osc_server.add_handler("/live/song_view/get/selected_clip", get_selected_clip)
        self.osc_server.add_handler("/live/song_view/get/selected_device", get_selected_device)
        self.osc_server.add_handler("/live/song_view/set/selected_scene", set_selected_scene)
        self.osc_server.add_handler("/live/song_view/set/selected_track", set_selected_track)
        self.osc_server.add_handler("/live/song_view/set/selected_clip", set_selected_clip)
        self.osc_server.add_handler("/live/song_view/set/selected_device", set_selected_device)

        self.osc_server.add_handler('/live/song_view/start_listen/selected_scene',
                                    partial(self._start_listen, self.song.view, "selected_scene", getter=get_selected_scene))
        self.osc_server.add_handler('/live/song_view/start_listen/selected_track',
                                    partial(self._start_listen, self.song.view, "selected_track", getter=get_selected_track))
        self.osc_server.add_handler('/live/song_view/stop_listen/selected_scene',
                                    partial(self._stop_listen, self.song.view, "selected_scene"))
        self.osc_server.add_handler('/live/song_view/stop_listen/selected_track',
                                    partial(self._stop_listen, self.song.view, "selected_track"))

        #--------------------------------------------------------------------------------
        # selected_clip: not a real Live property -- derived from selected_track and
        # selected_scene together, so observing it means firing on either underlying
        # change.
        #--------------------------------------------------------------------------------
        def start_listen_selected_clip(params: Optional[Tuple] = ()):
            stop_listen_selected_clip()

            def callback():
                value = get_selected_clip()
                self.logger.info("Property selected_clip changed of song_view: %s" % str(value))
                self.osc_server.send("/live/song_view/get/selected_clip", value)

            self.song.view.add_selected_track_listener(callback)
            self.song.view.add_selected_scene_listener(callback)
            self._selected_clip_listener_cb = callback
            callback()

        def stop_listen_selected_clip(params: Optional[Tuple] = ()):
            callback = self._selected_clip_listener_cb
            if callback is not None:
                try:
                    self.song.view.remove_selected_track_listener(callback)
                except Exception:
                    pass
                try:
                    self.song.view.remove_selected_scene_listener(callback)
                except Exception:
                    pass
                self._selected_clip_listener_cb = None

        self._stop_listen_selected_clip = stop_listen_selected_clip

        self.osc_server.add_handler('/live/song_view/start_listen/selected_clip', start_listen_selected_clip)
        self.osc_server.add_handler('/live/song_view/stop_listen/selected_clip', stop_listen_selected_clip)

        #--------------------------------------------------------------------------------
        # selected_device: lives on whichever track is currently selected, not on
        # song.view itself -- watching it means re-attaching the device listener to the
        # newly selected track's .view every time selected_track changes, in addition to
        # listening for selected_device changes on the current one.
        #--------------------------------------------------------------------------------
        def start_listen_selected_device(params: Optional[Tuple] = ()):
            stop_listen_selected_device()

            def push_value():
                value = get_selected_device()
                self.logger.info("Property selected_device changed of song_view: %s" % str(value))
                self.osc_server.send("/live/song_view/get/selected_device", value)

            def device_changed():
                push_value()

            def track_changed():
                state = self._selected_device_listener_state
                if state["track"] is not None:
                    try:
                        state["track"].view.remove_selected_device_listener(state["device_cb"])
                    except Exception:
                        pass
                new_track = self.song.view.selected_track
                new_track.view.add_selected_device_listener(device_changed)
                state["track"] = new_track
                state["device_cb"] = device_changed
                push_value()

            self._selected_device_listener_state = {"track": None, "device_cb": None, "track_cb": track_changed}
            self.song.view.add_selected_track_listener(track_changed)
            track_changed()

        def stop_listen_selected_device(params: Optional[Tuple] = ()):
            state = self._selected_device_listener_state
            if state is not None:
                if state["track_cb"] is not None:
                    try:
                        self.song.view.remove_selected_track_listener(state["track_cb"])
                    except Exception:
                        pass
                if state["track"] is not None and state["device_cb"] is not None:
                    try:
                        state["track"].view.remove_selected_device_listener(state["device_cb"])
                    except Exception:
                        pass
                self._selected_device_listener_state = None

        self._stop_listen_selected_device = stop_listen_selected_device

        self.osc_server.add_handler('/live/song_view/start_listen/selected_device', start_listen_selected_device)
        self.osc_server.add_handler('/live/song_view/stop_listen/selected_device', stop_listen_selected_device)
