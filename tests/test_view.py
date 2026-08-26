from . import client, wait_one_tick, TICK_DURATION

#--------------------------------------------------------------------------------
# Test view features
#--------------------------------------------------------------------------------

def test_selected_scene(client):
    client.send_message("/live/view/set/selected_scene", (1, ))
    rv = client.query("/live/view/get/selected_scene")
    assert rv == (1, )

def test_selected_track(client):
    client.send_message("/live/view/set/selected_track", (2, ))
    rv = client.query("/live/view/get/selected_track")
    assert rv == (2, )

def test_selected_clip(client):
    client.send_message("/live/view/set/selected_clip", (3, 4))
    rv = client.query("/live/view/get/selected_clip")
    assert rv == (3, 4)

def test_selected_device_no_device_selected(client):
    # Track 1 has no devices, so nothing can be selected on it.
    client.send_message("/live/view/set/selected_track", (1,))
    wait_one_tick()
    assert client.query("/live/view/get/selected_device") == (1, -1)

#--------------------------------------------------------------------------------
# Test view listeners
#--------------------------------------------------------------------------------

def test_selected_clip_listen(client):
    #--------------------------------------------------------------------------------
    # selected_clip isn't a real Live property -- it's derived from selected_track and
    # selected_scene together, so this also verifies that a change to *either* one
    # triggers a push.
    #--------------------------------------------------------------------------------
    client.send_message("/live/view/set/selected_track", (0,))
    client.send_message("/live/view/set/selected_scene", (0,))
    wait_one_tick()

    client.send_message("/live/view/start_listen/selected_clip")
    assert client.await_message("/live/view/get/selected_clip", TICK_DURATION * 2) == (0, 0)

    client.send_message("/live/view/set/selected_track", (1,))
    assert client.await_message("/live/view/get/selected_clip", TICK_DURATION * 2) == (1, 0)

    client.send_message("/live/view/set/selected_scene", (1,))
    assert client.await_message("/live/view/get/selected_clip", TICK_DURATION * 2) == (1, 1)

    client.send_message("/live/view/stop_listen/selected_clip")

def test_selected_device_listen(client):
    #--------------------------------------------------------------------------------
    # selected_device lives on the currently selected track's .view, so this also
    # verifies that switching to a different track re-attaches the listener there
    # (track 1 has no devices, exercising the -1 "nothing selected" case too).
    #--------------------------------------------------------------------------------
    client.send_message("/live/view/set/selected_track", (0,))
    client.send_message("/live/view/set/selected_device", (0, 0))
    wait_one_tick()

    client.send_message("/live/view/start_listen/selected_device")
    assert client.await_message("/live/view/get/selected_device", TICK_DURATION * 2) == (0, 0)

    client.send_message("/live/view/set/selected_track", (1,))
    assert client.await_message("/live/view/get/selected_device", TICK_DURATION * 2) == (1, -1)

    client.send_message("/live/view/stop_listen/selected_device")