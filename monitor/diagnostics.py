"""Deterministic operational diagnostics for failed checks."""

from __future__ import annotations

from monitor.health import CheckResult, HealthStatus


def enrich_diagnostics(result: CheckResult) -> CheckResult:
    """Add factual, check-specific investigation guidance."""

    if result.status < HealthStatus.WARNING:
        return result
    if result.name == "Disk Utilization":
        utilization = result.details.get("utilization_percent")
        critical = result.details.get("critical_threshold")
        available = result.details.get("available_gib")
        result.diagnostics.extend(
            [
                f"Observed: disk utilization is {utilization}% (critical threshold: {critical}%).",
                f"Available space: {available} GiB.",
                "Suggested investigation: inspect large directories, logs, temporary files, and log rotation.",
            ]
        )
    elif result.name == "Memory Utilization":
        result.diagnostics.append(
            "Suggested investigation: inspect memory-heavy processes and recent workload changes."
        )
    elif result.name == "CPU Utilization":
        result.diagnostics.append(
            "Suggested investigation: inspect CPU-heavy processes and sustained load patterns."
        )
    return result
