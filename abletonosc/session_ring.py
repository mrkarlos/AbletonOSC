
from typing import Optional, Tuple, Any
# from ableton.v2.control_surface.components import SessionRingComponent
from .handler import AbletonOSCHandler

class SessionRingHandler(AbletonOSCHandler):
    """Handles OSC-based control of the Session Ring in Ableton Live."""

    def __init__(self, manager):
        super().__init__(manager)
        self.class_identifier = "session_ring"

        # Initialize the Session Ring
        # self.session_ring = None
        self.num_tracks = 4
        self.num_scenes = 2

        # Track listening state
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
            """Turns on the session ring, ensuring size constraints.

            Args:
                params (Optional[Tuple]): A tuple containing (num_tracks, num_scenes).
            """

            # Unpack parameters with default values

            num_tracks, num_scenes = params if params else (4, 2)
            # Ensure the session ring is not larger than the number of tracks/scenes in the song
            total_tracks = len(self.song.tracks)
            total_scenes = len(self.song.scenes)

            num_tracks = max(0, num_tracks)
            num_scenes = max(0, num_scenes)

            if num_tracks > total_tracks:
                num_tracks = total_tracks  # Limit to the available tracks
            if num_scenes > total_scenes:
                num_scenes = total_scenes  # Limit to the available scenes

            # Initialize the session ring with valid dimensions
            # self.session_ring = SessionRingComponent(num_tracks, num_scenes)
            self.num_tracks = num_tracks
            self.num_scenes = num_scenes

            # Stop listeners
            stop_tracks_listener()
            stop_scenes_listener()
            stop_position_listener()

            self.manager.build_session_ring(num_tracks, num_scenes, is_enabled=True)

            # Start listeners
            start_tracks_listener()
            start_scenes_listener()
            start_position_listener()

            self.logger.info(f"Session ring turned on with size ({num_tracks}x{num_scenes})")

        def turn_off(params: Optional[Tuple] = ()):
            """Turns off the session ring and stops listeners."""
            if self.session_ring:
                stop_tracks_listener()
                stop_scenes_listener()

                # Properly notify Ableton Live's API that the session ring is being destroyed
                self.session_ring.set_enabled(False)  # Disable it
                # self.session_ring = None  # Remove reference
                self.logger.info("Session ring turned off")
            else:
                self.logger.info("Cannot turn off, session_ring is None")

        def get_session_ring_position(params: Optional[Tuple] = ()):
            """Returns the current position of the session ring."""
            if self.session_ring:
                return (self.session_ring.track_offset, self.session_ring.scene_offset)
            else:
                self.logger.info("Cannot change position, session_ring is None")

        def set_session_ring_position(params: Tuple):
            """Sets the session ring's position to (track_offset, scene_offset)."""
            if self.session_ring:
                track_offset, scene_offset = params
                self.session_ring.set_offsets(track_offset, scene_offset)
            else:
                self.logger.info("Cannot change position, session_ring is None")

        def move_session_ring(params: Tuple[int, int]):
            """Move the session ring left/right (x_offset) and up/down (y_offset)."""
            if self.session_ring:
                x_offset, y_offset = params
                # Calculate new offsets
                new_track_offset = self.session_ring.track_offset + x_offset
                new_scene_offset = self.session_ring.scene_offset + y_offset

                # Ensure the new offsets stay within the allowed range
                max_tracks = max(0, len(self.song.tracks) - self.num_tracks)
                max_scenes = max(0, len(self.song.scenes) - self.num_scenes)

                new_track_offset = max(0, min(new_track_offset, max_tracks))
                new_scene_offset = max(0, min(new_scene_offset, max_scenes))

                # Apply the new offsets
                self.session_ring.set_offsets(new_track_offset, new_scene_offset)

                self.logger.info(f"Session Ring moved to ({new_track_offset}, {new_scene_offset})")
            else:
                self.logger.info("Cannot move xy, session_ring is None")

        def move_session_ring_left(params: Optional[Tuple] = ()):
            """Moves the session ring left by one track if within bounds."""
            if self.session_ring:
                if self.session_ring.track_offset > 0:
                    move_session_ring((-1, 0))
                    self.logger.info("Session ring moved left")
                else:
                    self.logger.info("Session ring at leftmost boundary, cannot move left")
            else:
                self.logger.info("Cannot move left, session_ring is None")

        def move_session_ring_right(params: Optional[Tuple] = ()):
            """Moves the session ring right by one track if within bounds."""
            if self.session_ring:
                max_tracks = len(self.song.tracks) - self.num_tracks  # Ensure the ring fits within the total tracks
                if self.session_ring.track_offset < max_tracks:
                    move_session_ring((1, 0))
                    # self.session_ring.move(1, 0)
                    self.logger.info("Session ring moved right")
                else:
                    self.logger.info("Session ring at rightmost boundary, cannot move right")
            else:
                self.logger.info("Cannot move right, session_ring is None")

        def move_session_ring_track_left(params: Optional[Tuple] = ()):
            """Moves the session track ring left by one track if within bounds."""
            if self.session_ring:
                if self.session_ring.track_offset > 0:
                    move_session_ring((-1, 0))
                    self.logger.info("Session ring track moved left")
                else:
                    self.logger.info("Session ring track at leftmost boundary, cannot move left")
            else:
                self.logger.info("Cannot move track left, session_ring is None")

        def move_session_ring_track_right(params: Optional[Tuple] = ()):
            """Moves the selected track within the session ring right by one track if within bounds."""
            if self.session_ring:
                max_tracks = len(self.song.tracks) - self.num_tracks  # Ensure the ring fits within the total tracks
                if self.session_ring.track_offset < max_tracks:
                    move_session_ring((1, 0))
                    # self.session_ring.move(1, 0)
                    self.logger.info("Session track ring moved right")
                else:
                    self.logger.info("Session ring track at rightmost boundary, cannot move right")
            else:
                self.logger.info("Cannot move track right, session_ring is None")

        def move_session_ring_up(params: Optional[Tuple] = ()):
            """Moves the session ring up by one scene if within bounds."""
            if self.session_ring:
                if self.session_ring.scene_offset > 0:
                    move_session_ring((0, -1))
                    self.logger.info("Session ring moved up")
                else:
                    self.logger.info("Session ring at top boundary, cannot move up")
            else:
                self.logger.info("Cannot move up, session_ring is None")

        def move_session_ring_down(params: Optional[Tuple] = ()):
            """Moves the session ring down by one scene if within bounds."""
            if self.session_ring:
                max_scenes = len(self.song.scenes) - self.num_scenes  # Ensure the ring fits within the total scenes
                if self.session_ring.scene_offset < max_scenes:
                    move_session_ring((0, 1))
                    self.logger.info("Session ring moved down")
                else:
                    self.logger.info("Session ring at bottom boundary, cannot move down")
            else:
                self.logger.info("Cannot move down, session_ring is None")

        def get_session_ring_tracks(params: Optional[Tuple] = ()):
            """Returns a tuple of track indexes inside the session ring."""
            if self.session_ring:
                track_indexes = tuple(range(self.session_ring.track_offset, self.session_ring.track_offset + self.num_tracks))
                return track_indexes
            else:
                self.logger.info("Cannot get tracks, session_ring is None")

        def get_session_ring_scenes(params: Optional[Tuple] = ()):
            """Returns a tuple of scene indexes inside the session ring."""
            if self.session_ring:
                scene_indexes = tuple(range(self.session_ring.scene_offset, self.session_ring.scene_offset + self.num_scenes))
                return scene_indexes
            else:
                self.logger.info("Cannot get scenes, session_ring is None")

        def start_tracks_listener(params: Tuple[Any] = ()):
            """Start listening for track offset changes."""
            if self.session_ring:
                if not self.tracks_listener_is_active:
                    self.session_ring.add_offset_listener(self.tracks_offset_changed)
                    self.tracks_listener_is_active = True
                    self.logger.info("Started session ring tracks listener")
            else:
                self.logger.info("Cannot start tracks listener, session_ring is None")

        def stop_tracks_listener(params: Tuple[Any] = ()):

            if self.session_ring is None:
                self.logger.info("Cannot stop tracks listener, session_ring is None")
                return

            """Stop listening for track offset changes."""
            if self.tracks_listener_is_active:
                self.session_ring.remove_offset_listener(self.tracks_offset_changed)
                self.tracks_listener_is_active = False
                self.logger.info("Stopped session ring tracks listener")
            else:
                self.logger.info("Cannot stop tracks listener, is is not active")

        def start_scenes_listener(params: Tuple[Any] = ()):
            """Start listening for scene offset changes."""
            if self.session_ring:
                if not self.scenes_listener_is_active:
                    self.session_ring.add_offset_listener(self.scenes_offset_changed)
                    self.scenes_listener_is_active = True
                    self.logger.info("Started session ring scenes listener")
            else:
                self.logger.info("Cannot start scenes listener, session_ring is None")

        def stop_scenes_listener(params: Tuple[Any] = ()):
            """Stop listening for scene offset changes."""
            if self.session_ring is None:
                self.logger.info("Cannot stop scenes listener, session_ring is None")
                return

            if self.scenes_listener_is_active:
                self.session_ring.remove_offset_listener(self.scenes_offset_changed)
                self.scenes_listener_is_active = False
                self.logger.info("Stopped session ring scenes listener")
            else:
                self.logger.info("Did not stop scene listener, is is not active")


        def start_position_listener(params: Tuple[Any] = ()):
            """Start listening for scene offset changes."""
            if self.session_ring:
                if not self.position_listener_is_active:
                    self.session_ring.add_offset_listener(self.position_changed)
                    self.position_listener_is_active = True
                    self.logger.info("Started session ring position listener")
            else:
                self.logger.info("Cannot start position listener, session_ring is None")

        def stop_position_listener(params: Tuple[Any] = ()):

            if self.session_ring is None:
                self.logger.info("Cannot stop position listener, session_ring is None")
                return

            """Stop listening for position changes."""
            if self.position_listener_is_active:
                self.session_ring.remove_offset_listener(self.position_changed)
                self.position_listener_is_active = False
                self.logger.info("Stopped session ring position listener")
            else:
                self.logger.info("Cannot stop position listener, is is not active")

        # Register OSC Handlers
        self.osc_server.add_handler("/live/session_ring/on", turn_on)
        self.osc_server.add_handler("/live/session_ring/off", turn_off)
        self.osc_server.add_handler("/live/session_ring/move", move_session_ring)
        self.osc_server.add_handler("/live/session_ring/move_left", move_session_ring_left)
        self.osc_server.add_handler("/live/session_ring/move_right", move_session_ring_right)
        self.osc_server.add_handler("/live/session_ring/move_up", move_session_ring_up)
        self.osc_server.add_handler("/live/session_ring/move_down", move_session_ring_down)
        self.osc_server.add_handler("/live/session_ring/move_track_left", move_session_ring_track_left)
        self.osc_server.add_handler("/live/session_ring/move_track_right", move_session_ring_track_right)
        self.osc_server.add_handler("/live/session_ring/get/position", get_session_ring_position)
        self.osc_server.add_handler("/live/session_ring/set/position", set_session_ring_position)
        self.osc_server.add_handler("/live/session_ring/get/tracks", get_session_ring_tracks)
        self.osc_server.add_handler("/live/session_ring/get/scenes", get_session_ring_scenes)
        self.osc_server.add_handler("/live/session_ring/start_listen/tracks", start_tracks_listener)
        self.osc_server.add_handler("/live/session_ring/stop_listen/tracks", stop_tracks_listener)
        self.osc_server.add_handler("/live/session_ring/start_listen/position", start_position_listener)
        self.osc_server.add_handler("/live/session_ring/stop_listen/position", stop_position_listener)
        self.osc_server.add_handler("/live/session_ring/start_listen/scenes", start_scenes_listener)
        self.osc_server.add_handler("/live/session_ring/stop_listen/scenes", stop_scenes_listener)

    def tracks_offset_changed(self, *args, **kwargs):
        if self.session_ring is None:
            self.warning.info("Cannot process callback, session_ring is None")
            return

        """Callback function triggered when the session ring's track offset changes."""
        track_indexes = tuple(range(self.session_ring.track_offset, self.session_ring.track_offset + self.num_tracks))
        self.osc_server.send("/live/session_ring/get/tracks", track_indexes) # Send the Tuple
        self.logger.info(f"Session ring tracks updated: {track_indexes}")

    def scenes_offset_changed(self, *args, **kwargs):
        if self.session_ring is None:
            self.warning.info("Cannot process callback, session_ring is None")
            return

        """Callback function triggered when the session ring's scene offset changes."""
        scene_indexes = tuple(range(self.session_ring.scene_offset, self.session_ring.scene_offset + self.num_scenes))
        self.osc_server.send("/live/session_ring/get/scenes", scene_indexes) # Send the Tuple
        self.logger.info(f"Session ring scenes updated: {scene_indexes}")

    def position_changed(self, *args, **kwargs):
        if self.session_ring is None:
            self.warning.info("Cannot process callback, session_ring is None")
            return

        """Callback function triggered when the session ring's position changes."""
        position_indexes = (self.session_ring.track_offset, self.session_ring.scene_offset)
        self.osc_server.send("/live/session_ring/get/position", position_indexes) # Send the Tuple
        self.logger.info(f"Session ring position updated: {position_indexes}")