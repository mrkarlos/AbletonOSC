import pytest
from . import client, wait_one_tick, TICK_DURATION

#--------------------------------------------------------------------------------
# Test clip_view (Clip.View) features
#--------------------------------------------------------------------------------
#
# Track 0 has no clip loaded by default (a Looper *device* lives at track 0/device 0,
# per TESTING.md's fixed song shape, but that says nothing about clip_slots). Create
# and delete a clip around each test, same as test_clip.py's note-editing tests do.
#--------------------------------------------------------------------------------

@pytest.fixture
def clip(client):
    client.send_message("/live/clip_slot/create_clip", [0, 0, 8.0])
    wait_one_tick()
    yield (0, 0)
    client.send_message("/live/track/delete_clip", [0, 0])
    wait_one_tick()

def test_grid_quantization_get_set(client, clip):
    track_id, clip_id = clip
    original = client.query("/live/clip_view/get/grid_quantization", (track_id, clip_id))[2]
    try:
        client.send_message("/live/clip_view/set/grid_quantization", (track_id, clip_id, 4))
        wait_one_tick()
        assert client.query("/live/clip_view/get/grid_quantization", (track_id, clip_id)) == (track_id, clip_id, 4)
    finally:
        client.send_message("/live/clip_view/set/grid_quantization", (track_id, clip_id, original))
        wait_one_tick()

def test_grid_is_triplet_get_set(client, clip):
    track_id, clip_id = clip
    client.send_message("/live/clip_view/set/grid_is_triplet", (track_id, clip_id, 1))
    wait_one_tick()
    assert client.query("/live/clip_view/get/grid_is_triplet", (track_id, clip_id)) == (track_id, clip_id, 1)
    client.send_message("/live/clip_view/set/grid_is_triplet", (track_id, clip_id, 0))
    wait_one_tick()
    assert client.query("/live/clip_view/get/grid_is_triplet", (track_id, clip_id)) == (track_id, clip_id, 0)

def test_show_hide_envelope_and_loop(client, clip):
    track_id, clip_id = clip
    # These are fire-and-forget UI methods with no query-able reply; just confirm they
    # don't raise/error over OSC.
    client.send_message("/live/clip_view/show_envelope", (track_id, clip_id))
    wait_one_tick()
    client.send_message("/live/clip_view/hide_envelope", (track_id, clip_id))
    wait_one_tick()
    client.send_message("/live/clip_view/show_loop", (track_id, clip_id))
    wait_one_tick()
