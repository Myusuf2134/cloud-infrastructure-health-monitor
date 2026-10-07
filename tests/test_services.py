import requests

from monitor.health import HealthStatus
from monitor.services import check_http


TARGET = {
    "name": "Test API",
    "url": "https://service.test/health",
    "expected_status": 200,
    "timeout_seconds": 1,
}


class SuccessfulClient:
    @staticmethod
    def get(url, *, timeout):
        return type("Response", (), {"status_code": 200})()


class FailedClient:
    @staticmethod
    def get(url, *, timeout):
        raise requests.ConnectionError("connection refused")


def test_successful_http_health_check() -> None:
    result = check_http(TARGET, client=SuccessfulClient)
    assert result.status == HealthStatus.HEALTHY
    assert result.details["status_code"] == 200


def test_failed_http_health_check() -> None:
    result = check_http(TARGET, client=FailedClient)
    assert result.status == HealthStatus.CRITICAL
    assert result.details["reachable"] is False
    assert "connection refused" in result.details["error"]
