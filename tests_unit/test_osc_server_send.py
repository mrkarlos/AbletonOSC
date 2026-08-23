import errno
import logging

from ..abletonosc.osc_server import OSCServer


class _FakeSocket:
    """
    Stands in for OSCServer._socket so sendto() can be made to raise
    arbitrary errors -- the real socket.socket type doesn't allow monkeypatching
    individual methods since it's a C-extension type.
    """
    def __init__(self, sendto_side_effect):
        self._sendto_side_effect = sendto_side_effect

    def sendto(self, *args, **kwargs):
        return self._sendto_side_effect(*args, **kwargs)


def _make_server() -> OSCServer:
    #--------------------------------------------------------------------------------
    # Bind to an ephemeral local port (0) so this never collides with a real
    # AbletonOSC instance listening on the default port 11000.
    #--------------------------------------------------------------------------------
    return OSCServer(local_addr=("127.0.0.1", 0), remote_addr=("127.0.0.1", 0))


def test_send_connection_reset_logged_as_warning(caplog, monkeypatch):
    server = _make_server()

    def raise_connection_reset(*args, **kwargs):
        raise ConnectionResetError(errno.ECONNRESET, "Connection reset by peer")

    monkeypatch.setattr(server, "_socket", _FakeSocket(raise_connection_reset))

    with caplog.at_level(logging.DEBUG, logger="abletonosc"):
        server.send("/live/test", (1, 2))

    assert not any(record.levelno == logging.ERROR for record in caplog.records)
    assert any(
        record.levelno == logging.WARNING and "Non-fatal socket send error" in record.getMessage()
        for record in caplog.records
    )


def test_send_other_socket_error_logged_as_error(caplog, monkeypatch):
    server = _make_server()

    def raise_permission_error(*args, **kwargs):
        raise OSError(errno.EACCES, "Permission denied")

    monkeypatch.setattr(server, "_socket", _FakeSocket(raise_permission_error))

    with caplog.at_level(logging.DEBUG, logger="abletonosc"):
        server.send("/live/test", (1, 2))

    assert any(
        record.levelno == logging.ERROR and "Socket send error" in record.getMessage()
        for record in caplog.records
    )
