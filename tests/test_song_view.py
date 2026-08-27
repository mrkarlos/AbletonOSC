from . import client, wait_one_tick, TICK_DURATION

#--------------------------------------------------------------------------------
# Test song_view (full Song.View coverage, including the selection state also
# available -- for backward compatibility -- under legacy /live/view/*) features
#--------------------------------------------------------------------------------

def test_draw_mode_get_set(client):
    original = client.query("/live/song_view/get/draw_mode")[0]
    try:
        client.send_message("/live/song_view/set/draw_mode", (1,))
        wait_one_tick()
        assert client.query("/live/song_view/get/draw_mode") == (1,)
        client.send_message("/live/song_view/set/draw_mode", (0,))
        wait_one_tick()
        assert client.query("/live/song_view/get/draw_mode") == (0,)
    finally:
        client.send_message("/live/song_view/set/draw_mode", (original,))
        wait_one_tick()

def test_follow_song_get_set(client):
    original = client.query("/live/song_view/get/follow_song")[0]
    try:
        client.send_message("/live/song_view/set/follow_song", (1,))
        wait_one_tick()
        assert client.query("/live/song_view/get/follow_song") == (1,)
        client.send_message("/live/song_view/set/follow_song", (0,))
        wait_one_tick()
        assert client.query("/live/song_view/get/follow_song") == (0,)
    finally:
        client.send_message("/live/song_view/set/follow_song", (original,))
        wait_one_tick()

def test_detail_clip_no_clip(client):
    # (-1, -1) as input to set/detail_clip is a documented no-op (Live's API has no
    # supported way to explicitly clear detail_clip) -- this just confirms the get side
    # reports (-1, -1) when nothing has ever set a detail clip in this session.
    client.send_message("/live/song_view/set/detail_clip", (-1, -1))
    wait_one_tick()
    assert client.query("/live/song_view/get/detail_clip") == (-1, -1)

def test_detail_clip_get_set(client):
    client.send_message("/live/clip_slot/create_clip", [0, 0, 8.0])
    wait_one_tick()
    try:
        client.send_message("/live/song_view/set/detail_clip", (0, 0))
        wait_one_tick()
        assert client.query("/live/song_view/get/detail_clip") == (0, 0)
    finally:
        # set/detail_clip (-1, -1) is a no-op (see test_detail_clip_no_clip) -- deleting
        # the clip below is what actually resets detail_clip back to (-1, -1).
        client.send_message("/live/song_view/set/detail_clip", (-1, -1))
        client.send_message("/live/track/delete_clip", [0, 0])
        wait_one_tick()

def test_detail_clip_listen(client):
    client.send_message("/live/clip_slot/create_clip", [0, 0, 8.0])
    wait_one_tick()
    try:
        client.send_message("/live/song_view/start_listen/detail_clip")
        # Drain the immediate registration-time push before triggering the real change,
        # so the await_message below can't race against it (same fix as
        # test_application_view.py's test_focused_document_view_listen).
        client.await_message("/live/song_view/get/detail_clip", TICK_DURATION * 2)
        client.send_message("/live/song_view/set/detail_clip", (0, 0))
        assert client.await_message("/live/song_view/get/detail_clip", TICK_DURATION * 2) == (0, 0)
        client.send_message("/live/song_view/stop_listen/detail_clip")
    finally:
        # set/detail_clip (-1, -1) is a no-op (see test_detail_clip_no_clip) -- deleting
        # the clip below is what actually resets detail_clip back to (-1, -1).
        client.send_message("/live/song_view/set/detail_clip", (-1, -1))
        client.send_message("/live/track/delete_clip", [0, 0])
        wait_one_tick()

def test_highlighted_clip_slot_get_set(client):
    client.send_message("/live/song_view/set/highlighted_clip_slot", (1, 1))
    wait_one_tick()
    assert client.query("/live/song_view/get/highlighted_clip_slot") == (1, 1)

#--------------------------------------------------------------------------------
# selected_scene/selected_track/selected_clip/selected_device: full parity with
# /live/view/*'s equivalents (test_view.py), reimplemented under /live/song_view/* --
# see song_view.py for why this duplication is deliberate.
#--------------------------------------------------------------------------------

def test_selected_scene(client):
    client.send_message("/live/song_view/set/selected_scene", (1,))
    assert client.query("/live/song_view/get/selected_scene") == (1,)

def test_selected_track(client):
    client.send_message("/live/song_view/set/selected_track", (2,))
    assert client.query("/live/song_view/get/selected_track") == (2,)

def test_selected_clip(client):
    client.send_message("/live/song_view/set/selected_clip", (3, 4))
    assert client.query("/live/song_view/get/selected_clip") == (3, 4)

def test_selected_device_no_device_selected(client):
    # Track 1 has no devices, so nothing can be selected on it.
    client.send_message("/live/song_view/set/selected_track", (1,))
    wait_one_tick()
    assert client.query("/live/song_view/get/selected_device") == (1, -1)

def test_selected_clip_listen(client):
    client.send_message("/live/song_view/set/selected_track", (0,))
    client.send_message("/live/song_view/set/selected_scene", (0,))
    wait_one_tick()

    client.send_message("/live/song_view/start_listen/selected_clip")
    assert client.await_message("/live/song_view/get/selected_clip", TICK_DURATION * 2) == (0, 0)

    client.send_message("/live/song_view/set/selected_track", (1,))
    assert client.await_message("/live/song_view/get/selected_clip", TICK_DURATION * 2) == (1, 0)

    client.send_message("/live/song_view/set/selected_scene", (1,))
    assert client.await_message("/live/song_view/get/selected_clip", TICK_DURATION * 2) == (1, 1)

    client.send_message("/live/song_view/stop_listen/selected_clip")

def test_selected_device_listen(client):
    client.send_message("/live/song_view/set/selected_track", (0,))
    client.send_message("/live/song_view/set/selected_device", (0, 0))
    wait_one_tick()

    client.send_message("/live/song_view/start_listen/selected_device")
    assert client.await_message("/live/song_view/get/selected_device", TICK_DURATION * 2) == (0, 0)

    client.send_message("/live/song_view/set/selected_track", (1,))
    assert client.await_message("/live/song_view/get/selected_device", TICK_DURATION * 2) == (1, -1)

    client.send_message("/live/song_view/stop_listen/selected_device")
