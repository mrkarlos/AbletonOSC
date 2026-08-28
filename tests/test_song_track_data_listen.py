from . import client, wait_one_tick, TICK_DURATION

#--------------------------------------------------------------------------------
# start_listen/stop_listen on track_data
#
# Track 2 (per TESTING.md's 7-track fixture Set) is an audio track -- create_clip
# only works on MIDI tracks, so clip-related tests here use track 1 instead (a regular
# MIDI track, matching the convention in tests/test_song.py). Track/scene-property-only
# tests (no clip creation) use tracks 2/3 to avoid clashing with other suites' use of
# tracks 0/1.
#--------------------------------------------------------------------------------

def test_track_data_listen_initial_snapshot(client):
    client.send_message("/live/song/start_listen/track_data", (2, 4, "track.name"))
    snapshot = client.await_message("/live/song/get/track_data", TICK_DURATION * 4)
    assert snapshot == client.query("/live/song/get/track_data", (2, 4, "track.name"))
    client.send_message("/live/song/stop_listen/track_data", (2, 4, "track.name"))

def test_track_data_listen_pushes_track_property(client):
    original_name = client.query("/live/track/get/name", (2,))[1]

    client.send_message("/live/song/start_listen/track_data", (2, 3, "track.name"))
    client.await_message("/live/song/get/track_data", TICK_DURATION * 4)

    client.send_message("/live/track/set/name", (2, "tmp_track_data_name"))
    assert client.await_message("/live/track/get/name", TICK_DURATION * 4) == (2, "tmp_track_data_name")

    client.send_message("/live/track/set/name", (2, original_name))
    wait_one_tick()
    client.send_message("/live/song/stop_listen/track_data", (2, 3, "track.name"))

def test_track_data_listen_pushes_clip_property(client):
    client.send_message("/live/clip_slot/create_clip", (1, 0, 4.0))
    wait_one_tick()

    client.send_message("/live/song/start_listen/track_data", (1, 2, "clip.name"))
    client.await_message("/live/song/get/track_data", TICK_DURATION * 4)

    client.send_message("/live/clip/set/name", (1, 0, "tmp_clip_name"))
    assert client.await_message("/live/clip/get/name", TICK_DURATION * 4) == (1, 0, "tmp_clip_name")

    client.send_message("/live/song/stop_listen/track_data", (1, 2, "clip.name"))
    client.send_message("/live/clip_slot/delete_clip", (1, 0))

def test_track_data_listen_union_merge(client):
    client.send_message("/live/song/start_listen/track_data", (2, 4, "track.name"))
    snapshot_a = client.await_message("/live/song/get/track_data", TICK_DURATION * 4)
    assert snapshot_a == client.query("/live/song/get/track_data", (2, 4, "track.name"))

    client.send_message("/live/song/start_listen/track_data", (3, 5, "track.color"))
    snapshot_b = client.await_message("/live/song/get/track_data", TICK_DURATION * 4)
    assert snapshot_b == client.query("/live/song/get/track_data", (3, 5, "track.color"))

    #--------------------------------------------------------------------------------
    # Track 3's track.name listener (from the first call) should still be active --
    # the second call must not have clobbered it.
    #--------------------------------------------------------------------------------
    original_name = client.query("/live/track/get/name", (3,))[1]
    client.send_message("/live/track/set/name", (3, "tmp_union_name"))
    assert client.await_message("/live/track/get/name", TICK_DURATION * 4) == (3, "tmp_union_name")
    client.send_message("/live/track/set/name", (3, original_name))
    wait_one_tick()

    client.send_message("/live/song/stop_listen/track_data", (2, 4, "track.name"))
    client.send_message("/live/song/stop_listen/track_data", (3, 5, "track.color"))

def test_track_data_stop_listen_hole_in_range(client):
    client.send_message("/live/song/start_listen/track_data", (0, 6, "track.name"))
    client.await_message("/live/song/get/track_data", TICK_DURATION * 4)

    #--------------------------------------------------------------------------------
    # Stop only tracks 2-3 (no properties given -- clears everything for those tracks),
    # leaving tracks either side still covered.
    #--------------------------------------------------------------------------------
    client.send_message("/live/song/stop_listen/track_data", (2, 4))
    wait_one_tick()

    original_name_1 = client.query("/live/track/get/name", (1,))[1]
    original_name_4 = client.query("/live/track/get/name", (4,))[1]
    original_name_2 = client.query("/live/track/get/name", (2,))[1]

    client.send_message("/live/track/set/name", (1, "tmp_hole_1"))
    assert client.await_message("/live/track/get/name", TICK_DURATION * 4) == (1, "tmp_hole_1")
    client.send_message("/live/track/set/name", (1, original_name_1))
    wait_one_tick()

    client.send_message("/live/track/set/name", (4, "tmp_hole_4"))
    assert client.await_message("/live/track/get/name", TICK_DURATION * 4) == (4, "tmp_hole_4")
    client.send_message("/live/track/set/name", (4, original_name_4))
    wait_one_tick()

    client.send_message("/live/track/set/name", (2, "tmp_hole_2"))
    try:
        client.await_message("/live/track/get/name", TICK_DURATION * 4)
        assert False, "Expected no push for track 2, which was explicitly stopped"
    except RuntimeError:
        pass
    client.send_message("/live/track/set/name", (2, original_name_2))
    wait_one_tick()

    client.send_message("/live/song/stop_listen/track_data", (0, 6))

def test_track_data_stop_listen_specific_property(client):
    client.send_message("/live/song/start_listen/track_data", (2, 3, "track.name", "track.color"))
    client.await_message("/live/song/get/track_data", TICK_DURATION * 4)

    client.send_message("/live/song/stop_listen/track_data", (2, 3, "track.name"))
    wait_one_tick()

    original_color = client.query("/live/track/get/color", (2,))[1]
    client.send_message("/live/track/set/color", (2, 0))
    assert client.await_message("/live/track/get/color", TICK_DURATION * 4) == (2, 0)
    client.send_message("/live/track/set/color", (2, original_color))
    wait_one_tick()

    original_name = client.query("/live/track/get/name", (2,))[1]
    client.send_message("/live/track/set/name", (2, "tmp_removed_prop"))
    try:
        client.await_message("/live/track/get/name", TICK_DURATION * 4)
        assert False, "Expected no push for track.name, which was explicitly stopped"
    except RuntimeError:
        pass
    client.send_message("/live/track/set/name", (2, original_name))
    wait_one_tick()

    client.send_message("/live/song/stop_listen/track_data", (2, 3, "track.color"))

def test_track_data_auto_rebuild_toggle(client):
    assert client.query("/live/song/get/track_data_auto_rebuild") == (True,)

    client.send_message("/live/song/set/track_data_auto_rebuild", (0,))
    assert client.query("/live/song/get/track_data_auto_rebuild") == (False,)

    client.send_message("/live/song/set/track_data_auto_rebuild", (1,))
    assert client.query("/live/song/get/track_data_auto_rebuild") == (True,)

def test_track_data_auto_rebuild_new_clip(client):
    #--------------------------------------------------------------------------------
    # Track 1, slot 1 starts empty. With auto-rebuild on (the default), watching
    # clip.name across a range that includes this empty slot, then creating a clip in
    # it, should surface a push with no further start_listen call.
    #--------------------------------------------------------------------------------
    client.send_message("/live/song/start_listen/track_data", (1, 2, "clip.name"))
    client.await_message("/live/song/get/track_data", TICK_DURATION * 4)

    client.send_message("/live/clip_slot/create_clip", (1, 1, 4.0))
    assert client.await_message("/live/clip/get/name", TICK_DURATION * 4)[:2] == (1, 1)

    client.send_message("/live/clip_slot/delete_clip", (1, 1))
    wait_one_tick()
    client.send_message("/live/song/stop_listen/track_data", (1, 2, "clip.name"))

def test_track_data_auto_rebuild_disabled_new_clip(client):
    client.send_message("/live/song/set/track_data_auto_rebuild", (0,))

    client.send_message("/live/song/start_listen/track_data", (1, 2, "clip.name"))
    client.await_message("/live/song/get/track_data", TICK_DURATION * 4)

    client.send_message("/live/clip_slot/create_clip", (1, 1, 4.0))
    try:
        client.await_message("/live/clip/get/name", TICK_DURATION * 4)
        assert False, "Expected no auto-rebuild push while track_data_auto_rebuild is disabled"
    except RuntimeError:
        pass

    client.send_message("/live/clip_slot/delete_clip", (1, 1))
    wait_one_tick()
    client.send_message("/live/song/stop_listen/track_data", (1, 2, "clip.name"))
    client.send_message("/live/song/set/track_data_auto_rebuild", (1,))
