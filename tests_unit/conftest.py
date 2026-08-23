import sys
import types

#--------------------------------------------------------------------------------
# abletonosc/__init__.py eagerly imports every handler module (application.py,
# song.py, clip.py, ...), and a few of those do `import Live` at module level —
# Ableton's embedded API, only available inside the Live process. Stub it out
# so `abletonosc` (and anything under it, e.g. abletonosc.osc_server) can be
# imported here without Live running. None of those modules touch `Live.*` at
# import time, so an empty stub module is sufficient.
#--------------------------------------------------------------------------------
if "Live" not in sys.modules:
    sys.modules["Live"] = types.ModuleType("Live")

#--------------------------------------------------------------------------------
# abletonosc/handler.py subclasses ableton.v2.control_surface.component.Component,
# which is part of Live's bundled "ableton" framework package, also only present
# inside the Live process. It's only used as a base class at class-definition
# time (never instantiated here), so a bare stand-in class is sufficient.
#--------------------------------------------------------------------------------
def _stub_module(dotted_name: str) -> types.ModuleType:
    if dotted_name in sys.modules:
        return sys.modules[dotted_name]
    module = types.ModuleType(dotted_name)
    sys.modules[dotted_name] = module
    if "." in dotted_name:
        parent_name, attr = dotted_name.rsplit(".", 1)
        setattr(_stub_module(parent_name), attr, module)
    return module


_component_module = _stub_module("ableton.v2.control_surface.component")
if not hasattr(_component_module, "Component"):
    _component_module.Component = type("Component", (object,), {})
