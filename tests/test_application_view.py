from . import client, wait_one_tick, TICK_DURATION

#--------------------------------------------------------------------------------
# Test application_view (Application.View) features
#--------------------------------------------------------------------------------

def test_available_main_views(client):
    rv = client.query("/live/application_view/get/available_main_views")
    assert "Session" in rv
    assert "Arranger" in rv

def test_focused_document_view_get(client):
    rv = client.query("/live/application_view/get/focused_document_view")
    assert rv[0] in ("Session", "Arranger")

def test_show_focus_is_view_visible(client):
    original = client.query("/live/application_view/get/focused_document_view")[0]
    try:
        client.send_message("/live/application_view/focus_view", ("Session",))
        wait_one_tick()
        assert client.query("/live/application_view/get/is_view_visible", ("Session",)) == (True,)
    finally:
        client.send_message("/live/application_view/focus_view", (original,))
        wait_one_tick()

def test_focused_document_view_listen(client):
    original = client.query("/live/application_view/get/focused_document_view")[0]
    other = "Arranger" if original == "Session" else "Session"
    try:
        client.send_message("/live/application_view/start_listen/focused_document_view")
        #--------------------------------------------------------------------------------
        # start_listen immediately pushes the current value -- drain that first so the
        # await_message below can only match the push triggered by focus_view, not race
        # against the registration-time push.
        #--------------------------------------------------------------------------------
        client.await_message("/live/application_view/get/focused_document_view", TICK_DURATION * 2)
        client.send_message("/live/application_view/focus_view", (other,))
        assert client.await_message("/live/application_view/get/focused_document_view",
                                    TICK_DURATION * 2) == (other,)
        client.send_message("/live/application_view/stop_listen/focused_document_view")
    finally:
        client.send_message("/live/application_view/focus_view", (original,))
        wait_one_tick()
