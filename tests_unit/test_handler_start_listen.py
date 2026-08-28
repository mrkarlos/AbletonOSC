import logging

from ..abletonosc.handler import AbletonOSCHandler


class _FakeOSCServer:
    def __init__(self):
        self.sent = []

    def send(self, address, params):
        self.sent.append((address, params))


class _FakeManager:
    def __init__(self):
        self.osc_server = _FakeOSCServer()


class _NoListenerTarget:
    """
    Stands in for a Live object whose property has no native listener at all --
    e.g. Clip.length, which has no add_length_listener (see
    _TRACK_DATA_CLIP_PROPERTIES_WITHOUT_LISTENER in song.py).
    """
    length = 4.0


class _ListenableTarget:
    def __init__(self):
        self.name = "clip"
        self._name_listeners = []

    def add_name_listener(self, callback):
        self._name_listeners.append(callback)

    def remove_name_listener(self, callback):
        self._name_listeners.remove(callback)


def _make_handler() -> AbletonOSCHandler:
    handler = AbletonOSCHandler(_FakeManager())
    handler.class_identifier = "clip"
    return handler


def test_start_listen_on_non_observable_property_warns_and_does_not_raise(caplog):
    handler = _make_handler()

    with caplog.at_level(logging.WARNING, logger="abletonosc"):
        handler._start_listen(_NoListenerTarget(), "length", (1, 0))

    assert ("length", (1, 0)) not in handler.listener_functions
    assert ("length", (1, 0)) not in handler.listener_objects
    assert not handler.osc_server.sent
    assert any(record.levelno == logging.WARNING for record in caplog.records)


def test_start_listen_on_non_observable_property_does_not_block_sibling_listener(caplog):
    #--------------------------------------------------------------------------------
    # Regression for the bug reported against /live/song/start_listen/track_data:
    # a failed listener registration for one property (e.g. clip.length) must not
    # prevent a caller from successfully registering a sibling property (e.g.
    # clip.name) on the same object in a subsequent call.
    #--------------------------------------------------------------------------------
    handler = _make_handler()

    with caplog.at_level(logging.WARNING, logger="abletonosc"):
        handler._start_listen(_NoListenerTarget(), "length", (1, 0))

    target = _ListenableTarget()
    handler._start_listen(target, "name", (1, 0))

    assert ("name", (1, 0)) in handler.listener_functions
    assert handler.listener_objects[("name", (1, 0))] is target
    assert handler.osc_server.sent == [("/live/clip/get/name", (1, 0, "clip"))]
