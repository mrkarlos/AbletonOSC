from . import client, wait_one_tick, TICK_DURATION
import pytest
import itertools
import threading

#--------------------------------------------------------------------------------
# Test track properties
#--------------------------------------------------------------------------------

def _test_track_property(client, track_id, property, values):
    #--------------------------------------------------------------------------------
    # Restore the pre-test value afterwards, so running the suite repeatedly against
    # the same loaded Set doesn't leave track properties (name, color, ...) drifted
    # from run to run.
    #--------------------------------------------------------------------------------
    original_value = client.query("/live/track/get/%s" % property, [track_id])[1]
    try:
        for value in values:
            print("Testing property %s, value: %s" % (property, value))
            client.send_message("/live/track/set/%s" % property, [track_id, value])
            wait_one_tick()
            assert client.query("/live/track/get/%s" % property, [track_id]) == (track_id, value,)
    finally:
        client.send_message("/live/track/set/%s" % property, [track_id, original_value])
        wait_one_tick()

def test_track_property_panning(client):
    _test_track_property(client, 2, "panning", [0.5, 0.0])

def test_track_property_volume(client):
    _test_track_property(client, 2, "volume", [0.5, 1.0])

def test_track_property_color(client):
    # Only specific colors from the color picker can be used
    _test_track_property(client, 2, "color", [0x001AFF2F, 0x001A2F96])

def test_track_property_mute(client):
    _test_track_property(client, 2, "mute", [1, 0])

def test_track_property_solo(client):
    _test_track_property(client, 2, "solo", [1, 0])

def test_track_property_name(client):
    _test_track_property(client, 2, "name", ["Test", "Track"])

#--------------------------------------------------------------------------------
# Test track properties - sends
#--------------------------------------------------------------------------------

def test_track_get_send(client):
    track_id = 2
    send_id = 1

    original_value = client.query("/live/track/get/send", (track_id, send_id))[2]
    try:
        for value in [0.5, 0.0]:
            client.send_message("/live/track/set/send", [track_id, send_id, value])
            wait_one_tick()
            assert client.query("/live/track/get/send", (track_id, send_id)) == (track_id, send_id, value,)
    finally:
        client.send_message("/live/track/set/send", [track_id, send_id, original_value])
        wait_one_tick()

#--------------------------------------------------------------------------------
# Test track properties - clips
#--------------------------------------------------------------------------------

def test_track_clips(client):
    track_id = 1
    client.send_message("/live/clip_slot/create_clip", (track_id, 0, 4))
    client.send_message("/live/clip_slot/create_clip", (track_id, 1, 2))
    client.send_message("/live/clip/set/name", (track_id, 0, "Alpha"))
    client.send_message("/live/clip/set/name", (track_id, 1, "Beta"))

    wait_one_tick()
    assert client.query("/live/track/get/clips/name", (track_id,)) == (track_id,
                                                                       "Alpha", "Beta", None, None,
                                                                       None, None, None, None)
    assert client.query("/live/track/get/clips/length", (track_id,)) == (track_id,
                                                                         4, 2, None, None,
                                                                         None, None, None, None)

    client.send_message("/live/clip_slot/delete_clip", (track_id, 0))
    client.send_message("/live/clip_slot/delete_clip", (track_id, 1))

#--------------------------------------------------------------------------------
# Test track properties - devices
#--------------------------------------------------------------------------------

def test_track_devices(client):
    track_id = 1
    assert client.query("/live/track/get/num_devices", (track_id,)) == (track_id, 0,)

#--------------------------------------------------------------------------------
# Test track properties - listeners
#--------------------------------------------------------------------------------

def test_track_listen_playing_slot_index(client):
    client.verbose = True
    # 1/16th quantize
    original_quantization = client.query("/live/song/get/clip_trigger_quantization")[0]
    client.send_message("/live/song/set/clip_trigger_quantization", (11,))
    for track_id, clip_id in itertools.product((0, 1), (0, 1)):
        client.send_message("/live/clip_slot/create_clip", (track_id, clip_id, 4))

    last_received = {}
    event = threading.Event()

    def capture(address, params):
        last_received['params'] = params
        event.set()

    client.set_handler("/live/track/get/playing_slot_index", capture)

    def expect(expected):
        fired = event.wait(TICK_DURATION * 4)
        event.clear()
        assert fired, "No update received on /live/track/get/playing_slot_index"
        rv = last_received['params']
        assert rv == expected

    client.send_message("/live/track/start_listen/playing_slot_index", (0,))
    expect((0, -1,))  # -1 = nothing playing/queued yet

    client.send_message("/live/track/start_listen/playing_slot_index", (1,))
    expect((1, -1,))  # -1 = nothing playing/queued yet

    client.send_message("/live/clip_slot/fire", (0, 0))
    expect((0, 0,))

    # Firing an empty clip slot just reports that slot's own (positive) index -- it does
    # not queue a "stop" (-2). -2 is specific to the dedicated Stop Clip control, exposed
    # as Track.stop_all_clips() / /live/track/stop_all_clips.
    client.send_message("/live/track/stop_all_clips", (0,))
    expect((0, -2,))

    client.send_message("/live/clip_slot/fire", (1, 0))
    expect((1, 0,))

    client.send_message("/live/track/stop_all_clips", (1,))
    expect((1, -2,))

    client.remove_handler("/live/track/get/playing_slot_index")
    client.send_message("/live/track/stop_listen/playing_slot_index", (0,))
    client.send_message("/live/track/stop_listen/playing_slot_index", (1,))

    for track_id, clip_id in itertools.product((0, 1), (0, 1)):
        client.send_message("/live/clip_slot/delete_clip", (track_id, clip_id))

    client.send_message("/live/song/set/clip_trigger_quantization", (original_quantization,))

#--------------------------------------------------------------------------------
# Test track properties - Group tracks
#--------------------------------------------------------------------------------

def test_track_listen_arm_group_track_graceful(client):
    """
    Group tracks (like Master/Return tracks) have no Arm state. Live raises a
    RuntimeError from add_arm_listener/remove_arm_listener when queried on one
    ("Main and Return Tracks have no 'Arm' state!" -- the same message Live uses
    for any track without an Arm state, not just literal Master/Return tracks).

    This should be handled gracefully -- logged and skipped -- rather than raise
    an unhandled exception that reaches osc_server's generic error handler.
    See track.py's track_callback.
    """
    group_track_id = 4

    assert client.query("/live/track/get/can_be_armed", (group_track_id,)) == (group_track_id, False)

    # get/arm is already handled gracefully by the generic _get_property, which catches
    # RuntimeError and returns None.
    assert client.query("/live/track/get/arm", (group_track_id,)) == (group_track_id, None)

    # start_listen/arm must not crash the OSC server, and must not register a listener
    # (since the underlying add_arm_listener call raises).
    client.send_message("/live/track/start_listen/arm", (group_track_id,))
    wait_one_tick()

    # The server should still be alive and responsive to further queries.
    rv = client.query("/live/track/get/name", (group_track_id,))
    assert rv[0] == group_track_id and isinstance(rv[1], str)

    client.send_message("/live/track/stop_listen/arm", (group_track_id,))
