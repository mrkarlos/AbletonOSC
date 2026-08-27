from typing import Tuple, Any
from .handler import AbletonOSCHandler

class ClipViewHandler(AbletonOSCHandler):
    """
    Wraps Live's Clip.View class (clip.view), indexed by (track_index, clip_index),
    matching clip.py's addressing scheme exactly.
    """
    def __init__(self, manager):
        super().__init__(manager)
        self.class_identifier = "clip_view"

    def init_api(self):
        def create_clip_view_callback(func, *args, pass_clip_index: bool = False):
            def clip_view_callback(params: Tuple[Any]) -> Tuple:
                track_index, clip_index = int(params[0]), int(params[1])
                track = self.song.tracks[track_index]
                clip = track.clip_slots[clip_index].clip
                if clip is None:
                    self.logger.warning("No clip at track %d slot %d" % (track_index, clip_index))
                    return
                clip_view = clip.view

                if pass_clip_index:
                    rv = func(clip_view, *args, tuple(params[0:]))
                else:
                    rv = func(clip_view, *args, tuple(params[2:]))

                if rv is not None:
                    return (track_index, clip_index, *rv)

            return clip_view_callback

        #--------------------------------------------------------------------------------
        # grid_quantization/grid_is_triplet are documented as NOT observable in the LOM,
        # so only get/set handlers are registered -- this is deliberate, not an oversight.
        #--------------------------------------------------------------------------------
        properties_rw = [
            "grid_quantization",
            "grid_is_triplet",
        ]

        for prop in properties_rw:
            self.osc_server.add_handler("/live/clip_view/get/%s" % prop,
                                        create_clip_view_callback(self._get_property, prop))
            self.osc_server.add_handler("/live/clip_view/set/%s" % prop,
                                        create_clip_view_callback(self._set_property, prop))

        methods = [
            "show_envelope",
            "hide_envelope",
            "show_loop",
        ]
        for method in methods:
            self.osc_server.add_handler("/live/clip_view/%s" % method,
                                        create_clip_view_callback(self._call_method, method))

        #--------------------------------------------------------------------------------
        # select_envelope_parameter(parameter) is deliberately not exposed: it needs a
        # 3rd (device_index, parameter_index) address that doesn't fit the clip_view
        # 2-index protocol without a new addressing convention. Left for a future
        # iteration.
        #--------------------------------------------------------------------------------
