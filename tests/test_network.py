import socket

from monitor.health import HealthStatus
from monitor.network import check_tcp


TARGET = {"name": "Test TCP", "host": "service.test", "port": 443, "timeout_seconds": 1}


class FakeSocket:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None


def test_successful_tcp_check(monkeypatch) -> None:
    monkeypatch.setattr(
        "monitor.network.socket.getaddrinfo",
        lambda *args, **kwargs: [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("192.0.2.1", 443))],
    )
    monkeypatch.setattr("monitor.network.socket.create_connection", lambda *args, **kwargs: FakeSocket())
    result = check_tcp(TARGET)
    assert result.status == HealthStatus.HEALTHY
    assert result.details["reachable"] is True


def test_failed_tcp_check(monkeypatch) -> None:
    monkeypatch.setattr("monitor.network.socket.getaddrinfo", lambda *args, **kwargs: [(1, 2, 3, "", ("x", 1))])

    def fail(*args, **kwargs):
        raise socket.timeout("timed out")

    monkeypatch.setattr("monitor.network.socket.create_connection", fail)
    result = check_tcp(TARGET)
    assert result.status == HealthStatus.CRITICAL
    assert result.details["reachable"] is False
    assert "timed out" in result.summary.lower()
