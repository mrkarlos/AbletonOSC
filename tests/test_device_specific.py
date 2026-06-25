from . import client, wait_one_tick, TICK_DURATION
import pytest

LOOPER_TRACK = 0
LOOPER_DEVICE = 0

#--------------------------------------------------------------------------------
# Generic: is_active
#--------------------------------------------------------------------------------

def test_is_active_get(client):
    rv = client.query("/live/device/get/is_active", [LOOPER_TRACK, LOOPER_DEVICE])
    assert rv[:2] == (LOOPER_TRACK, LOOPER_DEVICE)
    assert rv[2] in (0, 1, True, False)


#--------------------------------------------------------------------------------
# Looper: state (parameter)
#--------------------------------------------------------------------------------

def test_looper_get_state(client):
    rv = client.query("/live/device/looper/get/state", [LOOPER_TRACK, LOOPER_DEVICE])
    assert rv[:2] == (LOOPER_TRACK, LOOPER_DEVICE)
    assert rv[2] in (0.0, 1.0, 2.0, 3.0)

def test_looper_set_and_get_state(client):
    client.send_message("/live/device/looper/set/state", [LOOPER_TRACK, LOOPER_DEVICE, 0])
    wait_one_tick()
    rv = client.query("/live/device/looper/get/state", [LOOPER_TRACK, LOOPER_DEVICE])
    assert rv[2] == 0.0

def test_looper_listen_state(client):
    client.send_message("/live/device/looper/start_listen/state", [LOOPER_TRACK, LOOPER_DEVICE])
    msg = client.await_message("/live/device/looper/get/state", TICK_DURATION * 2)
    assert msg[:2] == (LOOPER_TRACK, LOOPER_DEVICE)
    assert msg[2] in (0.0, 1.0, 2.0, 3.0)

def test_looper_stop_listen_state(client):
    client.send_message("/live/device/looper/stop_listen/state", [LOOPER_TRACK, LOOPER_DEVICE])
    wait_one_tick()

#--------------------------------------------------------------------------------
# Looper: properties (direct LOM attributes)
#--------------------------------------------------------------------------------

def test_looper_get_loop_length(client):
    rv = client.query("/live/device/looper/get/loop_length", [LOOPER_TRACK, LOOPER_DEVICE])
    assert rv[:2] == (LOOPER_TRACK, LOOPER_DEVICE)
    assert isinstance(rv[2], float)

def test_looper_get_tempo(client):
    rv = client.query("/live/device/looper/get/tempo", [LOOPER_TRACK, LOOPER_DEVICE])
    assert rv[:2] == (LOOPER_TRACK, LOOPER_DEVICE)
    assert isinstance(rv[2], float)

def test_looper_get_record_length_list(client):
    # Returns (track_id, device_id, str, str, ...) — StringVector unpacked into OSC args
    rv = client.query("/live/device/looper/get/record_length_list", [LOOPER_TRACK, LOOPER_DEVICE])
    assert rv[:2] == (LOOPER_TRACK, LOOPER_DEVICE)
    assert len(rv) > 2  # at least one entry

def test_looper_get_record_length_index(client):
    rv = client.query("/live/device/looper/get/record_length_index", [LOOPER_TRACK, LOOPER_DEVICE])
    assert rv[:2] == (LOOPER_TRACK, LOOPER_DEVICE)
    assert isinstance(rv[2], int)

def test_looper_set_record_length_index(client):
    original = client.query("/live/device/looper/get/record_length_index", [LOOPER_TRACK, LOOPER_DEVICE])[2]
    target = 0 if original != 0 else 1
    client.send_message("/live/device/looper/set/record_length_index", [LOOPER_TRACK, LOOPER_DEVICE, target])
    wait_one_tick()
    rv = client.query("/live/device/looper/get/record_length_index", [LOOPER_TRACK, LOOPER_DEVICE])
    assert rv[2] == target
    # Restore
    client.send_message("/live/device/looper/set/record_length_index", [LOOPER_TRACK, LOOPER_DEVICE, original])

def test_looper_get_overdub_after_record(client):
    rv = client.query("/live/device/looper/get/overdub_after_record", [LOOPER_TRACK, LOOPER_DEVICE])
    assert rv[:2] == (LOOPER_TRACK, LOOPER_DEVICE)
    assert rv[2] in (0, 1, True, False)

def test_looper_set_overdub_after_record(client):
    original = client.query("/live/device/looper/get/overdub_after_record", [LOOPER_TRACK, LOOPER_DEVICE])[2]
    target = 0 if original else 1
    client.send_message("/live/device/looper/set/overdub_after_record", [LOOPER_TRACK, LOOPER_DEVICE, target])
    wait_one_tick()
    rv = client.query("/live/device/looper/get/overdub_after_record", [LOOPER_TRACK, LOOPER_DEVICE])
    assert rv[2] in (target, bool(target))
    # Restore
    client.send_message("/live/device/looper/set/overdub_after_record", [LOOPER_TRACK, LOOPER_DEVICE, original])

def test_looper_listen_loop_length(client):
    client.send_message("/live/device/looper/start_listen/loop_length", [LOOPER_TRACK, LOOPER_DEVICE])
    msg = client.await_message("/live/device/looper/get/loop_length", TICK_DURATION * 2)
    assert msg[:2] == (LOOPER_TRACK, LOOPER_DEVICE)
    client.send_message("/live/device/looper/stop_listen/loop_length", [LOOPER_TRACK, LOOPER_DEVICE])

#--------------------------------------------------------------------------------
# Looper: functions (fire-and-forget; just assert no crash / no OSC error)
#--------------------------------------------------------------------------------

def test_looper_function_stop(client):
    client.send_message("/live/device/looper/function/stop", [LOOPER_TRACK, LOOPER_DEVICE])
    wait_one_tick()

def test_looper_function_record(client):
    client.send_message("/live/device/looper/function/record", [LOOPER_TRACK, LOOPER_DEVICE])
    wait_one_tick()

def test_looper_function_overdub(client):
    client.send_message("/live/device/looper/function/overdub", [LOOPER_TRACK, LOOPER_DEVICE])
    wait_one_tick()

def test_looper_function_play(client):
    client.send_message("/live/device/looper/function/play", [LOOPER_TRACK, LOOPER_DEVICE])
    wait_one_tick()

def test_looper_function_undo(client):
    client.send_message("/live/device/looper/function/undo", [LOOPER_TRACK, LOOPER_DEVICE])
    wait_one_tick()

def test_looper_function_clear(client):
    client.send_message("/live/device/looper/function/clear", [LOOPER_TRACK, LOOPER_DEVICE])
    wait_one_tick()

def test_looper_function_double_speed(client):
    client.send_message("/live/device/looper/function/double_speed", [LOOPER_TRACK, LOOPER_DEVICE])
    wait_one_tick()

def test_looper_function_half_speed(client):
    client.send_message("/live/device/looper/function/half_speed", [LOOPER_TRACK, LOOPER_DEVICE])
    wait_one_tick()

def test_looper_function_double_length(client):
    client.send_message("/live/device/looper/function/double_length", [LOOPER_TRACK, LOOPER_DEVICE])
    wait_one_tick()

def test_looper_function_half_length(client):
    client.send_message("/live/device/looper/function/half_length", [LOOPER_TRACK, LOOPER_DEVICE])
    wait_one_tick()

#--------------------------------------------------------------------------------
# Introspection
#--------------------------------------------------------------------------------

def test_introspect_properties(client):
    rv = client.query("/live/device/looper/get/properties/name", [LOOPER_TRACK, LOOPER_DEVICE])
    assert rv[:2] == (LOOPER_TRACK, LOOPER_DEVICE)
    assert "loop_length" in rv
    assert "overdub_after_record" in rv
    assert "record_length_index" in rv
    assert "record_length_list" in rv
    assert "tempo" in rv

def test_introspect_parameters(client):
    rv = client.query("/live/device/looper/get/parameters/name", [LOOPER_TRACK, LOOPER_DEVICE])
    assert rv[:2] == (LOOPER_TRACK, LOOPER_DEVICE)
    assert "state" in rv

def test_introspect_functions(client):
    rv = client.query("/live/device/looper/get/functions/name", [LOOPER_TRACK, LOOPER_DEVICE])
    assert rv[:2] == (LOOPER_TRACK, LOOPER_DEVICE)
    assert "undo" in rv
    assert "clear" in rv
    assert "record" in rv
    assert "double_speed" in rv
