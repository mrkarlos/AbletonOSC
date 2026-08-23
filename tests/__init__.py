import time
import pytest

#--------------------------------------------------------------------------------
# Add . to the path so that pythonosc can be imported, enabling unit testing
# without any external dependencies
#--------------------------------------------------------------------------------
import sys
sys.path.append(".")

from ..client import AbletonOSCClient, TICK_DURATION

# Live tick is 100ms. Wait for this long plus a short additional buffer.
TICK_DURATION = 0.125

@pytest.fixture(scope="module")
def client() -> AbletonOSCClient:
    client = AbletonOSCClient()
    client.verbose = True
    yield client
    client.stop()

def wait_one_tick():
    """
    Sleep for one Ableton Live tick (100ms).
    """
    time.sleep(TICK_DURATION)

def wait_two_ticks():
    """
    Sleep for two Ableton Live tick (100ms).
    """
    time.sleep(TICK_DURATION)
    time.sleep(TICK_DURATION)

c = AbletonOSCClient()
c.send_message("/live/api/reload")
c.stop()

def _check_environment():
    """
    Fail fast with a clear message if the test song doesn't match the prerequisites in
    TESTING.md, rather than letting an unprepped set surface as a wall of unrelated
    test failures/timeouts.

    Note this can only check what's visible over OSC (song/device shape). It can't verify
    Preferences > Record, Warp & Launch > Count-In, or the default audio input/output
    devices -- those aren't exposed via the Live API, so check them by hand per TESTING.md.
    """
    client = AbletonOSCClient()
    try:
        try:
            num_tracks = client.query("/live/song/get/num_tracks", timeout=3.0)[0]
        except RuntimeError:
            pytest.exit(
                "Could not reach AbletonOSC on 127.0.0.1:11000. Check that Live is running "
                "with a set loaded, and that AbletonOSC is selected as the Control Surface "
                "in Live's MIDI preferences (see TESTING.md).",
                returncode=1,
            )
            return

        if num_tracks != 4:
            pytest.exit(
                "Test song has %d track(s), expected 4. Load the blank default set described "
                "in TESTING.md before running the integration suite." % num_tracks,
                returncode=1,
            )

        try:
            device_class_name = client.query("/live/device/get/class_name", (0, 0), timeout=2.0)[2]
        except RuntimeError:
            device_class_name = None

        if device_class_name != "Looper":
            pytest.exit(
                "Expected a Looper device at track 0, device 0 (found %r instead). The "
                "device-specific and find_* integration tests assume this -- add a Looper "
                "there and re-save it as the default set (see TESTING.md)." % device_class_name,
                returncode=1,
            )
    finally:
        client.stop()

_check_environment()
