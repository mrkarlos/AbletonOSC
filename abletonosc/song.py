import os
import sys
import tempfile
import Live
import json
from functools import partial
from typing import Tuple, Any

from .handler import AbletonOSCHandler

#--------------------------------------------------------------------------------
# The "obj" prefixes a track_data dotted property (e.g. "track.name") can use, each
# handled by its own sibling handler instance's start_listen/stop_listen machinery.
#
# Sibling handlers are deliberately looked up by class_identifier string (see
# _track_data_get_sibling_handler below), not by importing TrackHandler/ClipHandler/
# etc. and matching with isinstance(). manager.py's reload_imports() reloads track.py
# strictly after song.py, so a class imported here at module level would go stale the
# moment /live/api/reload runs: isinstance() would compare a freshly-constructed
# TrackHandler instance (built from the just-reloaded class) against song.py's
# now-outdated reference to the pre-reload class, and never match.
#--------------------------------------------------------------------------------
_TRACK_DATA_OBJECT_TYPES = ("track", "clip", "clip_slot", "device")

#--------------------------------------------------------------------------------
# clip.* properties with no native Live listener (add_<prop>_listener doesn't exist),
# confirmed against the LOM reference. get/track_data can still read these; listening
# for changes cannot work, so _track_data_resolve skips them up front rather than
# attempting and failing on every clip creation -- mirroring the track.num_devices
# special case below.
#--------------------------------------------------------------------------------
_TRACK_DATA_CLIP_PROPERTIES_WITHOUT_LISTENER = (
    "length",
    "is_audio_clip",
    "is_midi_clip",
    "is_triggered",
    "will_record_on_start",
    "has_groove",
    "file_path",
    "gain_display_string",
    "sample_length",
)

class SongHandler(AbletonOSCHandler):
    def __init__(self, manager):
        super().__init__(manager)
        self.class_identifier = "song"

        #--------------------------------------------------------------------------------
        # State for start_listen/stop_listen on track_data (see init_api() below).
        # _track_data_active is the only state that can't be recovered from the sibling
        # handlers' own listener_functions/listener_objects dicts: it's what lets a
        # brand-new clip in a previously-empty slot pick up its requested properties
        # automatically (see _track_data_sync_has_clip_listeners).
        #--------------------------------------------------------------------------------
        self._track_data_active = set()                 # {(track_index, "obj.prop"), ...}
        self._track_data_has_clip_listeners = {}         # {clip_slot: callback}
        self._track_data_auto_rebuild = True
        self._track_data_structural_listeners_installed = False
        self._track_data_sibling_handler_cache = {}

    def init_api(self):
        #--------------------------------------------------------------------------------
        # Callbacks for Song: methods
        #--------------------------------------------------------------------------------
        for method in [
            "capture_and_insert_scene",
            "capture_midi",
            "continue_playing",
            "create_audio_track",
            "create_midi_track",
            "create_return_track",
            "create_scene",
            "delete_return_track",
            "delete_scene",
            "delete_track",
            "duplicate_scene",
            "duplicate_track",
            "force_link_beat_time",
            "jump_by",
            "jump_to_prev_cue",
            "jump_to_next_cue",
            "redo",
            "re_enable_automation",
            "set_or_delete_cue",
            "start_playing",
            "stop_all_clips",
            "stop_playing",
            "tap_tempo",
            "trigger_session_record",
            "undo"
        ]:
            callback = partial(self._call_method, self.song, method)
            self.osc_server.add_handler("/live/song/%s" % method, callback)

        #--------------------------------------------------------------------------------
        # Callbacks for Song: properties (read/write)
        #--------------------------------------------------------------------------------
        properties_rw = [
            "arrangement_overdub",
            "back_to_arranger",
            "clip_trigger_quantization",
            "current_song_time",
            "groove_amount",
            "is_ableton_link_enabled",
            "loop",
            "loop_length",
            "loop_start",
            "metronome",
            "midi_recording_quantization",
            "nudge_down",
            "nudge_up",
            "punch_in",
            "punch_out",
            "record_mode",
            "root_note",
            "scale_name",
            "session_record",
            "signature_denominator",
            "signature_numerator",
            "tempo"
        ]

        #--------------------------------------------------------------------------------
        # Callbacks for Song: properties (read-only)
        #--------------------------------------------------------------------------------
        properties_r = [
            "can_redo",
            "can_undo",
            "is_playing",
            "song_length",
            "session_record_status"
        ]

        for prop in properties_r + properties_rw:
            self.osc_server.add_handler("/live/song/get/%s" % prop, partial(self._get_property, self.song, prop))
            self.osc_server.add_handler("/live/song/start_listen/%s" % prop, partial(self._start_listen, self.song, prop))
            self.osc_server.add_handler("/live/song/stop_listen/%s" % prop, partial(self._stop_listen, self.song, prop))
        for prop in properties_rw:
            self.osc_server.add_handler("/live/song/set/%s" % prop, partial(self._set_property, self.song, prop))

        #--------------------------------------------------------------------------------
        # Callbacks for Song: Track properties
        #--------------------------------------------------------------------------------
        self.osc_server.add_handler("/live/song/get/num_tracks", lambda _: (len(self.song.tracks),))

        #--------------------------------------------------------------------------------
        # num_tracks has no native Live listener; piggyback on the tracks listener
        # (which fires whenever a track is added or removed) and push just the count.
        #--------------------------------------------------------------------------------
        def stop_num_tracks_listener(params: Tuple[Any] = ()):
            try:
                self.song.remove_tracks_listener(self.num_tracks_changed)
            except:
                pass

        def start_num_tracks_listener(params: Tuple[Any] = ()):
            stop_num_tracks_listener()
            self.song.add_tracks_listener(self.num_tracks_changed)
            self.num_tracks_changed()

        self.osc_server.add_handler("/live/song/start_listen/num_tracks", start_num_tracks_listener)
        self.osc_server.add_handler("/live/song/stop_listen/num_tracks", stop_num_tracks_listener)

        def song_get_track_names(params):
            if len(params) == 0:
                track_index_min, track_index_max = 0, len(self.song.tracks)
            else:
                track_index_min, track_index_max = params
                if track_index_max == -1:
                    track_index_max = len(self.song.tracks)
            return tuple(self.song.tracks[index].name for index in range(track_index_min, track_index_max))
        self.osc_server.add_handler("/live/song/get/track_names", song_get_track_names)
        self.osc_server.add_handler("/live/song/get/tracks", song_get_track_names)
        self.osc_server.add_handler("/live/song/start_listen/tracks",
                                     partial(self._start_listen, self.song, "tracks", getter=song_get_track_names))
        self.osc_server.add_handler("/live/song/stop_listen/tracks",
                                     partial(self._stop_listen, self.song, "tracks"))

        def song_get_track_data(params):
            """
            Retrieve one more properties of a block of tracks and their clips.
            Properties must be of the format track.property_name or clip.property_name.

            For example:
                /live/song/get/track_data 0 12 track.name clip.name clip.length

            Queries tracks 0..11, and returns a list of values comprising:

            [track_0_name, clip_0_0_name,   clip_0_1_name,   ... clip_0_7_name,
                           clip_1_0_length, clip_0_1_length, ... clip_0_7_length,
             track_1_name, clip_1_0_name,   clip_1_1_name,   ... clip_1_7_name, ...]
            """
            track_index_min, track_index_max, *properties = params
            track_index_min = int(track_index_min)
            track_index_max = int(track_index_max)
            self.logger.info("Getting track data: %s (tracks %d..%d)" %
                             (properties, track_index_min, track_index_max))
            if track_index_max == -1:
                track_index_max = len(self.song.tracks)
            rv = []
            for track_index in range(track_index_min, track_index_max):
                track = self.song.tracks[track_index]
                for prop in properties:
                    obj, property_name = prop.split(".")
                    if obj == "track":
                        if property_name == "num_devices":
                            value = len(track.devices)
                        else:
                            value = getattr(track, property_name)
                            if isinstance(value, Live.Track.Track):
                                #--------------------------------------------------------------------------------
                                # Map Track objects to their track_index to return via OSC
                                #--------------------------------------------------------------------------------
                                value = list(self.song.tracks).index(value)
                        rv.append(value)
                    elif obj == "clip":
                        for clip_slot in track.clip_slots:
                            if clip_slot.clip is not None:
                                rv.append(getattr(clip_slot.clip, property_name))
                            else:
                                rv.append(None)
                    elif obj == "clip_slot":
                        for clip_slot in track.clip_slots:
                            rv.append(getattr(clip_slot, property_name))
                    elif obj == "device":
                        for device in track.devices:
                            rv.append(getattr(device, property_name))
                    else:
                        self.logger.error("Unknown object identifier in get/track_data: %s" % obj)
            return tuple(rv)
        self.osc_server.add_handler("/live/song/get/track_data", song_get_track_data)

        def song_start_listen_track_data(params):
            """
            Bulk-arm the individual per-property listeners implied by a track_data
            request, so that /live/track/get/<prop>, /live/clip/get/<prop>,
            /live/clip_slot/get/<prop> and /live/device/get/<prop> push updates for
            every track/clip/device in range going forward -- without having to call
            each object's own start_listen individually.

            Repeated calls merge (union) into whatever's already active, rather than
            replacing it. The reply is a one-time initial snapshot, in exactly the same
            shape as get/track_data, sent to /live/song/get/track_data; everything after
            that arrives via the ordinary per-property push addresses.
            """
            track_index_min, track_index_max, *properties = params
            track_index_min = int(track_index_min)
            track_index_max = int(track_index_max)
            if track_index_max == -1:
                track_index_max = len(self.song.tracks)
            if not properties:
                self.logger.error("start_listen/track_data requires at least one property")
                return
            for track_index in range(track_index_min, track_index_max):
                for prop_string in properties:
                    pair = (track_index, prop_string)
                    if pair not in self._track_data_active:
                        self._track_data_active.add(pair)
                        self._track_data_start_pair(track_index, prop_string)
            if self._track_data_auto_rebuild:
                self._track_data_ensure_structural_listeners()
            self.osc_server.send("/live/song/get/track_data", song_get_track_data(params))
        self.osc_server.add_handler("/live/song/start_listen/track_data", song_start_listen_track_data)

        def song_stop_listen_track_data(params):
            """
            Reverse of song_start_listen_track_data. If properties are given, removes
            exactly those (track, property) pairs; if not, removes every track_data
            listener for tracks in the given range regardless of property.
            """
            track_index_min, track_index_max, *properties = params
            track_index_min = int(track_index_min)
            track_index_max = int(track_index_max)
            if track_index_max == -1:
                track_index_max = len(self.song.tracks)
            if properties:
                for track_index in range(track_index_min, track_index_max):
                    for prop_string in properties:
                        pair = (track_index, prop_string)
                        if pair in self._track_data_active:
                            self._track_data_stop_pair(track_index, prop_string)
                            self._track_data_active.discard(pair)
            else:
                self._track_data_stop_range(track_index_min, track_index_max)
            if self._track_data_active:
                self._track_data_sync_has_clip_listeners()
            else:
                self._track_data_teardown_structural_listeners()
        self.osc_server.add_handler("/live/song/stop_listen/track_data", song_stop_listen_track_data)

        def song_get_track_data_auto_rebuild(params):
            return (self._track_data_auto_rebuild,)
        self.osc_server.add_handler("/live/song/get/track_data_auto_rebuild", song_get_track_data_auto_rebuild)

        def song_set_track_data_auto_rebuild(params):
            enabled, = params
            self._track_data_auto_rebuild = bool(int(enabled))
            if self._track_data_auto_rebuild:
                if self._track_data_active:
                    self._track_data_ensure_structural_listeners()
            else:
                self._track_data_teardown_structural_listeners()
        self.osc_server.add_handler("/live/song/set/track_data_auto_rebuild", song_set_track_data_auto_rebuild)

        def song_find_tracks(params):
            """
            Find tracks whose name contains name_pattern (case-insensitive substring match).

            Track names are user-mutable and change across song reloads, so this is intended
            as a best-effort lookup, e.g. to feed a track_index into /live/track/find_devices.

                /live/song/find_tracks Guitar

            Returns a flat list of (track_index, track_name) pairs for every match.
            """
            name_pattern, = params
            name_pattern = str(name_pattern).lower()
            rv = []
            for track_index, track in enumerate(self.song.tracks):
                if name_pattern in track.name.lower():
                    rv.append(track_index)
                    rv.append(track.name)
            return tuple(rv)
        self.osc_server.add_handler("/live/song/find_tracks", song_find_tracks)

        def song_find_devices(params):
            """
            Find devices across all tracks matching class_name exactly, optionally narrowed
            by a case-insensitive substring match against track name and/or device name.

            Device class_name (e.g. "Looper") is the only identifier that survives renames,
            so it's the required filter; track_name_pattern/device_name_pattern are optional
            disambiguators for sets containing more than one device of the same class.

                /live/song/find_devices Looper
                /live/song/find_devices Looper Guitar
                /live/song/find_devices Looper Guitar "Looper 2"

            Returns a flat list of (track_index, device_index, track_name, device_name) quads.
            """
            class_name, *rest = params
            track_name_pattern = str(rest[0]).lower() if len(rest) > 0 and rest[0] else ""
            device_name_pattern = str(rest[1]).lower() if len(rest) > 1 and rest[1] else ""
            rv = []
            for track_index, track in enumerate(self.song.tracks):
                if track_name_pattern and track_name_pattern not in track.name.lower():
                    continue
                for device_index, device in enumerate(track.devices):
                    if device.class_name != class_name:
                        continue
                    if device_name_pattern and device_name_pattern not in device.name.lower():
                        continue
                    rv.extend((track_index, device_index, track.name, device.name))
            return tuple(rv)
        self.osc_server.add_handler("/live/song/find_devices", song_find_devices)

        def song_export_structure(params):
            tracks = []
            for track_index, track in enumerate(self.song.tracks):
                group_track = None
                if track.group_track is not None:
                    group_track = list(self.song.tracks).index(track.group_track)
                track_data = {
                    "index": track_index,
                    "name": track.name,
                    "is_foldable": track.is_foldable,
                    "group_track": group_track,
                    "clips": [],
                    "devices": []
                }
                for clip_index, clip_slot in enumerate(track.clip_slots):
                    if clip_slot.clip:
                        clip_data = {
                            "index": clip_index,
                            "name": clip_slot.clip.name,
                            "length": clip_slot.clip.length,
                        }
                        track_data["clips"].append(clip_data)

                for device_index, device in enumerate(track.devices):
                    device_data = {
                        "class_name": device.class_name,
                        "type": device.type,
                        "name": device.name,
                        "parameters": []
                    }
                    for parameter in device.parameters:
                        device_data["parameters"].append({
                            "name": parameter.name,
                            "value": parameter.value,
                            "min": parameter.min,
                            "max": parameter.max,
                            "is_quantized": parameter.is_quantized,
                        })
                    track_data["devices"].append(device_data)

                tracks.append(track_data)
            song = {
                "tracks": tracks
            }

            if sys.platform == "darwin":
                #--------------------------------------------------------------------------------
                # On macOS, TMPDIR by default points to a process-specific directory.
                # We want to use a global temp dir (typically, tmp) so that other processes
                # know where to find this output .json, so unset TMPDIR.
                #--------------------------------------------------------------------------------
                os.environ["TMPDIR"] = ""
            fd = open(os.path.join(tempfile.gettempdir(), "abletonosc-song-structure.json"), "w")
            json.dump(song, fd)
            fd.close()
            self.logger.warning("Exported song structure to directory %s" % tempfile.gettempdir())
            return (1,)
        self.osc_server.add_handler("/live/song/export/structure", song_export_structure)

        #--------------------------------------------------------------------------------
        # Callbacks for Song: Scene properties
        #--------------------------------------------------------------------------------
        self.osc_server.add_handler("/live/song/get/num_scenes", lambda _: (len(self.song.scenes),))

        #--------------------------------------------------------------------------------
        # num_scenes has no native Live listener; piggyback on the scenes listener
        # (which fires whenever a scene is added or removed) and push just the count.
        #--------------------------------------------------------------------------------
        def stop_num_scenes_listener(params: Tuple[Any] = ()):
            try:
                self.song.remove_scenes_listener(self.num_scenes_changed)
            except:
                pass

        def start_num_scenes_listener(params: Tuple[Any] = ()):
            stop_num_scenes_listener()
            self.song.add_scenes_listener(self.num_scenes_changed)
            self.num_scenes_changed()

        self.osc_server.add_handler("/live/song/start_listen/num_scenes", start_num_scenes_listener)
        self.osc_server.add_handler("/live/song/stop_listen/num_scenes", stop_num_scenes_listener)

        def song_get_scene_names(params):
            if len(params) == 0:
                scene_index_min, scene_index_max = 0, len(self.song.scenes)
            else:
                scene_index_min, scene_index_max = params
            return tuple(self.song.scenes[index].name for index in range(scene_index_min, scene_index_max))
        self.osc_server.add_handler("/live/song/get/scenes/name", song_get_scene_names)
        self.osc_server.add_handler("/live/song/get/scenes", song_get_scene_names)
        self.osc_server.add_handler("/live/song/start_listen/scenes",
                                     partial(self._start_listen, self.song, "scenes", getter=song_get_scene_names))
        self.osc_server.add_handler("/live/song/stop_listen/scenes",
                                     partial(self._stop_listen, self.song, "scenes"))

        #--------------------------------------------------------------------------------
        # Callbacks for Song: Cue point properties
        #--------------------------------------------------------------------------------
        def song_get_cue_points(song, _):
            cue_points = song.cue_points
            cue_point_pairs = [(cue_point.name, cue_point.time) for cue_point in cue_points]
            return tuple(element for pair in cue_point_pairs for element in pair)
        self.osc_server.add_handler("/live/song/get/cue_points", partial(song_get_cue_points, self.song))
        self.osc_server.add_handler("/live/song/start_listen/cue_points",
                                     partial(self._start_listen, self.song, "cue_points",
                                             getter=partial(song_get_cue_points, self.song)))
        self.osc_server.add_handler("/live/song/stop_listen/cue_points",
                                     partial(self._stop_listen, self.song, "cue_points"))

        def song_jump_to_cue_point(song, params: Tuple[Any] = ()):
            cue_point_index = params[0]
            if isinstance(cue_point_index, str):
                for cue_point in song.cue_points:
                    if cue_point.name == cue_point_index:
                        cue_point.jump()
            elif isinstance(cue_point_index, int):
                cue_point = song.cue_points[cue_point_index]
                cue_point.jump()
        self.osc_server.add_handler("/live/song/cue_point/jump", partial(song_jump_to_cue_point, self.song))

        self.osc_server.add_handler("/live/song/cue_point/add_or_delete", partial(self._call_method, self.song, "set_or_delete_cue"))
        def song_cue_point_set_name(song, params: Tuple[Any] = ()):
            cue_point_index = params[0]
            new_name = params[1]
            cue_point = song.cue_points[cue_point_index]
            cue_point.name = new_name
        self.osc_server.add_handler("/live/song/cue_point/set/name", partial(song_cue_point_set_name, self.song))

        #--------------------------------------------------------------------------------
        # Listener for /live/song/get/beat
        #--------------------------------------------------------------------------------
        self.last_song_time = -1.0
        
        def stop_beat_listener(params: Tuple[Any] = ()):
            try:
                self.song.remove_current_song_time_listener(self.current_song_time_changed)
                self.logger.info("Removing beat listener")
            except:
                pass

        def start_beat_listener(params: Tuple[Any] = ()):
            stop_beat_listener()
            self.logger.info("Adding beat listener")
            self.song.add_current_song_time_listener(self.current_song_time_changed)

        self.osc_server.add_handler("/live/song/start_listen/beat", start_beat_listener)
        self.osc_server.add_handler("/live/song/stop_listen/beat", stop_beat_listener)

    def current_song_time_changed(self):
        #--------------------------------------------------------------------------------
        # If song has rewound or skipped to next beat, sent a /live/beat message
        #--------------------------------------------------------------------------------
        if (self.song.current_song_time < self.last_song_time) or \
                (int(self.song.current_song_time) > int(self.last_song_time)):
            self.osc_server.send("/live/song/get/beat", (int(self.song.current_song_time),))
        self.last_song_time = self.song.current_song_time

    def num_tracks_changed(self):
        self.osc_server.send("/live/song/get/num_tracks", (len(self.song.tracks),))

    def num_scenes_changed(self):
        self.osc_server.send("/live/song/get/num_scenes", (len(self.song.scenes),))

    #--------------------------------------------------------------------------------
    # start_listen/stop_listen on track_data
    #--------------------------------------------------------------------------------
    def _track_data_get_sibling_handler(self, obj_type: str):
        """
        Lazily resolve the shared TrackHandler/ClipHandler/ClipSlotHandler/DeviceHandler
        instance for a given track_data object prefix, matched by its class_identifier
        string rather than isinstance() against an imported class (see the comment on
        _TRACK_DATA_OBJECT_TYPES above for why). Caches only successful lookups -- a
        failed one isn't cached, so a call that arrives before self.manager.handlers is
        fully populated doesn't permanently poison later, legitimate lookups.
        """
        if obj_type not in self._track_data_sibling_handler_cache:
            if obj_type not in _TRACK_DATA_OBJECT_TYPES:
                self.logger.error("Unknown track_data object type: %s" % obj_type)
                return None
            handler = next((h for h in self.manager.handlers if getattr(h, "class_identifier", None) == obj_type), None)
            if handler is None:
                self.logger.error("Could not find sibling handler for track_data object type: %s" % obj_type)
                return None
            self._track_data_sibling_handler_cache[obj_type] = handler
        return self._track_data_sibling_handler_cache[obj_type]

    def _track_data_resolve(self, track_index, obj, property_name):
        """
        Resolve one (track_index, "obj.property_name") track_data pair into the list of
        concrete (handler, target, prop, params) native listener registrations it
        implies, given the CURRENT state of the Live set. Always recomputed fresh, never
        cached, so it naturally reflects renames/reorders/clip creation and deletion.
        """
        if track_index < 0 or track_index >= len(self.song.tracks):
            return []
        track = self.song.tracks[track_index]
        if obj == "track":
            if property_name == "num_devices":
                #--------------------------------------------------------------------------------
                # num_devices is a synthetic value (len(track.devices)), unlike every other
                # track_data property -- there is no native Live listener for it. get/track_data
                # still supports reading it; listening for changes is not supported.
                #--------------------------------------------------------------------------------
                self.logger.warning("track.num_devices cannot be listened for (no native listener); skipping")
                return []
            handler = self._track_data_get_sibling_handler("track")
            return [(handler, track, property_name, (track_index,))] if handler else []
        elif obj == "clip_slot":
            handler = self._track_data_get_sibling_handler("clip_slot")
            if not handler:
                return []
            return [(handler, clip_slot, property_name, (track_index, clip_index))
                    for clip_index, clip_slot in enumerate(track.clip_slots)]
        elif obj == "clip":
            if property_name in _TRACK_DATA_CLIP_PROPERTIES_WITHOUT_LISTENER:
                #--------------------------------------------------------------------------------
                # See _TRACK_DATA_CLIP_PROPERTIES_WITHOUT_LISTENER above -- no native Live
                # listener exists for this property. get/track_data still supports reading it;
                # listening for changes is not supported.
                #--------------------------------------------------------------------------------
                self.logger.warning("clip.%s cannot be listened for (no native listener); skipping" % property_name)
                return []
            handler = self._track_data_get_sibling_handler("clip")
            if not handler:
                return []
            return [(handler, clip_slot.clip, property_name, (track_index, clip_index))
                    for clip_index, clip_slot in enumerate(track.clip_slots)
                    if clip_slot.clip is not None]
        elif obj == "device":
            handler = self._track_data_get_sibling_handler("device")
            if not handler:
                return []
            return [(handler, device, property_name, (track_index, device_index))
                    for device_index, device in enumerate(track.devices)]
        else:
            self.logger.error("Unknown object identifier in track_data listen: %s" % obj)
            return []

    def _track_data_start_pair(self, track_index, prop_string):
        obj, property_name = prop_string.split(".")
        for handler, target, prop, params in self._track_data_resolve(track_index, obj, property_name):
            handler._start_listen(target, prop, params)

    def _track_data_stop_pair(self, track_index, prop_string):
        obj, property_name = prop_string.split(".")
        for handler, target, prop, params in self._track_data_resolve(track_index, obj, property_name):
            handler._stop_listen(target, prop, params)

    def _track_data_stop_range(self, track_index_min, track_index_max):
        """
        Stop every native listener, of any track_data object type, whose params
        reference a track in [track_index_min, track_index_max) -- used by
        stop_listen/track_data when called without an explicit property list, and by
        clear_api(). Scans the sibling handlers' own listener_functions/listener_objects
        directly rather than tracking a separate registry, so this also stops any
        listener a client registered independently via the plain per-object
        start_listen endpoints for a track/clip/device in range -- a known, documented
        trade-off (see README).
        """
        for obj_type in _TRACK_DATA_OBJECT_TYPES:
            handler = self._track_data_get_sibling_handler(obj_type)
            if handler is None:
                continue
            for listener_key in list(handler.listener_functions.keys()):
                prop, params = listener_key
                if params and track_index_min <= int(params[0]) < track_index_max:
                    target = handler.listener_objects.get(listener_key)
                    if target is not None:
                        handler._stop_listen(target, prop, params)
        self._track_data_active = {(t, p) for (t, p) in self._track_data_active
                                    if not (track_index_min <= t < track_index_max)}

    def _track_data_sync_has_clip_listeners(self):
        """
        Ensure a raw has_clip listener is installed on every clip slot of every track
        that currently has an active clip.<property> track_data pair, and removed from
        every other clip slot. This is what lets a clip created after
        start_listen/track_data was called pick up its requested properties
        automatically (see _track_data_on_has_clip_changed) -- without it, a clip
        appearing in a slot/track that had nothing listening on it before would go
        unnoticed, since nothing else in the codebase tracks that intent.
        """
        desired_tracks = {track_index for track_index, prop_string in self._track_data_active
                           if prop_string.startswith("clip.")}
        desired_slots = {}
        for track_index in desired_tracks:
            if track_index < 0 or track_index >= len(self.song.tracks):
                continue
            for clip_index, clip_slot in enumerate(self.song.tracks[track_index].clip_slots):
                desired_slots[clip_slot] = (track_index, clip_index)

        for clip_slot in list(self._track_data_has_clip_listeners.keys()):
            if clip_slot not in desired_slots:
                callback = self._track_data_has_clip_listeners.pop(clip_slot)
                try:
                    clip_slot.remove_has_clip_listener(callback)
                except Exception as e:
                    self.logger.info("Exception removing has_clip listener (likely benign): %s" % e)

        for clip_slot, (track_index, clip_index) in desired_slots.items():
            if clip_slot not in self._track_data_has_clip_listeners:
                callback = partial(self._track_data_on_has_clip_changed, clip_slot, track_index, clip_index)
                clip_slot.add_has_clip_listener(callback)
                self._track_data_has_clip_listeners[clip_slot] = callback

    def _track_data_on_has_clip_changed(self, clip_slot, track_index, clip_index):
        """
        Fired when a clip is created or deleted in a slot covered by an active
        clip.<property> track_data pair. Surgically starts/stops just this slot's clip
        listeners, reading ClipHandler's own listener_functions/listener_objects to
        decide what's already registered rather than tracking that separately.
        """
        clip_handler = self._track_data_get_sibling_handler("clip")
        if clip_handler is None:
            return
        for track_idx, prop_string in list(self._track_data_active):
            if track_idx != track_index or not prop_string.startswith("clip."):
                continue
            property_name = prop_string.split(".", 1)[1]
            if property_name in _TRACK_DATA_CLIP_PROPERTIES_WITHOUT_LISTENER:
                # See _TRACK_DATA_CLIP_PROPERTIES_WITHOUT_LISTENER -- already warned about once
                # in _track_data_resolve when start_listen/track_data was first called; no need
                # to retry (and fail, and re-warn) on every clip that appears.
                continue
            listener_key = (property_name, (track_index, clip_index))
            if clip_slot.clip is not None:
                if listener_key not in clip_handler.listener_functions:
                    clip_handler._start_listen(clip_slot.clip, property_name, (track_index, clip_index))
            else:
                if listener_key in clip_handler.listener_functions:
                    old_target = clip_handler.listener_objects[listener_key]
                    clip_handler._stop_listen(old_target, property_name, (track_index, clip_index))

    def _track_data_on_structure_changed(self):
        """
        Fired when song.tracks or song.scenes changes (track/scene added, removed, or
        reordered). A reorder silently repoints which Track object a given track_index
        refers to, so this does a full resync rather than an incremental diff: every
        active pair is re-resolved against current live state and re-started, which
        transparently repoints existing registrations (_start_listen tears down and
        recreates on an existing key) at whatever object now sits at that index.
        Track/scene-count changes are comparatively rare (unlike has_clip), so this
        blunt whole-set approach -- mirroring session_ring.py's rebuild-on-resize -- is
        an acceptable trade-off for the simplicity it buys.
        """
        num_tracks = len(self.song.tracks)
        stale_tracks = {t for (t, p) in self._track_data_active if t >= num_tracks}
        for track_index in stale_tracks:
            self._track_data_stop_range(track_index, track_index + 1)
        for track_index, prop_string in list(self._track_data_active):
            self._track_data_start_pair(track_index, prop_string)
        self._track_data_sync_has_clip_listeners()

    def _track_data_ensure_structural_listeners(self):
        if not self._track_data_structural_listeners_installed:
            self.song.add_tracks_listener(self._track_data_on_structure_changed)
            self.song.add_scenes_listener(self._track_data_on_structure_changed)
            self._track_data_structural_listeners_installed = True
        self._track_data_sync_has_clip_listeners()

    def _track_data_teardown_structural_listeners(self):
        if self._track_data_structural_listeners_installed:
            try:
                self.song.remove_tracks_listener(self._track_data_on_structure_changed)
            except Exception:
                pass
            try:
                self.song.remove_scenes_listener(self._track_data_on_structure_changed)
            except Exception:
                pass
            self._track_data_structural_listeners_installed = False
        for clip_slot, callback in list(self._track_data_has_clip_listeners.items()):
            try:
                clip_slot.remove_has_clip_listener(callback)
            except Exception:
                pass
        self._track_data_has_clip_listeners.clear()

    def clear_api(self):
        super().clear_api()
        try:
            self.song.remove_current_song_time_listener(self.current_song_time_changed)
        except:
            pass
        try:
            self.song.remove_tracks_listener(self.num_tracks_changed)
        except:
            pass
        try:
            self.song.remove_scenes_listener(self.num_scenes_changed)
        except:
            pass
        self._track_data_stop_range(0, len(self.song.tracks))
        self._track_data_teardown_structural_listeners()
        self._track_data_active.clear()
