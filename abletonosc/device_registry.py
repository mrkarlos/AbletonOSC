DEVICE_REGISTRY = {
    "Looper": {
        "properties": ["state"],    # int: 0=Stop, 1=Record, 2=Play, 3=Overdub; LOM param "State"
        "functions": ["undo", "clear"],
    },
}
