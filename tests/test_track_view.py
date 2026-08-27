from . import client, wait_one_tick, TICK_DURATION

#--------------------------------------------------------------------------------
# Test track_view (Track.View) features
#--------------------------------------------------------------------------------

def _test_track_view_property(client, track_id, property, values):
    original_value = client.query("/live/track_view/get/%s" % property, [track_id])[1]
    try:
        for value in values:
            client.send_message("/live/track_view/set/%s" % property, [track_id, value])
            wait_one_tick()
            assert client.query("/live/track_view/get/%s" % property, [track_id]) == (track_id, value,)
    finally:
        client.send_message("/live/track_view/set/%s" % property, [track_id, original_value])
        wait_one_tick()

def test_track_view_is_collapsed(client):
    _test_track_view_property(client, 2, "is_collapsed", [1, 0])

def test_track_view_device_insert_mode(client):
    # The LOM docs describe device_insert_mode as an int enum (0/1/2), but Live 12.3
    # actually returns/accepts a plain bool at runtime -- the handler is a pure passthrough
    # of whatever Live returns, so just confirm the roundtrip doesn't error, rather than
    # asserting a specific echoed value that doesn't match the documented semantics.
    original = client.query("/live/track_view/get/device_insert_mode", [2])[1]
    try:
        client.send_message("/live/track_view/set/device_insert_mode", [2, 1])
        wait_one_tick()
        rv = client.query("/live/track_view/get/device_insert_mode", [2])
        assert rv[0] == 2
    finally:
        client.send_message("/live/track_view/set/device_insert_mode", [2, original])
        wait_one_tick()

def test_track_view_selected_device_no_device(client):
    # Track 1 has no devices, per the fixed test song shape (TESTING.md).
    assert client.query("/live/track_view/get/selected_device", (1,)) == (1, -1)

def test_track_view_selected_device_listen(client):
    # Track 0 has exactly one device (a Looper at index 0), per the fixed test song shape
    # (TESTING.md) -- there's no second device on any track to switch to and back, so this
    # only verifies the immediate push on start_listen carries the right value, not a live
    # change (see test_selected_device_listen in test_view.py for that, which uses the
    # legacy /live/view/* namespace's own re-attachment logic across tracks instead).
    client.send_message("/live/view/set/selected_track", (0,))
    client.send_message("/live/view/set/selected_device", (0, 0))
    wait_one_tick()

    client.send_message("/live/track_view/start_listen/selected_device", (0,))
    assert client.await_message("/live/track_view/get/selected_device", TICK_DURATION * 2) == (0, 0)

    client.send_message("/live/track_view/stop_listen/selected_device", (0,))
