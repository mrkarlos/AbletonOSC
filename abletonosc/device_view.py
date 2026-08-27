from typing import Tuple, Any
from .handler import AbletonOSCHandler

class DeviceViewHandler(AbletonOSCHandler):
    """
    Wraps Live's Device.View class (device.view), indexed by (track_index, device_index),
    matching device.py's addressing scheme exactly.
    """
    def __init__(self, manager):
        super().__init__(manager)
        self.class_identifier = "device_view"

    def init_api(self):
        def create_device_view_callback(func, *args, include_ids: bool = False):
            def device_view_callback(params: Tuple[Any]):
                track_index, device_index = int(params[0]), int(params[1])
                device_view = self.song.tracks[track_index].devices[device_index].view
                if include_ids:
                    rv = func(device_view, *args, params[0:])
                else:
                    rv = func(device_view, *args, params[2:])

                if rv is not None:
                    return (track_index, device_index, *rv)

            return device_view_callback

        properties_rw = [
            "is_collapsed",
        ]

        for prop in properties_rw:
            self.osc_server.add_handler("/live/device_view/get/%s" % prop,
                                        create_device_view_callback(self._get_property, prop))
            self.osc_server.add_handler("/live/device_view/set/%s" % prop,
                                        create_device_view_callback(self._set_property, prop))
            self.osc_server.add_handler("/live/device_view/start_listen/%s" % prop,
                                        create_device_view_callback(self._start_listen, prop, include_ids=True))
            self.osc_server.add_handler("/live/device_view/stop_listen/%s" % prop,
                                        create_device_view_callback(self._stop_listen, prop, include_ids=True))
