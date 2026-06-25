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

def test_is_active_set(client):
    client.send_message("/live/device/set/is_active", [LOOPER_TRACK, LOOPER_DEVICE, 1])
    wait_one_tick()
    rv = client.query("/live/device/get/is_active", [LOOPER_TRACK, LOOPER_DEVICE])
    assert rv[2] in (1, True)

#--------------------------------------------------------------------------------
# Looper: state property
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

def test_looper_stop_listen(client):
    client.send_message("/live/device/looper/stop_listen/state", [LOOPER_TRACK, LOOPER_DEVICE])
    wait_one_tick()

#--------------------------------------------------------------------------------
# Looper: functions
#--------------------------------------------------------------------------------

def test_looper_function_undo(client):
    client.send_message("/live/device/looper/function/undo", [LOOPER_TRACK, LOOPER_DEVICE])
    wait_one_tick()

def test_looper_function_clear(client):
    client.send_message("/live/device/looper/function/clear", [LOOPER_TRACK, LOOPER_DEVICE])
    wait_one_tick()

#--------------------------------------------------------------------------------
# Looper: introspection
#--------------------------------------------------------------------------------

def test_introspect_properties(client):
    rv = client.query("/live/device/looper/get/properties/name", [LOOPER_TRACK, LOOPER_DEVICE])
    assert rv[:2] == (LOOPER_TRACK, LOOPER_DEVICE)
    assert "state" in rv

def test_introspect_functions(client):
    rv = client.query("/live/device/looper/get/functions/name", [LOOPER_TRACK, LOOPER_DEVICE])
    assert rv[:2] == (LOOPER_TRACK, LOOPER_DEVICE)
    assert "undo" in rv
    assert "clear" in rv
