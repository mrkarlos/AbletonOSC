from functools import partial
from typing import Optional, Tuple, Any
from .handler import AbletonOSCHandler

class ApplicationViewHandler(AbletonOSCHandler):
    """
    Wraps Live's Application.View class (self.application.view), i.e. the top-level
    UI/window state -- which main view is focused, hot-swap/browse mode, and the
    show/hide/focus/scroll/zoom navigation methods.

    This is distinct from /live/view/*, which wraps Song.View (selection state), and
    from /live/song_view/*, which wraps the rest of Song.View.
    """
    def __init__(self, manager):
        super().__init__(manager)
        self.class_identifier = "application_view"

    def init_api(self):
        target = self.application.view

        properties_r = [
            "browse_mode",
            "focused_document_view",
        ]

        for prop in properties_r:
            self.osc_server.add_handler("/live/application_view/get/%s" % prop,
                                        partial(self._get_property, target, prop))
            self.osc_server.add_handler("/live/application_view/start_listen/%s" % prop,
                                        partial(self._start_listen, target, prop))
            self.osc_server.add_handler("/live/application_view/stop_listen/%s" % prop,
                                        partial(self._stop_listen, target, prop))

        #--------------------------------------------------------------------------------
        # Action methods (no meaningful return value) -- same shape as e.g. track.py's
        # "delete_device"/"stop_all_clips" methods loop.
        #--------------------------------------------------------------------------------
        methods = [
            "show_view",
            "hide_view",
            "focus_view",
            "toggle_browse",
        ]
        for method in methods:
            self.osc_server.add_handler("/live/application_view/%s" % method,
                                        partial(self._call_method, target, method))

        #--------------------------------------------------------------------------------
        # Query methods -- placed under get/ since they return a value the caller wants
        # back, same convention as e.g. device.py's /live/device/get/parameter/value.
        # is_view_visible(name) (-> bool) goes through the generic _call_method (see
        # handler.py), which now captures and normalises the return value.
        #--------------------------------------------------------------------------------
        self.osc_server.add_handler("/live/application_view/get/is_view_visible",
                                    partial(self._call_method, target, "is_view_visible"))

        #--------------------------------------------------------------------------------
        # available_main_views() returns Live "symbol" objects, not plain str -- _call_method's
        # generic OSC-primitive type check (deliberately conservative, since it also has to
        # avoid trying to serialise a raw Live object like a Clip -- see handler.py) doesn't
        # recognise them, so it drops the return value rather than crashing. Cast explicitly
        # to str here instead of relying on the generic path.
        #--------------------------------------------------------------------------------
        def available_main_views(params: Tuple[Any] = ()):
            return tuple(str(view_name) for view_name in target.available_main_views())

        self.osc_server.add_handler("/live/application_view/get/available_main_views", available_main_views)

        #--------------------------------------------------------------------------------
        # scroll_view/zoom_view take (direction: int, view_name: str, modifier_pressed: bool).
        # Cast direction/modifier_pressed defensively, as OSC clients such as TouchOSC send
        # floats by default (same precedent as clip.py/device.py's int() casts).
        #--------------------------------------------------------------------------------
        def scroll_view(params: Tuple[Any] = ()):
            direction, view_name, modifier_pressed = params
            target.scroll_view(int(direction), view_name, bool(modifier_pressed))

        def zoom_view(params: Tuple[Any] = ()):
            direction, view_name, modifier_pressed = params
            target.zoom_view(int(direction), view_name, bool(modifier_pressed))

        self.osc_server.add_handler("/live/application_view/scroll_view", scroll_view)
        self.osc_server.add_handler("/live/application_view/zoom_view", zoom_view)
