from . import client, wait_one_tick, TICK_DURATION

#--------------------------------------------------------------------------------
# Test song_view (Song.View, excluding legacy /live/view/* selection state) features
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
