from typing import Tuple, Any, Optional
from .handler import AbletonOSCHandler

class TrackViewHandler(AbletonOSCHandler):
    """
    Wraps Live's Track.View class (track.view), indexed by track_index.
    """
    def __init__(self, manager):
        super().__init__(manager)
        self.class_identifier = "track_view"
        #--------------------------------------------------------------------------------
        # selected_device listeners are keyed by track_index; state lives here (rather
        # than in listener_functions/listener_objects) because the listener is attached
        # to track.view, not the track_view "handler target" itself. Same situation as
        # track.py's mixer listeners and view.py's selected_device listener.
        #--------------------------------------------------------------------------------
        self._selected_device_listener_state = {}

    def clear_api(self):
        for track_index in list(self._selected_device_listener_state.keys()):
            track, callback = self._selected_device_listener_state.pop(track_index)
            try:
                track.view.remove_selected_device_listener(callback)
            except Exception:
                pass
        super().clear_api()

    def init_api(self):
        def create_track_view_callback(func, *args, include_track_id: bool = False):
            def track_view_callback(params: Tuple[Any]):
                if params[0] == "*":
                    track_indices = list(range(len(self.song.tracks)))
                else:
                    track_indices = [int(params[0])]

                for track_index in track_indices:
                    track_view = self.song.tracks[track_index].view
                    try:
                        if include_track_id:
                            rv = func(track_view, *args, tuple([track_index] + list(params[1:])))
                        else:
                            rv = func(track_view, *args, tuple(params[1:]))
                    except RuntimeError as e:
                        self.logger.warning("AbletonOSC: track %d does not support this operation: %s" %
                                            (track_index, e))
                        continue

                    if rv is not None:
                        return (track_index, *rv)

            return track_view_callback

        properties_rw = [
            "device_insert_mode",
            "is_collapsed",
        ]

        for prop in properties_rw:
            self.osc_server.add_handler("/live/track_view/get/%s" % prop,
                                        create_track_view_callback(self._get_property, prop))
            self.osc_server.add_handler("/live/track_view/set/%s" % prop,
                                        create_track_view_callback(self._set_property, prop))
            self.osc_server.add_handler("/live/track_view/start_listen/%s" % prop,
                                        create_track_view_callback(self._start_listen, prop, include_track_id=True))
            self.osc_server.add_handler("/live/track_view/stop_listen/%s" % prop,
                                        create_track_view_callback(self._stop_listen, prop, include_track_id=True))

        #--------------------------------------------------------------------------------
        # select_instrument() -> bool. _call_method (see handler.py) now captures and
        # normalises the return value, so this goes through the generic path.
        #--------------------------------------------------------------------------------
        self.osc_server.add_handler("/live/track_view/select_instrument",
                                    create_track_view_callback(self._call_method, "select_instrument"))

        #--------------------------------------------------------------------------------
        # selected_device: a Device, R, observable. -1 is the "no device selected"
        # sentinel, matching view.py's existing convention. Simpler than view.py's
        # version: this is scoped to one fixed track_index per call, so it's a direct
        # listener on that track's .view, no re-attachment across tracks needed.
        #--------------------------------------------------------------------------------
        def get_selected_device(track_index: int) -> Tuple[int]:
            track = self.song.tracks[track_index]
            device = track.view.selected_device
            if device is None:
                return (-1,)
            return (list(track.devices).index(device),)

        def track_view_get_selected_device(params: Tuple[Any]):
            track_index = int(params[0])
            return (track_index, *get_selected_device(track_index))

        def start_listen_selected_device(params: Tuple[Any]):
            track_index = int(params[0])
            stop_listen_selected_device((track_index,))
            track = self.song.tracks[track_index]

            def callback():
                value = get_selected_device(track_index)
                self.logger.info("Property selected_device changed of track_view %d: %s" % (track_index, value))
                self.osc_server.send("/live/track_view/get/selected_device", (track_index, *value))

            track.view.add_selected_device_listener(callback)
            self._selected_device_listener_state[track_index] = (track, callback)
            callback()

        def stop_listen_selected_device(params: Tuple[Any]):
            track_index = int(params[0])
            state = self._selected_device_listener_state.pop(track_index, None)
            if state is not None:
                track, callback = state
                try:
                    track.view.remove_selected_device_listener(callback)
                except Exception:
                    pass

        self.osc_server.add_handler("/live/track_view/get/selected_device", track_view_get_selected_device)
        self.osc_server.add_handler("/live/track_view/start_listen/selected_device", start_listen_selected_device)
        self.osc_server.add_handler("/live/track_view/stop_listen/selected_device", stop_listen_selected_device)
