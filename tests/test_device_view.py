from . import client, wait_one_tick, TICK_DURATION

#--------------------------------------------------------------------------------
# Test device_view (Device.View) features
#--------------------------------------------------------------------------------
# Track 0/device 0 is a Looper, per the fixed test song shape (TESTING.md).
#--------------------------------------------------------------------------------

def test_is_collapsed_get_set(client):
    original = client.query("/live/device_view/get/is_collapsed", (0, 0))[2]
    try:
        client.send_message("/live/device_view/set/is_collapsed", (0, 0, 1))
        wait_one_tick()
        assert client.query("/live/device_view/get/is_collapsed", (0, 0)) == (0, 0, 1)
        client.send_message("/live/device_view/set/is_collapsed", (0, 0, 0))
        wait_one_tick()
        assert client.query("/live/device_view/get/is_collapsed", (0, 0)) == (0, 0, 0)
    finally:
        client.send_message("/live/device_view/set/is_collapsed", (0, 0, original))
        wait_one_tick()

def test_is_collapsed_listen(client):
    original = client.query("/live/device_view/get/is_collapsed", (0, 0))[2]
    try:
        client.send_message("/live/device_view/start_listen/is_collapsed", (0, 0))
        # Drain the immediate registration-time push before triggering the real change, so
        # the await_message below can't race against it (see test_application_view.py's
        # test_focused_document_view_listen for the same fix).
        client.await_message("/live/device_view/get/is_collapsed", TICK_DURATION * 2)
        client.send_message("/live/device_view/set/is_collapsed", (0, 0, 1))
        assert client.await_message("/live/device_view/get/is_collapsed", TICK_DURATION * 2) == (0, 0, 1)
        client.send_message("/live/device_view/stop_listen/is_collapsed", (0, 0))
    finally:
        client.send_message("/live/device_view/set/is_collapsed", (0, 0, original))
        wait_one_tick()
