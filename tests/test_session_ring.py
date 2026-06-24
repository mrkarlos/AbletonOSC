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

# ---------------------------------------------------------------------------
# Follow selected cell
# ---------------------------------------------------------------------------

def test_follow_scene_moves_ring_when_outside_bounds(client):
    client.send_message("/live/session_ring/follow/off", ())
    client.send_message("/live/session_ring/on", (2, 2))
    client.send_message("/live/session_ring/set/position", (0, 0))
    wait_one_tick()

    client.send_message("/live/session_ring/follow/on", ())
    wait_one_tick()

    # Select scene index 2 — outside ring [0, 2)
    client.send_message("/live/view/set/selected_scene", (2,))
    wait_one_tick()

    pos = client.query("/live/session_ring/get/position", ())
    assert pos[1] == 2, "Ring scene offset should align to selected scene"

    client.send_message("/live/session_ring/follow/off", ())
    wait_one_tick()

def test_follow_track_moves_ring_when_outside_bounds(client):
    client.send_message("/live/session_ring/follow/off", ())
    client.send_message("/live/session_ring/on", (2, 2))
    client.send_message("/live/session_ring/set/position", (0, 0))
    wait_one_tick()

    client.send_message("/live/session_ring/follow/on", ())
    wait_one_tick()

    # Select track index 2 — outside ring [0, 2)
    client.send_message("/live/view/set/selected_track", (2,))
    wait_one_tick()

    pos = client.query("/live/session_ring/get/position", ())
    assert pos[0] == 2, "Ring track offset should align to selected track"

    client.send_message("/live/session_ring/follow/off", ())
    wait_one_tick()

def test_follow_does_not_move_ring_when_inside_bounds(client):
    client.send_message("/live/session_ring/follow/off", ())
    client.send_message("/live/session_ring/on", (2, 2))
    client.send_message("/live/session_ring/set/position", (0, 0))
    wait_one_tick()

    client.send_message("/live/session_ring/follow/on", ())
    wait_one_tick()

    # Select scene 1 — inside ring [0, 2), ring should stay at 0
    client.send_message("/live/view/set/selected_scene", (1,))
    wait_one_tick()
    pos = client.query("/live/session_ring/get/position", ())
    assert pos[1] == 0, "Ring should not move when selection is inside bounds"

    # Select track 1 — inside ring [0, 2), ring should stay at 0
    client.send_message("/live/view/set/selected_track", (1,))
    wait_one_tick()
    pos = client.query("/live/session_ring/get/position", ())
    assert pos[0] == 0, "Ring should not move when selection is inside bounds"

    client.send_message("/live/session_ring/follow/off", ())
    wait_one_tick()

def test_follow_persists_after_ring_rebuild(client):
    client.send_message("/live/session_ring/follow/off", ())
    client.send_message("/live/session_ring/on", (2, 2))
    client.send_message("/live/session_ring/set/position", (0, 0))
    wait_one_tick()

    client.send_message("/live/session_ring/follow/on", ())
    wait_one_tick()

    # Rebuild ring with different dimensions
    client.send_message("/live/session_ring/on", (3, 3))
    wait_one_tick()
    client.send_message("/live/session_ring/set/position", (0, 0))
    wait_one_tick()

    # Select scene outside new ring [0, 3)
    client.send_message("/live/view/set/selected_scene", (3,))
    wait_one_tick()

    pos = client.query("/live/session_ring/get/position", ())
    assert pos[1] == 3, "Follow mode should persist after ring rebuild"

    client.send_message("/live/session_ring/follow/off", ())
    wait_one_tick()

# ---------------------------------------------------------------------------
# Page up / page down
# ---------------------------------------------------------------------------

def test_page_down(client):
    client.send_message("/live/session_ring/follow/off", ())
    client.send_message("/live/session_ring/on", (2, 2))
    client.send_message("/live/session_ring/set/position", (0, 0))
    client.send_message("/live/session_ring/set/page_size", (2,))
    wait_one_tick()

    client.send_message("/live/session_ring/page_down", ())
    wait_one_tick()

    pos = client.query("/live/session_ring/get/position", ())
    assert pos[1] == 2, "Page down should advance scene offset by page_size"

def test_page_up(client):
    client.send_message("/live/session_ring/follow/off", ())
    client.send_message("/live/session_ring/on", (2, 2))
    client.send_message("/live/session_ring/set/position", (0, 4))
    client.send_message("/live/session_ring/set/page_size", (2,))
    wait_one_tick()

    client.send_message("/live/session_ring/page_up", ())
    wait_one_tick()

    pos = client.query("/live/session_ring/get/position", ())
    assert pos[1] == 2, "Page up should retreat scene offset by page_size"

def test_page_down_clamps_at_end(client):
    client.send_message("/live/session_ring/follow/off", ())
    client.send_message("/live/session_ring/on", (2, 2))
    client.send_message("/live/session_ring/set/page_size", (999,))
    client.send_message("/live/session_ring/set/position", (0, 0))
    wait_one_tick()

    client.send_message("/live/session_ring/page_down", ())
    wait_one_tick()
    pos1 = client.query("/live/session_ring/get/position", ())

    # A second page down should not advance further (already at max)
    client.send_message("/live/session_ring/page_down", ())
    wait_one_tick()
    pos2 = client.query("/live/session_ring/get/position", ())

    assert pos1 == pos2, "Repeated page down should not move past the end"
    assert pos1[1] >= 0

def test_page_up_clamps_at_start(client):
    client.send_message("/live/session_ring/follow/off", ())
    client.send_message("/live/session_ring/on", (2, 2))
    client.send_message("/live/session_ring/set/position", (0, 0))
    client.send_message("/live/session_ring/set/page_size", (999,))
    wait_one_tick()

    client.send_message("/live/session_ring/page_up", ())
    wait_one_tick()

    pos = client.query("/live/session_ring/get/position", ())
    assert pos[1] == 0, "Page up from start should clamp to 0"

def test_get_set_page_size(client):
    client.send_message("/live/session_ring/set/page_size", (4,))
    wait_one_tick()

    size = client.query("/live/session_ring/get/page_size", ())
    assert size == (4,), "Page size should be retrievable after setting"

    # Restore default
    client.send_message("/live/session_ring/set/page_size", (8,))
    wait_one_tick()
