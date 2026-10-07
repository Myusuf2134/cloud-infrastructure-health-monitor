#!/usr/bin/env python3
"""Command-line entry point for the infrastructure health monitor."""

from __future__ import annotations

import argparse
import sys
import time
from datetime import datetime
from pathlib import Path

from monitor.config import ConfigError, load_config
from monitor.output import render_json, render_terminal


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


def collect_checks(config: dict, section: str | None = None) -> dict:
    """Collect requested checks. Check implementations are added by later modules."""

    names = (section,) if section else ("system", "network", "services", "processes")
    return {name: [] for name in names}


def run_once(config: dict, section: str | None, json_output: bool) -> None:
    sections = collect_checks(config, section)
    timestamp = datetime.now().astimezone()
    print(render_json(sections, timestamp) if json_output else render_terminal(sections, timestamp))


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        config = load_config(Path(args.config))
    except ConfigError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 2

    try:
        while True:
            run_once(config, args.section, args.json_output)
            if not args.watch:
                break
            time.sleep(config["monitoring"]["interval_seconds"])
    except KeyboardInterrupt:
        if not args.json_output:
            print("\nMonitoring stopped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
