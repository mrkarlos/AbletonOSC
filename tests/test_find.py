from . import client, wait_one_tick, TICK_DURATION

# The integration test suite's default set has a Looper device at (0, 0)
# (see LOOPER_TRACK/LOOPER_DEVICE in test_device_specific.py).
LOOPER_TRACK = 0
LOOPER_DEVICE = 0

#--------------------------------------------------------------------------------
# /live/song/find_tracks
#--------------------------------------------------------------------------------

def test_find_tracks_by_name(client):
    original_name = client.query("/live/track/get/name", [LOOPER_TRACK])[1]
    client.send_message("/live/track/set/name", [LOOPER_TRACK, "GuitarLooperTrack"])
    wait_one_tick()

    rv = client.query("/live/song/find_tracks", ["guitarlooper"])
    assert rv == (LOOPER_TRACK, "GuitarLooperTrack")

    client.send_message("/live/track/set/name", [LOOPER_TRACK, original_name])
    wait_one_tick()

def test_find_tracks_no_match(client):
    rv = client.query("/live/song/find_tracks", ["ThisTrackNameDoesNotExist"])
    assert rv == ()

#--------------------------------------------------------------------------------
# /live/track/find_devices
#--------------------------------------------------------------------------------

def test_track_find_devices_by_class_name(client):
    rv = client.query("/live/track/find_devices", [LOOPER_TRACK, "Looper"])
    assert rv[0] == LOOPER_TRACK
    assert LOOPER_DEVICE in rv[1:]

def test_track_find_devices_by_class_name_and_name_hint(client):
    # /live/device/set/name isn't exposed, so exercise the name_pattern filter against
    # the device's existing (default) name rather than renaming it.
    device_name = client.query("/live/device/get/name", [LOOPER_TRACK, LOOPER_DEVICE])[2]
    name_hint = device_name[:4].lower()

    rv = client.query("/live/track/find_devices", [LOOPER_TRACK, "Looper", name_hint])
    assert rv == (LOOPER_TRACK, LOOPER_DEVICE, device_name)

def test_track_find_devices_no_match(client):
    rv = client.query("/live/track/find_devices", [LOOPER_TRACK, "NoSuchDeviceClass"])
    assert rv == (LOOPER_TRACK,)

#--------------------------------------------------------------------------------
# /live/song/find_devices
#--------------------------------------------------------------------------------

def test_song_find_devices_by_class_name(client):
    rv = client.query("/live/song/find_devices", ["Looper"])
    assert len(rv) >= 4
    # Results are quads of (track_index, device_index, track_name, device_name)
    quads = [rv[i:i + 4] for i in range(0, len(rv), 4)]
    assert any(q[0] == LOOPER_TRACK and q[1] == LOOPER_DEVICE for q in quads)

def test_song_find_devices_with_track_and_device_name_hints(client):
    # /live/device/set/name isn't exposed, so exercise the device_name_pattern filter
    # against the device's existing (default) name rather than renaming it.
    original_track_name = client.query("/live/track/get/name", [LOOPER_TRACK])[1]
    device_name = client.query("/live/device/get/name", [LOOPER_TRACK, LOOPER_DEVICE])[2]
    device_name_hint = device_name[:4].lower()
    client.send_message("/live/track/set/name", [LOOPER_TRACK, "GuitarLooperTrack"])
    wait_one_tick()

    rv = client.query("/live/song/find_devices", ["Looper", "guitarlooper", device_name_hint])
    assert rv == (LOOPER_TRACK, LOOPER_DEVICE, "GuitarLooperTrack", device_name)

    client.send_message("/live/track/set/name", [LOOPER_TRACK, original_track_name])
    wait_one_tick()

def test_song_find_devices_no_match(client):
    rv = client.query("/live/song/find_devices", ["NoSuchDeviceClass"])
    assert rv == ()
