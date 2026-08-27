from functools import partial
from typing import Optional, Tuple, Any
from .handler import AbletonOSCHandler

class SongViewHandler(AbletonOSCHandler):
    """
    Wraps the parts of Live's Song.View class (self.song.view) that aren't already
    exposed by the legacy /live/view/* namespace.

    /live/view/* (view.py) covers selected_scene/selected_track/selected_clip/
    selected_device and is left untouched for backward compatibility. This handler
    covers draw_mode, follow_song, detail_clip and highlighted_clip_slot.
    """
    def __init__(self, manager):
        super().__init__(manager)
        self.class_identifier = "song_view"

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
