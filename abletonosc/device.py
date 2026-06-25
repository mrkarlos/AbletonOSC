from typing import Tuple, Any
from .handler import AbletonOSCHandler
from .device_registry import DEVICE_REGISTRY

class DeviceHandler(AbletonOSCHandler):
    def __init__(self, manager):
        super().__init__(manager)
        self.class_identifier = "device"
        self._class_listeners = {}  # key -> (callback_fn, remove_fn)

    def clear_api(self):
        for key, (fn, remove_fn) in list(self._class_listeners.items()):
            try:
                remove_fn(fn)
            except Exception as e:
                self.logger.info("Exception removing class listener: %s" % e)
        self._class_listeners.clear()
        super().clear_api()

    def init_api(self):
        def create_device_callback(func, *args, include_ids: bool = False):
            def device_callback(params: Tuple[Any]):
                track_index, device_index = int(params[0]), int(params[1])
                device = self.song.tracks[track_index].devices[device_index]
                if (include_ids):
                    rv = func(device, *args, params[0:])
                else:
                    rv = func(device, *args, params[2:])

                if rv is not None:
                    return (track_index, device_index, *rv)

            return device_callback

        methods = [
        ]
        properties_r = [
            "class_name",
            "name",
            "type"
        ]
        properties_rw = [
            "is_active",
        ]

        for method in methods:
            self.osc_server.add_handler("/live/device/%s" % method,
                                        create_device_callback(self._call_method, method))

        for prop in properties_r + properties_rw:
            self.osc_server.add_handler("/live/device/get/%s" % prop,
                                        create_device_callback(self._get_property, prop))
            self.osc_server.add_handler("/live/device/start_listen/%s" % prop,
                                        create_device_callback(self._start_listen, prop))
            self.osc_server.add_handler("/live/device/stop_listen/%s" % prop,
                                        create_device_callback(self._stop_listen, prop))
        for prop in properties_rw:
            self.osc_server.add_handler("/live/device/set/%s" % prop,
                                        create_device_callback(self._set_property, prop))

        #--------------------------------------------------------------------------------
        # Device: Get/set parameter lists
        #--------------------------------------------------------------------------------
        def device_get_num_parameters(device, params: Tuple[Any] = ()):
            return len(device.parameters),

        def device_get_parameters_name(device, params: Tuple[Any] = ()):
            return tuple(parameter.name for parameter in device.parameters)

        def device_get_parameters_value(device, params: Tuple[Any] = ()):
            return tuple(parameter.value for parameter in device.parameters)

        def device_get_parameters_min(device, params: Tuple[Any] = ()):
            return tuple(parameter.min for parameter in device.parameters)

        def device_get_parameters_max(device, params: Tuple[Any] = ()):
            return tuple(parameter.max for parameter in device.parameters)

        def device_get_parameters_is_quantized(device, params: Tuple[Any] = ()):
            return tuple(parameter.is_quantized for parameter in device.parameters)

        def device_set_parameters_value(device, params: Tuple[Any] = ()):
            for index, value in enumerate(params):
                device.parameters[index].value = value

        self.osc_server.add_handler("/live/device/get/num_parameters", create_device_callback(device_get_num_parameters))
        self.osc_server.add_handler("/live/device/get/parameters/name", create_device_callback(device_get_parameters_name))
        self.osc_server.add_handler("/live/device/get/parameters/value", create_device_callback(device_get_parameters_value))
        self.osc_server.add_handler("/live/device/get/parameters/min", create_device_callback(device_get_parameters_min))
        self.osc_server.add_handler("/live/device/get/parameters/max", create_device_callback(device_get_parameters_max))
        self.osc_server.add_handler("/live/device/get/parameters/is_quantized", create_device_callback(device_get_parameters_is_quantized))
        self.osc_server.add_handler("/live/device/set/parameters/value", create_device_callback(device_set_parameters_value))

        #--------------------------------------------------------------------------------
        # Device: Get/set individual parameters
        #--------------------------------------------------------------------------------
        def device_get_parameter_value(device, params: Tuple[Any] = ()):
            # Cast to ints so that we can tolerate floats from interfaces such as TouchOSC
            # that send floats by default.
            # https://github.com/ideoforms/AbletonOSC/issues/33
            param_index = int(params[0])
            return param_index, device.parameters[param_index].value
        
        # Uses str_for_value method to return the UI-friendly version of a parameter value (ex: "2500 Hz")
        def device_get_parameter_value_string(device, params: Tuple[Any] = ()):
            param_index = int(params[0])
            return param_index, device.parameters[param_index].str_for_value(device.parameters[param_index].value)
        
        def device_get_parameter_value_listener(device, params: Tuple[Any] = ()):

            def property_changed_callback():
                value = device.parameters[params[2]].value
                self.logger.info("Property %s changed of %s %s: %s" % ('value', 'device parameter', str(params), value))
                self.osc_server.send("/live/device/get/parameter/value", (*params, value,))

                value_string = device.parameters[params[2]].str_for_value(device.parameters[params[2]].value)
                self.logger.info("Property %s changed of %s %s: %s" % ('value_string', 'device parameter', str(params), value_string))
                self.osc_server.send("/live/device/get/parameter/value_string", (*params, value_string,))

            listener_key = ('device_parameter_value', tuple(params))
            if listener_key in self.listener_functions:
               device_get_parameter_remove_value_listener(device, params)

            self.logger.info("Adding listener for %s %s, property: %s" % ('device parameter', str(params), 'value'))
            device.parameters[params[2]].add_value_listener(property_changed_callback)
            self.listener_functions[listener_key] = property_changed_callback

            property_changed_callback()

        def device_get_parameter_remove_value_listener(device, params: Tuple[Any] = ()):
            listener_key = ('device_parameter_value', tuple(params))
            if listener_key in self.listener_functions:
                self.logger.info("Removing listener for %s %s, property %s" % (self.class_identifier, str(params), 'value'))
                listener_function = self.listener_functions[listener_key]
                device.parameters[params[2]].remove_value_listener(listener_function)
                del self.listener_functions[listener_key]
            else:
                self.logger.warning("No listener function found for property: %s (%s)" % (prop, str(params)))

        def device_set_parameter_value(device, params: Tuple[Any] = ()):
            param_index, param_value = params[:2]
            param_index = int(param_index)
            device.parameters[param_index].value = param_value

        def device_get_parameter_name(device, params: Tuple[Any] = ()):
            param_index = int(params[0])
            return param_index, device.parameters[param_index].name

        self.osc_server.add_handler("/live/device/get/parameter/value", create_device_callback(device_get_parameter_value))
        self.osc_server.add_handler("/live/device/get/parameter/value_string", create_device_callback(device_get_parameter_value_string))
        self.osc_server.add_handler("/live/device/set/parameter/value", create_device_callback(device_set_parameter_value))
        self.osc_server.add_handler("/live/device/get/parameter/name", create_device_callback(device_get_parameter_name))
        self.osc_server.add_handler("/live/device/start_listen/parameter/value", create_device_callback(device_get_parameter_value_listener, include_ids = True))
        self.osc_server.add_handler("/live/device/stop_listen/parameter/value", create_device_callback(device_get_parameter_remove_value_listener, include_ids = True))

        #--------------------------------------------------------------------------------
        # Device class-specific handlers (from DEVICE_REGISTRY)
        #--------------------------------------------------------------------------------
        def create_device_class_callback(expected_class, action, name):
            def callback(params):
                track_index, device_index = int(params[0]), int(params[1])
                device = self.song.tracks[track_index].devices[device_index]
                if device.class_name != expected_class:
                    self.logger.error("Device (%d,%d) is %s, expected %s" % (
                        track_index, device_index, device.class_name, expected_class))
                    return None

                class_path = expected_class.lower()

                if action == "get":
                    try:
                        value = getattr(device, name)
                    except AttributeError:
                        param = next((p for p in device.parameters if p.name.lower() == name.lower()), None)
                        if param is None:
                            self.logger.error("Property %s not found on %s" % (name, expected_class))
                            return None
                        value = param.value
                    return (track_index, device_index, value)

                elif action == "set":
                    value = params[2]
                    try:
                        setattr(device, name, value)
                    except AttributeError:
                        param = next((p for p in device.parameters if p.name.lower() == name.lower()), None)
                        if param is None:
                            self.logger.error("Property %s not found on %s" % (name, expected_class))
                            return None
                        param.value = value
                    return None

                elif action == "function":
                    try:
                        result = getattr(device, name)(*params[2:])
                        if result is not None:
                            return (track_index, device_index, result)
                    except AttributeError:
                        self.logger.error("Function %s not found on %s" % (name, expected_class))
                    return None

                elif action == "start_listen":
                    osc_address = "/live/device/%s/get/%s" % (class_path, name)
                    listener_key = ('class_property', expected_class, track_index, device_index, name)

                    try:
                        _ = getattr(device, name)
                        def get_value():
                            return getattr(device, name)
                        def add_fn(cb):
                            getattr(device, "add_%s_listener" % name)(cb)
                        def remove_fn(cb):
                            getattr(device, "remove_%s_listener" % name)(cb)
                    except AttributeError:
                        param = next((p for p in device.parameters if p.name.lower() == name.lower()), None)
                        if param is None:
                            self.logger.error("Property %s not found on %s" % (name, expected_class))
                            return None
                        def get_value(p=param):
                            return p.value
                        def add_fn(cb, p=param):
                            p.add_value_listener(cb)
                        def remove_fn(cb, p=param):
                            p.remove_value_listener(cb)

                    if listener_key in self._class_listeners:
                        old_fn, old_remove = self._class_listeners[listener_key]
                        try:
                            old_remove(old_fn)
                        except Exception as e:
                            self.logger.info("Exception removing old class listener: %s" % e)
                        del self._class_listeners[listener_key]

                    def property_changed_callback():
                        value = get_value()
                        self.osc_server.send(osc_address, (track_index, device_index, value))

                    add_fn(property_changed_callback)
                    self._class_listeners[listener_key] = (property_changed_callback, remove_fn)
                    property_changed_callback()
                    return None

                elif action == "stop_listen":
                    listener_key = ('class_property', expected_class, track_index, device_index, name)
                    if listener_key in self._class_listeners:
                        fn, remove_fn = self._class_listeners[listener_key]
                        try:
                            remove_fn(fn)
                        except Exception as e:
                            self.logger.info("Exception removing class listener: %s" % e)
                        del self._class_listeners[listener_key]
                    return None

                elif action == "introspect_properties":
                    props = DEVICE_REGISTRY[expected_class]["properties"]
                    return (track_index, device_index, *props)

                elif action == "introspect_functions":
                    fns = DEVICE_REGISTRY[expected_class]["functions"]
                    return (track_index, device_index, *fns)

            return callback

        for class_name, class_info in DEVICE_REGISTRY.items():
            class_path = class_name.lower()

            for prop in class_info["properties"]:
                self.osc_server.add_handler("/live/device/%s/get/%s" % (class_path, prop),
                    create_device_class_callback(class_name, "get", prop))
                self.osc_server.add_handler("/live/device/%s/set/%s" % (class_path, prop),
                    create_device_class_callback(class_name, "set", prop))
                self.osc_server.add_handler("/live/device/%s/start_listen/%s" % (class_path, prop),
                    create_device_class_callback(class_name, "start_listen", prop))
                self.osc_server.add_handler("/live/device/%s/stop_listen/%s" % (class_path, prop),
                    create_device_class_callback(class_name, "stop_listen", prop))

            for fn in class_info["functions"]:
                self.osc_server.add_handler("/live/device/%s/function/%s" % (class_path, fn),
                    create_device_class_callback(class_name, "function", fn))

            self.osc_server.add_handler("/live/device/%s/get/properties/name" % class_path,
                create_device_class_callback(class_name, "introspect_properties", None))
            self.osc_server.add_handler("/live/device/%s/get/functions/name" % class_path,
                create_device_class_callback(class_name, "introspect_functions", None))
