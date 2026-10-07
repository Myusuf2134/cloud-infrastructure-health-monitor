"""HTTP and HTTPS service health checks."""

from __future__ import annotations

import time
from typing import Any, Protocol

import requests

from monitor.health import CheckResult, HealthStatus


class HTTPClient(Protocol):
    def get(self, url: str, *, timeout: float) -> Any: ...


def check_http(target: dict[str, Any], client: HTTPClient = requests) -> CheckResult:
    name = target["name"]
    url = target["url"]
    expected = target.get("expected_status", 200)
    timeout = float(target.get("timeout_seconds", 5))
    started = time.perf_counter()
    try:
        response = client.get(url, timeout=timeout)
        elapsed_ms = (time.perf_counter() - started) * 1000
        healthy = response.status_code == expected
        if healthy:
            status = HealthStatus.HEALTHY
        elif response.status_code >= 500:
            status = HealthStatus.CRITICAL
        else:
            status = HealthStatus.WARNING
        diagnostics = [] if healthy else [
            f"Observed: {url} returned HTTP {response.status_code}; expected {expected}.",
            "Possible causes: application error, route/configuration mismatch, or upstream dependency issue.",
        ]
        return CheckResult(
            name,
            status,
            f"{response.status_code} / {elapsed_ms:.0f} ms",
            {
                "url": url,
                "reachable": True,
                "healthy": healthy,
                "status_code": response.status_code,
                "expected_status": expected,
                "response_time_ms": round(elapsed_ms, 2),
            },
            diagnostics,
        )
    except requests.RequestException as exc:
        elapsed_ms = (time.perf_counter() - started) * 1000
        return CheckResult(
            name,
            HealthStatus.CRITICAL,
            "Request failed",
            {
                "url": url,
                "reachable": False,
                "healthy": False,
                "response_time_ms": round(elapsed_ms, 2),
                "error": str(exc),
            },
            [
                f"Observed: HTTP request to {url} failed: {exc}.",
                "Possible causes: DNS, TCP/TLS connectivity, proxy configuration, or service availability.",
            ],
        )


def collect_http_checks(targets: list[dict[str, Any]]) -> list[CheckResult]:
    return [check_http(target) for target in targets]
