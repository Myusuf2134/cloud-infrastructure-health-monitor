"""YAML configuration loading and validation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


class ConfigError(ValueError):
    """Raised when configuration cannot be read or validated."""


def _require_mapping(value: Any, location: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ConfigError(f"'{location}' must be a mapping.")
    return value


def _number(value: Any, location: str, minimum: float = 0) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ConfigError(f"'{location}' must be a number.")
    if value < minimum:
        raise ConfigError(f"'{location}' must be at least {minimum}.")
    return float(value)


def _validate_thresholds(config: dict[str, Any]) -> None:
    thresholds = _require_mapping(config.get("thresholds"), "thresholds")
    for resource in ("cpu", "memory", "disk"):
        limits = _require_mapping(thresholds.get(resource), f"thresholds.{resource}")
        warning = _number(limits.get("warning"), f"thresholds.{resource}.warning")
        critical = _number(limits.get("critical"), f"thresholds.{resource}.critical")
        if warning > 100 or critical > 100:
            raise ConfigError(f"Thresholds for '{resource}' cannot exceed 100.")
        if warning >= critical:
            raise ConfigError(
                f"'{resource}' warning threshold must be lower than critical threshold."
            )


def _validate_checks(config: dict[str, Any]) -> None:
    for section in ("network_checks", "http_checks", "process_checks"):
        checks = config.get(section, [])
        if not isinstance(checks, list):
            raise ConfigError(f"'{section}' must be a list.")
        for index, check in enumerate(checks):
            if not isinstance(check, dict):
                raise ConfigError(f"'{section}[{index}]' must be a mapping.")
            if not isinstance(check.get("name"), str) or not check["name"].strip():
                raise ConfigError(f"'{section}[{index}].name' must be a non-empty string.")

    for index, check in enumerate(config.get("network_checks", [])):
        if not isinstance(check.get("host"), str) or not check["host"].strip():
            raise ConfigError(f"'network_checks[{index}].host' must be a non-empty string.")
        port = check.get("port")
        if isinstance(port, bool) or not isinstance(port, int) or not 1 <= port <= 65535:
            raise ConfigError(f"'network_checks[{index}].port' must be between 1 and 65535.")
        if "timeout_seconds" in check:
            _number(check["timeout_seconds"], f"network_checks[{index}].timeout_seconds", 0.1)

    for index, check in enumerate(config.get("http_checks", [])):
        url = check.get("url")
        if not isinstance(url, str) or not url.startswith(("http://", "https://")):
            raise ConfigError(f"'http_checks[{index}].url' must use http:// or https://.")
        expected = check.get("expected_status", 200)
        if isinstance(expected, bool) or not isinstance(expected, int) or not 100 <= expected <= 599:
            raise ConfigError(f"'http_checks[{index}].expected_status' must be 100-599.")
        if "timeout_seconds" in check:
            _number(check["timeout_seconds"], f"http_checks[{index}].timeout_seconds", 0.1)

    for index, check in enumerate(config.get("process_checks", [])):
        process_name = check.get("process_name")
        if not isinstance(process_name, str) or not process_name.strip():
            raise ConfigError(
                f"'process_checks[{index}].process_name' must be a non-empty string."
            )


def validate_config(config: Any) -> dict[str, Any]:
    root = _require_mapping(config, "configuration")
    monitoring = _require_mapping(root.get("monitoring"), "monitoring")
    interval = _number(monitoring.get("interval_seconds"), "monitoring.interval_seconds", 1)
    monitoring["interval_seconds"] = interval
    _validate_thresholds(root)
    _validate_checks(root)
    return root


def load_config(path: str | Path) -> dict[str, Any]:
    config_path = Path(path)
    try:
        with config_path.open(encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
    except FileNotFoundError as exc:
        raise ConfigError(f"Configuration file not found: {config_path}") from exc
    except PermissionError as exc:
        raise ConfigError(f"Cannot read configuration file: {config_path}") from exc
    except yaml.YAMLError as exc:
        raise ConfigError(f"Invalid YAML in {config_path}: {exc}") from exc
    return validate_config(data)
