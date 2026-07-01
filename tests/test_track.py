from . import client, wait_one_tick, TICK_DURATION
import pytest
import itertools
import threading

#--------------------------------------------------------------------------------
# Test track properties
#--------------------------------------------------------------------------------

def _test_track_property(client, track_id, property, values):
    for value in values:
        print("Testing property %s, value: %s" % (property, value))
        client.send_message("/live/track/set/%s" % property, [track_id, value])
        wait_one_tick()
        assert client.query("/live/track/get/%s" % property, [track_id]) == (track_id, value,)

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

    for value in [0.5, 0.0]:
        client.send_message("/live/track/set/send", [track_id, send_id, value])
        wait_one_tick()
        assert client.query("/live/track/get/send", (track_id, send_id)) == (track_id, send_id, value,)

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
    expect((0, -2,))  # start listen sends a -1 response, which is weird I think

    client.send_message("/live/track/start_listen/playing_slot_index", (1,))
    expect((1, -2,))  # start listen sends a -1 response, which is weird I think

    client.send_message("/live/clip_slot/fire", (0, 0))
    expect((0, 0,))

    client.send_message("/live/clip_slot/fire", (0, 2))
    expect((0, -2,))

    client.send_message("/live/clip_slot/fire", (1, 2))
    expect((1, -2,))

    client.send_message("/live/clip_slot/fire", (1, 0))
    expect((1, 0,))

    client.remove_handler("/live/track/get/playing_slot_index")
    client.send_message("/live/track/stop_listen/playing_slot_index", (0,))
    client.send_message("/live/track/stop_listen/playing_slot_index", (1,))

    for track_id, clip_id in itertools.product((0, 1), (0, 1)):
        client.send_message("/live/clip_slot/delete_clip", (track_id, clip_id))
