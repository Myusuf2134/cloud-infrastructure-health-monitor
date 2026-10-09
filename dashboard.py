#!/usr/bin/env python3
"""Local web dashboard for the Cloud Infrastructure Health Monitor."""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, render_template, request

from main import collect_checks
from monitor.config import ConfigError, load_config
from monitor.logging_config import log_result, setup_logging
from monitor.output import report_payload


def create_app(config_path: str | Path = "config.yaml") -> Flask:
    app = Flask(__name__)
    app.config["MONITOR_CONFIG_PATH"] = str(config_path)
    logger = setup_logging()

    @app.get("/")
    def dashboard():
        return render_template("dashboard.html")

    @app.get("/api/health")
    def api_health():
        section = request.args.get("section")
        allowed_sections = {"system", "network", "services", "processes"}
        if section and section not in allowed_sections:
            return jsonify({"error": f"Unknown section: {section}"}), 400
        try:
            config = load_config(app.config["MONITOR_CONFIG_PATH"])
            sections = collect_checks(config, section)
            for section_name, results in sections.items():
                for result in results:
                    log_result(logger, section_name, result)
            payload = report_payload(sections, datetime.now().astimezone())
            payload["refresh_interval_seconds"] = config["monitoring"]["interval_seconds"]
            return jsonify(payload)
        except ConfigError as exc:
            logger.error("Dashboard configuration error: %s", exc)
            return jsonify({"error": str(exc)}), 500
        except Exception as exc:  # Keep the dashboard available if collection fails unexpectedly.
            logger.exception("Unexpected dashboard collection failure")
            return jsonify({"error": f"Health collection failed: {exc}"}), 500

    @app.get("/api/config")
    def api_config():
        try:
            config = load_config(app.config["MONITOR_CONFIG_PATH"])
        except ConfigError as exc:
            return jsonify({"error": str(exc)}), 500
        return jsonify(
            {
                "refresh_interval_seconds": config["monitoring"]["interval_seconds"],
                "network_checks": len(config.get("network_checks", [])),
                "service_checks": len(config.get("http_checks", [])),
                "process_checks": len(config.get("process_checks", [])),
                "thresholds": config["thresholds"],
            }
        )

    return app


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the local infrastructure health dashboard.")
    parser.add_argument("--config", default="config.yaml", help="YAML configuration path")
    parser.add_argument("--host", default="127.0.0.1", help="Dashboard bind address")
    parser.add_argument("--port", type=int, default=5000, help="Dashboard port")
    parser.add_argument("--debug", action="store_true", help="Enable Flask development debugging")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    create_app(args.config).run(host=args.host, port=args.port, debug=args.debug)
