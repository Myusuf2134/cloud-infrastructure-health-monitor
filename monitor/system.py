"""Local host system metric collection."""

from __future__ import annotations

import os
import time
from typing import Any

import psutil

from monitor.health import CheckResult, HealthStatus, classify_threshold


def bytes_to_gib(value: int) -> float:
    return value / (1024**3)


def format_uptime(seconds: float) -> str:
    total_minutes = max(0, int(seconds // 60))
    days, remaining = divmod(total_minutes, 24 * 60)
    hours, minutes = divmod(remaining, 60)
    return f"{days}d {hours:02d}h {minutes:02d}m"


def _utilization_result(
    name: str,
    value: float,
    limits: dict[str, Any],
    extra: dict[str, Any] | None = None,
) -> CheckResult:
    status = classify_threshold(value, limits["warning"], limits["critical"])
    details = {
        "utilization_percent": round(value, 1),
        "warning_threshold": limits["warning"],
        "critical_threshold": limits["critical"],
    }
    details.update(extra or {})
    return CheckResult(name, status, f"{value:.1f}%", details)


def check_cpu(limits: dict[str, Any]) -> CheckResult:
    return _utilization_result("CPU Utilization", psutil.cpu_percent(interval=0.1), limits)


def check_memory(limits: dict[str, Any]) -> CheckResult:
    memory = psutil.virtual_memory()
    available_gib = bytes_to_gib(memory.available)
    return _utilization_result(
        "Memory Utilization",
        memory.percent,
        limits,
        {"available_gib": round(available_gib, 2)},
    )


def check_disk(limits: dict[str, Any], path: str = "/") -> CheckResult:
    disk = psutil.disk_usage(path)
    available_gib = bytes_to_gib(disk.free)
    return _utilization_result(
        "Disk Utilization",
        disk.percent,
        limits,
        {"path": path, "available_gib": round(available_gib, 2)},
    )


def check_uptime() -> CheckResult:
    try:
        seconds = max(0.0, time.time() - psutil.boot_time())
    except (OSError, psutil.Error) as exc:
        return CheckResult(
            "System Uptime",
            HealthStatus.UNKNOWN,
            "Unavailable",
            {"error": str(exc)},
            ["Observed: the operating system did not permit reading the boot time."],
        )
    return CheckResult(
        "System Uptime",
        HealthStatus.HEALTHY,
        format_uptime(seconds),
        {"seconds": round(seconds)},
    )


def check_load_average() -> CheckResult:
    if not hasattr(os, "getloadavg"):
        return CheckResult(
            "Load Average",
            HealthStatus.UNKNOWN,
            "Not supported",
            {"supported": False},
        )
    one, five, fifteen = os.getloadavg()
    return CheckResult(
        "Load Average",
        HealthStatus.HEALTHY,
        f"{one:.2f} / {five:.2f} / {fifteen:.2f}",
        {"1_minute": one, "5_minutes": five, "15_minutes": fifteen, "supported": True},
    )


def collect_system_metrics(thresholds: dict[str, Any]) -> list[CheckResult]:
    """Collect all local host metrics."""

    return [
        check_cpu(thresholds["cpu"]),
        check_memory(thresholds["memory"]),
        check_disk(thresholds["disk"]),
        check_uptime(),
        check_load_average(),
    ]
