from . import client, wait_one_tick, TICK_DURATION
import pytest
import itertools


def test_session_ring_on_and_get_position(client):
    client.send_message("/live/session_ring/on", (4, 2))
    wait_one_tick()
    pos = client.query("/live/session_ring/get/position", ())
    assert len(pos) == 2
    assert pos[0] >= 0
    assert pos[1] >= 0

def test_session_ring_move_clamps_to_zero(client):
    client.send_message("/live/session_ring/on", (4, 2))
    wait_one_tick()

    client.send_message("/live/session_ring/set/position", (0, 0))
    wait_one_tick()

    client.send_message("/live/session_ring/move", (-999, -999))
    wait_one_tick()

    assert client.query("/live/session_ring/get/position", ()) == (0, 0)

def test_session_ring_resize_changes_reported_ranges(client):
    client.send_message("/live/session_ring/on", (4, 2))
    wait_one_tick()
    tracks = client.query("/live/session_ring/get/tracks", ())
    scenes = client.query("/live/session_ring/get/scenes", ())
    # tracks/scenes reply is just indexes, no leading IDs
    assert len(tracks) == 4
    assert len(scenes) == 2

    client.send_message("/live/session_ring/on", (2, 1))
    wait_one_tick()
    tracks = client.query("/live/session_ring/get/tracks", ())
    scenes = client.query("/live/session_ring/get/scenes", ())
    assert len(tracks) == 2
    assert len(scenes) == 1

def test_session_ring_position_listener_no_duplicates_after_resize(client):
    client.send_message("/live/session_ring/on", (2, 1))
    wait_one_tick()
    client.send_message("/live/session_ring/set/position", (0, 0))
    wait_one_tick()

    client.send_message("/live/session_ring/start_listen/position", ())
    # Trigger a change
    client.send_message("/live/session_ring/move", (0, 1))
    msg1 = client.await_message("/live/session_ring/get/position", TICK_DURATION * 2)
    assert len(msg1) == 2

    # Resize (forces ring rebuild)
    client.send_message("/live/session_ring/on", (3, 1))
    wait_one_tick()

    # Trigger another change
    client.send_message("/live/session_ring/move", (0, 1))
    msg2 = client.await_message("/live/session_ring/get/position", TICK_DURATION * 2)
    assert len(msg2) == 2

    # Assert there isn't a second (duplicate) position update arriving
    with pytest.raises(RuntimeError):
        client.await_message("/live/session_ring/get/position", TICK_DURATION * 1)

    client.send_message("/live/session_ring/stop_listen/position", ())

def test_session_ring_stop_listen_position(client):
    client.send_message("/live/session_ring/on", (2, 1))
    wait_one_tick()
    client.send_message("/live/session_ring/set/position", (0, 0))
    wait_one_tick()

    client.send_message("/live/session_ring/start_listen/position", ())
    client.send_message("/live/session_ring/move", (0, 1))
    client.await_message("/live/session_ring/get/position", TICK_DURATION * 2)

    client.send_message("/live/session_ring/stop_listen/position", ())
    client.send_message("/live/session_ring/move", (0, 1))

    with pytest.raises(RuntimeError):
        client.await_message("/live/session_ring/get/position", TICK_DURATION * 2)

def test_session_ring_off_is_idempotent(client):
    client.send_message("/live/session_ring/off", ())
    wait_one_tick()
    client.send_message("/live/session_ring/off", ())
    wait_one_tick()
