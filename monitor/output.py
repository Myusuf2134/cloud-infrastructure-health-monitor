"""Terminal and JSON output rendering."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from monitor.health import CheckResult, overall_status


def report_payload(sections: dict[str, list[CheckResult]], timestamp: datetime) -> dict[str, Any]:
    results = [result for values in sections.values() for result in values]
    return {
        "timestamp": timestamp.isoformat(timespec="seconds"),
        "overall_status": overall_status(results).name,
        "sections": {
            name: [result.to_dict() for result in values]
            for name, values in sections.items()
        },
    }


def render_json(sections: dict[str, list[CheckResult]], timestamp: datetime) -> str:
    return json.dumps(report_payload(sections, timestamp), indent=2)


def render_terminal(sections: dict[str, list[CheckResult]], timestamp: datetime) -> str:
    results = [result for values in sections.values() for result in values]
    lines = [
        "=" * 60,
        "           CLOUD INFRASTRUCTURE HEALTH MONITOR",
        "=" * 60,
    ]
    for section, values in sections.items():
        lines.extend(["", section.upper()])
        if not values:
            lines.append("No checks configured.")
        for result in values:
            lines.append(f"{result.name:<24} {result.summary:<20} {result.status.name}")
            for diagnostic in result.diagnostics:
                lines.append(f"  - {diagnostic}")
    lines.extend(
        [
            "",
            "-" * 60,
            f"OVERALL STATUS: {overall_status(results).name}",
            "-" * 60,
            f"Timestamp: {timestamp.isoformat(timespec='seconds')}",
        ]
    )
    return "\n".join(lines)
