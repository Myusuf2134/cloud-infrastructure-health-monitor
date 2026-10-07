"""DNS and TCP connectivity checks."""

from __future__ import annotations

import socket
import time
from typing import Any

from monitor.health import CheckResult, HealthStatus


def check_tcp(target: dict[str, Any]) -> CheckResult:
    """Resolve a target and verify a TCP connection to its configured port."""

    name = target["name"]
    host = target["host"]
    port = target["port"]
    timeout = float(target.get("timeout_seconds", 2))
    started = time.perf_counter()
    try:
        resolution_started = time.perf_counter()
        address_info = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
        dns_ms = (time.perf_counter() - resolution_started) * 1000
        addresses = sorted({entry[4][0] for entry in address_info})
        with socket.create_connection((host, port), timeout=timeout):
            latency_ms = (time.perf_counter() - started) * 1000
        return CheckResult(
            name,
            HealthStatus.HEALTHY,
            f"{latency_ms:.0f} ms",
            {
                "host": host,
                "port": port,
                "reachable": True,
                "latency_ms": round(latency_ms, 2),
                "dns_resolution_ms": round(dns_ms, 2),
                "resolved_addresses": addresses,
            },
        )
    except socket.gaierror as exc:
        return CheckResult(
            name,
            HealthStatus.CRITICAL,
            "DNS resolution failed",
            {"host": host, "port": port, "reachable": False, "error": str(exc)},
            [
                f"Observed: DNS resolution for {host} failed.",
                "Possible causes: invalid hostname, DNS server failure, or unavailable network.",
            ],
        )
    except (TimeoutError, socket.timeout) as exc:
        return CheckResult(
            name,
            HealthStatus.CRITICAL,
            "Connection timed out",
            {"host": host, "port": port, "reachable": False, "error": str(exc)},
            [
                f"Observed: TCP connection to {host}:{port} timed out.",
                "Possible causes: destination unavailable, blocked port, or routing problem.",
            ],
        )
    except OSError as exc:
        return CheckResult(
            name,
            HealthStatus.CRITICAL,
            "Connection failed",
            {"host": host, "port": port, "reachable": False, "error": str(exc)},
            [
                f"Observed: TCP connection to {host}:{port} failed: {exc}.",
                "Possible causes: service unavailable, firewall rejection, or connectivity problem.",
            ],
        )


def collect_network_checks(targets: list[dict[str, Any]]) -> list[CheckResult]:
    return [check_tcp(target) for target in targets]
