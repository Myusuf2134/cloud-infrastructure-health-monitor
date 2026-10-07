#!/usr/bin/env python3
"""Command-line entry point for the infrastructure health monitor."""

from __future__ import annotations

import argparse
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

from monitor.config import ConfigError, load_config
from monitor.diagnostics import enrich_diagnostics
from monitor.health import CheckResult, HealthStatus
from monitor.logging_config import log_result, setup_logging
from monitor.network import collect_network_checks
from monitor.output import render_json, render_terminal
from monitor.processes import collect_process_checks
from monitor.services import collect_http_checks
from monitor.system import collect_system_metrics


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Monitor local system, network, service, and process health."
    )
    parser.add_argument("--config", default="config.yaml", help="YAML config path (default: config.yaml)")
    parser.add_argument("--watch", action="store_true", help="Repeat checks at the configured interval")
    parser.add_argument("--json", action="store_true", dest="json_output", help="Print machine-readable JSON")
    parser.add_argument(
        "--section",
        choices=("system", "network", "services", "processes"),
        help="Run only one category of checks",
    )
    return parser.parse_args(argv)


def collect_checks(config: dict, section: str | None = None) -> dict[str, list[CheckResult]]:
    """Run the requested check categories."""

    collectors = {
        "system": lambda: collect_system_metrics(config["thresholds"]),
        "network": lambda: collect_network_checks(config.get("network_checks", [])),
        "services": lambda: collect_http_checks(config.get("http_checks", [])),
        "processes": lambda: collect_process_checks(config.get("process_checks", [])),
    }
    names = (section,) if section else tuple(collectors)
    sections: dict[str, list[CheckResult]] = {}
    for name in names:
        try:
            sections[name] = [enrich_diagnostics(result) for result in collectors[name]()]
        except Exception as exc:  # A single collector must not crash the monitoring run.
            logging.getLogger("cloud_health_monitor").exception("Unexpected %s collector failure", name)
            sections[name] = [
                CheckResult(
                    f"{name.title()} Checks",
                    HealthStatus.UNKNOWN,
                    "Unexpected error",
                    {"error": str(exc)},
                    [f"Observed: the {name} collector encountered an unexpected error."],
                )
            ]
    return sections


def run_once(config: dict, section: str | None, json_output: bool, logger: logging.Logger) -> None:
    sections = collect_checks(config, section)
    for section_name, results in sections.items():
        for result in results:
            log_result(logger, section_name, result)
    timestamp = datetime.now().astimezone()
    print(render_json(sections, timestamp) if json_output else render_terminal(sections, timestamp))


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    logger = setup_logging()
    try:
        config = load_config(Path(args.config))
    except ConfigError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 2

    try:
        while True:
            run_once(config, args.section, args.json_output, logger)
            if not args.watch:
                break
            time.sleep(config["monitoring"]["interval_seconds"])
    except KeyboardInterrupt:
        if not args.json_output:
            print("\nMonitoring stopped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
