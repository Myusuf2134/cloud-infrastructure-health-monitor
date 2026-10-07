"""Health status types and aggregation helpers."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import IntEnum
from typing import Any


class HealthStatus(IntEnum):
    """Ordered health states; higher values represent greater severity."""

    HEALTHY = 0
    UNKNOWN = 1
    WARNING = 2
    CRITICAL = 3


@dataclass
class CheckResult:
    """A normalized result from any monitor check."""

    name: str
    status: HealthStatus
    summary: str
    details: dict[str, Any] = field(default_factory=dict)
    diagnostics: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["status"] = self.status.name
        return payload


def classify_threshold(value: float, warning: float, critical: float) -> HealthStatus:
    """Classify a utilization value against inclusive warning/critical limits."""

    if value >= critical:
        return HealthStatus.CRITICAL
    if value >= warning:
        return HealthStatus.WARNING
    return HealthStatus.HEALTHY


def overall_status(results: list[CheckResult]) -> HealthStatus:
    """Return the most severe result, or UNKNOWN when no checks ran."""

    if not results:
        return HealthStatus.UNKNOWN
    return max(result.status for result in results)
