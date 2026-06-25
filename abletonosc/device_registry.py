DEVICE_REGISTRY = {
    "Looper": {
        # Direct LOM properties on the device object (accessed via getattr/setattr).
        # observable=True: register start/stop_listen handlers via add_<name>_listener.
        # access "r" = get + listen only; "rw" = also set.
        "properties": {
            "loop_length":          {"access": "r",  "observable": True},
            "overdub_after_record": {"access": "rw", "observable": True},
            "record_length_index":  {"access": "rw", "observable": True},
            "record_length_list":   {"access": "r",  "observable": False},
            "tempo":                {"access": "r",  "observable": True},
        },
        # Items in device.parameters (automation-capable controls).
        # Looked up by name, case-insensitive. Always observable via param.add_value_listener.
        # access "r" = get only; "rw" = also set via param.value.
        "parameters": {
            "state": {"access": "rw"},  # param name "State"; 0=Stop 1=Record 2=Play 3=Overdub
        },
        # Methods callable directly on the device object.
        "functions": [
            "clear", "double_speed", "half_speed", "double_length", "half_length",
            "record", "overdub", "play", "stop", "undo",
        ],
    },
}
