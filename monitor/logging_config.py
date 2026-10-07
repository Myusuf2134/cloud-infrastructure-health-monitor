"""Application logging configuration."""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from monitor.health import CheckResult, HealthStatus


def setup_logging(log_path: str | Path = "logs/monitor.log") -> logging.Logger:
    logger = logging.getLogger("cloud_health_monitor")
    if logger.handlers:
        return logger
    path = Path(log_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    handler = RotatingFileHandler(path, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    return logger


def log_result(logger: logging.Logger, section: str, result: CheckResult) -> None:
    level = logging.INFO
    if result.status == HealthStatus.WARNING:
        level = logging.WARNING
    elif result.status in (HealthStatus.CRITICAL, HealthStatus.UNKNOWN):
        level = logging.ERROR
    logger.log(level, "section=%s check=%r status=%s summary=%r", section, result.name, result.status.name, result.summary)
