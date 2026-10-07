"""Expected process checks."""

from __future__ import annotations

from typing import Any

import psutil

from monitor.health import CheckResult, HealthStatus


def check_process(target: dict[str, Any]) -> CheckResult:
    expected = target["process_name"]
    matches: list[dict[str, Any]] = []
    for process in psutil.process_iter(("pid", "name")):
        try:
            if process.info["name"] == expected:
                matches.append({"pid": process.info["pid"], "name": process.info["name"]})
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    if matches:
        return CheckResult(
            target["name"],
            HealthStatus.HEALTHY,
            f"Running ({len(matches)})",
            {"process_name": expected, "running": True, "matches": matches},
        )
    return CheckResult(
        target["name"],
        HealthStatus.CRITICAL,
        "Not running",
        {"process_name": expected, "running": False, "matches": []},
        [
            f"Observed: no running process matched the exact name '{expected}'.",
            "Suggested investigation: verify the service state, configured process name, and service logs.",
        ],
    )


def collect_process_checks(targets: list[dict[str, Any]]) -> list[CheckResult]:
    return [check_process(target) for target in targets]
