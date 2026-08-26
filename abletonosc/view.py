from functools import partial
from typing import Optional, Tuple, Any
from .handler import AbletonOSCHandler

class ViewHandler(AbletonOSCHandler):
    def __init__(self, manager):
        super().__init__(manager)
        self.class_identifier = "view"
        #--------------------------------------------------------------------------------
        # selected_clip and selected_device don't map onto a single Live property with
        # its own add_<prop>_listener, so they can't go through the generic
        # _start_listen/_stop_listen in handler.py. State for their bespoke listeners
        # lives here instead (same situation as track.py's mixer volume/panning
        # listeners, which also bypass the generic helper).
        #--------------------------------------------------------------------------------
        self._selected_clip_listener_cb = None
        self._selected_device_listener_state = None

    def init_api(self):
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
                #--------------------------------------------------------------------------------
                # No device selected (e.g. an empty chain) -- -1 mirrors the negative-sentinel
                # convention used elsewhere for "nothing" (e.g. track.py's fired_slot_index/
                # playing_slot_index), rather than raising ValueError from list.index(None).
                #--------------------------------------------------------------------------------
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
            device = self.song.tracks[params[0]].devices[params[1]]
            self.song.view.select_device(device)
            return params[0], params[1]

        self.osc_server.add_handler("/live/view/get/selected_scene", get_selected_scene)
        self.osc_server.add_handler("/live/view/get/selected_track", get_selected_track)
        self.osc_server.add_handler("/live/view/get/selected_clip", get_selected_clip)
        self.osc_server.add_handler("/live/view/get/selected_device", get_selected_device)
        self.osc_server.add_handler("/live/view/set/selected_scene", set_selected_scene)
        self.osc_server.add_handler("/live/view/set/selected_track", set_selected_track)
        self.osc_server.add_handler("/live/view/set/selected_clip", set_selected_clip)
        self.osc_server.add_handler("/live/view/set/selected_device", set_selected_device)

        self.osc_server.add_handler('/live/view/start_listen/selected_scene', partial(self._start_listen, self.song.view, "selected_scene", getter=get_selected_scene))
        self.osc_server.add_handler('/live/view/start_listen/selected_track', partial(self._start_listen, self.song.view, "selected_track", getter=get_selected_track))
        self.osc_server.add_handler('/live/view/stop_listen/selected_scene', partial(self._stop_listen, self.song.view, "selected_scene"))
        self.osc_server.add_handler('/live/view/stop_listen/selected_track', partial(self._stop_listen, self.song.view, "selected_track"))

        #--------------------------------------------------------------------------------
        # selected_clip: not a real Live property -- it's derived from selected_track and
        # selected_scene together, so observing it means firing on either underlying change.
        #--------------------------------------------------------------------------------
        def start_listen_selected_clip(params: Optional[Tuple] = ()):
            stop_listen_selected_clip()

            def callback():
                value = get_selected_clip()
                self.logger.info("Property selected_clip changed of view: %s" % str(value))
                self.osc_server.send("/live/view/get/selected_clip", value)

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

        self.osc_server.add_handler('/live/view/start_listen/selected_clip', start_listen_selected_clip)
        self.osc_server.add_handler('/live/view/stop_listen/selected_clip', stop_listen_selected_clip)

        #--------------------------------------------------------------------------------
        # selected_device: a real, observable property (Track.View.selected_device), but
        # it lives on whichever track is currently selected, not on song.view itself. So
        # watching it means re-attaching the device listener to the newly selected track's
        # .view every time selected_track changes, in addition to listening for
        # selected_device changes on the current one.
        #--------------------------------------------------------------------------------
        def start_listen_selected_device(params: Optional[Tuple] = ()):
            stop_listen_selected_device()

            def push_value():
                value = get_selected_device()
                self.logger.info("Property selected_device changed of view: %s" % str(value))
                self.osc_server.send("/live/view/get/selected_device", value)

            def device_changed():
                push_value()

            def track_changed():
                #--------------------------------------------------------------------------------
                # Mutate the state dict in place (rather than reassigning
                # self._selected_device_listener_state) so this closure and stop_listen_
                # selected_device always agree on the current track/device_cb without
                # needing to re-read "track_cb" back out on every call.
                #--------------------------------------------------------------------------------
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

        self.osc_server.add_handler('/live/view/start_listen/selected_device', start_listen_selected_device)
        self.osc_server.add_handler('/live/view/stop_listen/selected_device', stop_listen_selected_device)

    def clear_api(self):
        #--------------------------------------------------------------------------------
        # selected_clip/selected_device listeners are managed outside listener_functions/
        # listener_objects (see init_api), so stop them explicitly before the base class's
        # _clear_listeners() runs over listener_functions -- same approach track.py uses
        # for its mixer (volume/panning) listeners.
        #--------------------------------------------------------------------------------
        if self._selected_clip_listener_cb is not None:
            self._stop_listen_selected_clip()
        if self._selected_device_listener_state is not None:
            self._stop_listen_selected_device()
        super().clear_api()
