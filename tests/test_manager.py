import pytest

from . import client, TICK_DURATION

#--------------------------------------------------------------------------------
# /live/api/clear_listeners
#--------------------------------------------------------------------------------

def test_clear_listeners_removes_live_listener(client):
    """
    Clearing listeners should actually remove the underlying Live API listener, not
    just be a no-op -- confirmed by checking that a subsequent property change no
    longer pushes an unsolicited update.
    """
    client.send_message("/live/song/set/tempo", [120])
    client.send_message("/live/song/start_listen/tempo")
    assert client.await_message("/live/song/get/tempo", TICK_DURATION * 2) == (120,)

    client.send_message("/live/api/clear_listeners")

    client.send_message("/live/song/set/tempo", [130])
    with pytest.raises(RuntimeError):
        client.await_message("/live/song/get/tempo", TICK_DURATION * 2)

    # Restore tempo and leave no dangling listener for later tests.
    client.send_message("/live/song/set/tempo", [120])

def test_clear_listeners_preserves_osc_routing(client):
    """
    Unlike /live/api/reload (which also drops and rebuilds every registered OSC
    address), /live/api/clear_listeners must leave address routing intact -- a query
    sent immediately afterwards should still get a normal reply.
    """
    client.send_message("/live/api/clear_listeners")
    assert client.query("/live/song/get/tempo", timeout=TICK_DURATION * 2) is not None
