"""Optional, deterministic incident context for operators or future LLM consumers."""

from __future__ import annotations

from typing import Any

from monitor.health import CheckResult, HealthStatus


def build_incident_context(results: list[CheckResult]) -> dict[str, Any]:
    """Convert failed checks into structured, advisory investigation context."""

    failed = [result for result in results if result.status >= HealthStatus.WARNING]
    return {
        "observed": [
            {"check": result.name, "status": result.status.name, "summary": result.summary}
            for result in failed
        ],
        "investigation_guidance": [
            diagnostic
            for result in failed
            for diagnostic in result.diagnostics
            if diagnostic.startswith(("Possible causes:", "Suggested investigation:"))
        ],
        "advisory": "Investigation guidance is advisory and must be verified against system evidence.",
    }


class IncidentContextConsumer:
    """Interface for an optional future local or external analysis provider."""

    def analyze(self, context: dict[str, Any]) -> str:
        raise NotImplementedError
