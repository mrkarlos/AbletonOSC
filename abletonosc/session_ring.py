
from typing import Optional, Tuple, Any
from .handler import AbletonOSCHandler

class SessionRingHandler(AbletonOSCHandler):
    """Handles OSC-based control of the Session Ring in Ableton Live."""

    def __init__(self, manager):
        super().__init__(manager)
        self.class_identifier = "session_ring"

        self.tracks_listener_is_active = False
        self.scenes_listener_is_active = False
        self.position_listener_is_active = False

        self.logger.info("SessionRingHandler initialized but inactive. Use /live/session_ring/on to activate.")

    @property
    def session_ring(self):
        return getattr(self.manager, "session_ring", None)

    def init_api(self):
        """Registers OSC commands for controlling the Session Ring."""

        def turn_on(params: Optional[Tuple] = (4, 2)):
            num_tracks, num_scenes = params if params else (4, 2)

            total_tracks = len(self.song.tracks)
            total_scenes = len(self.song.scenes)

            num_tracks = max(0, min(num_tracks, total_tracks))
            num_scenes = max(0, min(num_scenes, total_scenes))

            self._stop_tracks_listener()
            self._stop_scenes_listener()
            self._stop_position_listener()

            self.manager.build_session_ring(num_tracks, num_scenes, is_enabled=True)

            self._start_tracks_listener()
            self._start_scenes_listener()
            self._start_position_listener()

            self.logger.info("Session ring turned on with size (%d x %d)" % (num_tracks, num_scenes))

        def turn_off(params: Optional[Tuple] = ()):
            if self.session_ring:
                self._stop_tracks_listener()
                self._stop_scenes_listener()
                self._stop_position_listener()
                self.session_ring.set_enabled(False)
                self.logger.info("Session ring turned off")
            else:
                self.logger.info("Cannot turn off, session_ring is None")

        def get_session_ring_position(params: Optional[Tuple] = ()):
            if self.session_ring:
                return (self.session_ring.track_offset, self.session_ring.scene_offset)
            else:
                self.logger.info("Cannot get position, session_ring is None")

        def set_session_ring_position(params: Tuple):
            if self.session_ring:
                track_offset, scene_offset = params
                self.session_ring.set_offsets(track_offset, scene_offset)
            else:
                self.logger.info("Cannot set position, session_ring is None")

        def move_session_ring(params: Tuple[int, int]):
            if self.session_ring:
                x_offset, y_offset = params
                new_track_offset = self.session_ring.track_offset + x_offset
                new_scene_offset = self.session_ring.scene_offset + y_offset

                max_tracks = max(0, len(self.song.tracks) - self.session_ring.num_tracks)
                max_scenes = max(0, len(self.song.scenes) - self.session_ring.num_scenes)

                new_track_offset = max(0, min(new_track_offset, max_tracks))
                new_scene_offset = max(0, min(new_scene_offset, max_scenes))

                self.session_ring.set_offsets(new_track_offset, new_scene_offset)
                self.logger.info("Session Ring moved to (%d, %d)" % (new_track_offset, new_scene_offset))
            else:
                self.logger.info("Cannot move, session_ring is None")

        def move_session_ring_left(params: Optional[Tuple] = ()):
            if self.session_ring:
                if self.session_ring.track_offset > 0:
                    move_session_ring((-1, 0))
                else:
                    self.logger.info("Session ring at leftmost boundary, cannot move left")
            else:
                self.logger.info("Cannot move left, session_ring is None")

        def move_session_ring_right(params: Optional[Tuple] = ()):
            if self.session_ring:
                max_tracks = len(self.song.tracks) - self.session_ring.num_tracks
                if self.session_ring.track_offset < max_tracks:
                    move_session_ring((1, 0))
                else:
                    self.logger.info("Session ring at rightmost boundary, cannot move right")
            else:
                self.logger.info("Cannot move right, session_ring is None")

        def move_session_ring_track_left(params: Optional[Tuple] = ()):
            if self.session_ring:
                if self.session_ring.track_offset > 0:
                    move_session_ring((-1, 0))
                else:
                    self.logger.info("Session ring track at leftmost boundary, cannot move left")
            else:
                self.logger.info("Cannot move track left, session_ring is None")

        def move_session_ring_track_right(params: Optional[Tuple] = ()):
            if self.session_ring:
                max_tracks = len(self.song.tracks) - self.session_ring.num_tracks
                if self.session_ring.track_offset < max_tracks:
                    move_session_ring((1, 0))
                else:
                    self.logger.info("Session ring track at rightmost boundary, cannot move right")
            else:
                self.logger.info("Cannot move track right, session_ring is None")

        def move_session_ring_up(params: Optional[Tuple] = ()):
            if self.session_ring:
                if self.session_ring.scene_offset > 0:
                    move_session_ring((0, -1))
                else:
                    self.logger.info("Session ring at top boundary, cannot move up")
            else:
                self.logger.info("Cannot move up, session_ring is None")

        def move_session_ring_down(params: Optional[Tuple] = ()):
            if self.session_ring:
                max_scenes = len(self.song.scenes) - self.session_ring.num_scenes
                if self.session_ring.scene_offset < max_scenes:
                    move_session_ring((0, 1))
                else:
                    self.logger.info("Session ring at bottom boundary, cannot move down")
            else:
                self.logger.info("Cannot move down, session_ring is None")

        def get_session_ring_tracks(params: Optional[Tuple] = ()):
            if self.session_ring:
                return tuple(range(self.session_ring.track_offset,
                                   self.session_ring.track_offset + self.session_ring.num_tracks))
            else:
                self.logger.info("Cannot get tracks, session_ring is None")

        def get_session_ring_scenes(params: Optional[Tuple] = ()):
            if self.session_ring:
                return tuple(range(self.session_ring.scene_offset,
                                   self.session_ring.scene_offset + self.session_ring.num_scenes))
            else:
                self.logger.info("Cannot get scenes, session_ring is None")

        self.osc_server.add_handler("/live/session_ring/on",               turn_on)
        self.osc_server.add_handler("/live/session_ring/off",              turn_off)
        self.osc_server.add_handler("/live/session_ring/move",             move_session_ring)
        self.osc_server.add_handler("/live/session_ring/move_left",        move_session_ring_left)
        self.osc_server.add_handler("/live/session_ring/move_right",       move_session_ring_right)
        self.osc_server.add_handler("/live/session_ring/move_up",          move_session_ring_up)
        self.osc_server.add_handler("/live/session_ring/move_down",        move_session_ring_down)
        self.osc_server.add_handler("/live/session_ring/move_track_left",  move_session_ring_track_left)
        self.osc_server.add_handler("/live/session_ring/move_track_right", move_session_ring_track_right)
        self.osc_server.add_handler("/live/session_ring/get/position",     get_session_ring_position)
        self.osc_server.add_handler("/live/session_ring/set/position",     set_session_ring_position)
        self.osc_server.add_handler("/live/session_ring/get/tracks",       get_session_ring_tracks)
        self.osc_server.add_handler("/live/session_ring/get/scenes",       get_session_ring_scenes)
        self.osc_server.add_handler("/live/session_ring/start_listen/tracks",   self._start_tracks_listener)
        self.osc_server.add_handler("/live/session_ring/stop_listen/tracks",    self._stop_tracks_listener)
        self.osc_server.add_handler("/live/session_ring/start_listen/scenes",   self._start_scenes_listener)
        self.osc_server.add_handler("/live/session_ring/stop_listen/scenes",    self._stop_scenes_listener)
        self.osc_server.add_handler("/live/session_ring/start_listen/position", self._start_position_listener)
        self.osc_server.add_handler("/live/session_ring/stop_listen/position",  self._stop_position_listener)

    def clear_api(self):
        self._stop_tracks_listener()
        self._stop_scenes_listener()
        self._stop_position_listener()
        super().clear_api()

    #--------------------------------------------------------------------------------
    # Listener management
    #--------------------------------------------------------------------------------

    def _start_tracks_listener(self, params: Tuple[Any] = ()):
        if self.session_ring:
            if not self.tracks_listener_is_active:
                self.session_ring.add_offset_listener(self.tracks_offset_changed)
                self.tracks_listener_is_active = True
                self.logger.info("Started session ring tracks listener")
        else:
            self.logger.info("Cannot start tracks listener, session_ring is None")

    def _stop_tracks_listener(self, params: Tuple[Any] = ()):
        if self.session_ring is None:
            return
        if self.tracks_listener_is_active:
            self.session_ring.remove_offset_listener(self.tracks_offset_changed)
            self.tracks_listener_is_active = False
            self.logger.info("Stopped session ring tracks listener")

    def _start_scenes_listener(self, params: Tuple[Any] = ()):
        if self.session_ring:
            if not self.scenes_listener_is_active:
                self.session_ring.add_offset_listener(self.scenes_offset_changed)
                self.scenes_listener_is_active = True
                self.logger.info("Started session ring scenes listener")
        else:
            self.logger.info("Cannot start scenes listener, session_ring is None")

    def _stop_scenes_listener(self, params: Tuple[Any] = ()):
        if self.session_ring is None:
            return
        if self.scenes_listener_is_active:
            self.session_ring.remove_offset_listener(self.scenes_offset_changed)
            self.scenes_listener_is_active = False
            self.logger.info("Stopped session ring scenes listener")

    def _start_position_listener(self, params: Tuple[Any] = ()):
        if self.session_ring:
            if not self.position_listener_is_active:
                self.session_ring.add_offset_listener(self.position_changed)
                self.position_listener_is_active = True
                self.logger.info("Started session ring position listener")
        else:
            self.logger.info("Cannot start position listener, session_ring is None")

    def _stop_position_listener(self, params: Tuple[Any] = ()):
        if self.session_ring is None:
            return
        if self.position_listener_is_active:
            self.session_ring.remove_offset_listener(self.position_changed)
            self.position_listener_is_active = False
            self.logger.info("Stopped session ring position listener")

    #--------------------------------------------------------------------------------
    # Offset change callbacks
    #--------------------------------------------------------------------------------

    def tracks_offset_changed(self, *args, **kwargs):
        if self.session_ring is None:
            self.logger.warning("Cannot process callback, session_ring is None")
            return
        track_indexes = tuple(range(self.session_ring.track_offset,
                                    self.session_ring.track_offset + self.session_ring.num_tracks))
        self.osc_server.send("/live/session_ring/get/tracks", track_indexes)
        self.logger.info("Session ring tracks updated: %s" % str(track_indexes))

    def scenes_offset_changed(self, *args, **kwargs):
        if self.session_ring is None:
            self.logger.warning("Cannot process callback, session_ring is None")
            return
        scene_indexes = tuple(range(self.session_ring.scene_offset,
                                    self.session_ring.scene_offset + self.session_ring.num_scenes))
        self.osc_server.send("/live/session_ring/get/scenes", scene_indexes)
        self.logger.info("Session ring scenes updated: %s" % str(scene_indexes))

    def position_changed(self, *args, **kwargs):
        if self.session_ring is None:
            self.logger.warning("Cannot process callback, session_ring is None")
            return
        position = (self.session_ring.track_offset, self.session_ring.scene_offset)
        self.osc_server.send("/live/session_ring/get/position", position)
        self.logger.info("Session ring position updated: %s" % str(position))
